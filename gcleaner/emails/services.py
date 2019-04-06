from django.conf import settings

from googleapiclient import errors
from googleapiclient.discovery import build

from gcleaner.emails.models import LatestEmail, Email
from gcleaner.emails.parsers import GMailEmailParser


class GoogleAPIService(object):
    """
    Service class to handle data retrieval/modification using GMail API.

    It serves as a gateway to do all the necessary operations in order to
    reflect changes done by the user on GMail servers.
    """

    def __init__(self, credentials):
        self.credentials = credentials
        self.service = build('gmail', 'v1', credentials=credentials)

    def get_labeled_emails(self, labels, d):
        """
        Retrieve a list of emails from GMail API.

        The list is retrieved for a given user and has to contain emails
        that have all the specified labels in `labelIds` keyword argument.

        In order to reduce the load on the GMail API, a max of 1000 emails
        are going to be retrieved, starting from the date indicated in the
        query keyword argument `q`.

        :param {list} labels: A list of label ids that the emails have to have.
        :param {str} d: (Optional) The earliest date to retrieve emails from.

        :return: The list of emails from GMail API.
        """
        list_filters = {
            'userId': 'me',
            'labelIds': labels,
            'maxResults': 1000
        }

        if d:
            list_filters['q'] = 'after:{}'.format(d)

        try:
            response = self.service.users().messages().list(**list_filters).execute()

            messages = []
            if 'messages' in response:
                messages.extend(response['messages'])

            while 'nextPageToken' in response:
                page_token = response['nextPageToken']
                list_filters['pageToken'] = page_token
                response = self.service.users().messages().list(**list_filters).execute()
                messages.extend(response['messages'])

            return messages

        except errors.HttpError as error:
            # TODO properly handle API errors
            print('An error occurred: %s' % error)
            return []

    def get_unread_emails_ids(self, d=None):
        """
        Retrieve a list of Unread emails from GMail API.

        :param {str} d: (Optional) The earliest date to retrieve emails from.

        :return: The list of unread emails from GMail API.
        """
        return self.get_labeled_emails(['UNREAD'], d)

    def get_emails_details(self, emails, callback):
        """
        Create a batch job to retrieve emails details from GMail API.

        According to GMail API, it is impossible to simply retrieve email
        details in a list, but rather make individual calls for each email.

        In order to simplify things, a "batch" object can be created that
        will execute a provided callback function against the received data
        for each emails.

        :param {list} emails: List of objects with email IDs for which to retrieve details.
        :param {function} callback: The callback function to call upon receiving email details.
        """
        batch = self.service.new_batch_http_request(callback=callback)

        for email in emails:
            get_request = self.service.users().messages().get(userId='me',
                                                              id=email['id'],
                                                              fields=settings.GOOGLE_AUTH_SETTINGS['MESSAGE_FIELDS'],
                                                              format='metadata',
                                                              metadataHeaders=settings.GOOGLE_AUTH_SETTINGS['METADATA_HEADERS'])
            batch.add(get_request)

        batch.execute()


class EmailService(object):
    """
    Service class to handle Email retrieval for a user.

    Does API calls to the GMail API and stores the results in the database
    for faster retrieval.
    """
    def __init__(self, credentials, user):
        self.gmail_service = GoogleAPIService(credentials)
        self.user = user
        self.latest_email = None

    def get_date_to_retrieve_new_emails(self):
        """
        Compute the starting date since when GMail API should send unread emails
        :return: Date of the latest email in the database or None.
        """
        try:
            latest_email = LatestEmail.objects.get(user=self.user)
            date = latest_email.email.date.strftime('%Y-%m-%d')
        except LatestEmail.DoesNotExist:
            date = None

        return date

    def retrieve_nr_of_unread_emails(self):
        """
        Retrieve number of unread emails locally and that are new from GMail servers.

        Because GMail has a restriction in terms of the load on their servers,
        retrieving more than 50 emails requires throttling locally API calls.

        In order for a better UX, this method computes the amount of emails that
        are already retrieved from GMail API and stored in the DB *and* the new
        emails that are on GMail servers but not locally.
        :return:
        """
        response = {}

        date = self.get_date_to_retrieve_new_emails()

        nr_of_local_emails = self.user.emails.all().count()
        nr_of_gmail_emails = len(self.gmail_service.get_unread_emails_ids(date))

        response['gmail'] = nr_of_gmail_emails
        response['local'] = nr_of_local_emails

        return response

    def retrieve_unread_emails(self):
        """
        Retrieve a list of User's unread emails to be sent as a response.

        This method consists of several steps:
            1. Check for the latest email that exists in the DB for the given user.
            2. Make an API call to GMail to get any emails *after* the latest email.
            3. Save new emails in the DB.
            4. Retrieve and return all unread emails.
        :return: A list of `gcleaner.emails.models.Email` object instances.
        """
        date = self.get_date_to_retrieve_new_emails()

        new_emails = self.gmail_service.get_unread_emails_ids(date)

        self.gmail_service.get_emails_details(new_emails, self.gmail_service_batch_callback)

        if self.latest_email:
            if hasattr(self.user, 'latest_email'):
                self.user.latest_email.email = self.latest_email
                self.user.latest_email.save()
            else:
                LatestEmail.objects.create(user=self.user, email=self.latest_email)

        return self.user.emails.all()

    def gmail_service_batch_callback(self, request_id, response, exception):
        """
        The callback to be called for each batch request.

        In case no exception have occurred, save the email in the database,
        otherwise handle the exception.

        :param request_id: A unique identifier for the request in the batch,
                           generated automatically.
        :param {dict} response: A deserialized email object from the API response.
        :param exception: A `googleapiclient.errors.HttpError` instance or None
        """
        if exception:
            # TODO handle exception
            print(exception)
            pass

        # do not create email in case it already exists in the database
        elif not self.user.emails.filter(google_id=response['id']).exists():
            email_dict = GMailEmailParser.parse(response)
            email_dict['user'] = self.user.pk

            email = self.create_email_from_dict(email_dict)

            if not self.latest_email or self.latest_email.date < email.date:
                self.latest_email = email

    @staticmethod
    def create_email_from_dict(email_dict):
        """
        Create an Email instance from a dict with all necessary data.
        :param email_dict: A dictionary with email details.
        :return: Newly reated Email instance.
        """
        return Email.from_dict(email_dict)
