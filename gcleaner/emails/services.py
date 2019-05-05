from time import sleep

from django.conf import settings

from googleapiclient import errors
from googleapiclient.discovery import build

from gcleaner.emails.constants import LABEL_UNREAD, LABEL_INBOX
from gcleaner.emails.models import LatestEmail, Email, Label
from gcleaner.emails.parsers import GMailEmailParser
from gcleaner.emails.serializers import LabelSerializer


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
                if len(messages) < 1000:
                    page_token = response['nextPageToken']
                    list_filters['pageToken'] = page_token
                    response = self.service.users().messages().list(**list_filters).execute()
                    messages.extend(response['messages'])
                else:
                    break

            # Return only 1000 messages as GMail does not allow
            # batches with more than 1000 requests in them.
            return messages[:1000]

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
        return self.get_labeled_emails([LABEL_UNREAD, LABEL_INBOX], d)

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

    def batch_modify_emails(self, payload):
        """
        Create and execute a batch request to modify labels on GMail servers.

        :param payload: A dict that has the "ids", "addLabelIds" and
                        "removeLabelIds" props, all lists with data to
                        be modified on GMail servers.
        :return: Errors if any or None
        """
        response = self.service.users().messages().batchModify(userId='me', body=payload).execute()

        # In case batchModify request was successful, it returns an empty string,
        # otherwise it returns a dict with an 'error' key with error details.
        if not response:
            return None
        else:
            return response['error']

    def list_user_labels(self):
        """
        Retrieve user labels from GMail API.

        :return: The list of labels.
        """
        response = self.service.users().labels().list(userId='me').execute()

        labels = response.get('labels', [])

        return labels


class EmailService(object):
    """
    Service class to handle Email retrieval for a user.

    Does API calls to the GMail API and stores the results in the database
    for faster retrieval.
    """
    def __init__(self, credentials, user):
        self.gmail_service = GoogleAPIService(credentials)
        self.email_label_serializer = LabelSerializer
        self.user = user
        self.last_saved_email = self.get_last_saved_email()
        self.emails = []
        self.email_ids = []
        self.failed_requests = {}

        self.exponential_backoff_delay = 1
        self.max_backoff_delay = 16

    def get_last_saved_email(self):
        """
        Retrieves the last Email instance of the user in case there is one.

        This method does not return a LatestEmail instance, as
        :return: Email instance or None
        """
        try:
            last_saved_email = LatestEmail.objects.get(user=self.user).email
        except LatestEmail.DoesNotExist:
            last_saved_email = None

        return last_saved_email

    def get_date_to_retrieve_new_emails(self):
        """
        Compute the starting date since when GMail API should send unread emails
        :return: Date of the latest email in the database or None.
        """
        if self.last_saved_email:
            return self.last_saved_email.date.strftime('%Y-%m-%d')

        return None

    def retrieve_nr_of_unread_emails(self):
        """
        Retrieve number of unread emails from GMail servers.

        Because GMail has a restriction in terms of the load on their servers,
        retrieving more than 50 emails requires throttling locally API calls.

        In order for a better UX, this method computes the amount of emails
        that are on GMail servers, so a loading animation with corresponding
        message can be shown to the user on the frontend.

        :return: A dict with number of emails on GMail.
        """
        response = {}

        nr_of_gmail_emails = len(self.gmail_service.get_unread_emails_ids())

        response['gmail'] = nr_of_gmail_emails

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
        if self.failed_requests:
            self.email_ids = list(self.failed_requests.values())
            self.failed_requests = {}
        else:
            self.email_ids = self.gmail_service.get_unread_emails_ids()

        self.gmail_service.get_emails_details(self.email_ids, self.gmail_service_batch_callback)

        self._handle_failed_requests()

        return self.emails

    def gmail_service_batch_callback(self, request_id, response, exception):
        """
        The callback to be called for each batch request.

        In case no exception have occurred, save the email in the database,
        otherwise handle the exception.

        :param request_id: A unique identifier for the request in the batch,
                           generated automatically.
        :param {dict} response: A deserialized email object from the API response.
        :param exception: A `googleapiclient.errors.HttpError` instance or None

        :return: The created email instance or None
        """
        if exception:
            if exception.resp.status in [403, 429]:
                self.failed_requests[request_id] = self.email_ids[int(request_id) - 1]

        else:
            email_dict = GMailEmailParser.parse(response, self.user)

            # Update labels in case there are new ones
            user_labels = Label.objects.filter(user=self.user).values_list('google_id', flat=True)
            if not set(email_dict['labels']).issubset(set(user_labels)):
                self.update_labels()

            self._populate_with_serialized_labels(email_dict)

            self.emails.append(email_dict)

    def _handle_failed_requests(self):
        """
        Check if there were failed requests in the batch and retry them with an
        exponential backoff.
        """
        if not self.failed_requests or self.exponential_backoff_delay > self.max_backoff_delay:
            return

        sleep(self.exponential_backoff_delay)
        self.exponential_backoff_delay *= 2

        self.retrieve_unread_emails()

    def _populate_with_serialized_labels(self, email_dict):
        """
        Swap label ids with serialized Label instances on the email dict.

        :param email_dict: The dict that contains all the info about the email.

        :return: The updated email instance.
        """
        serialized_labels = []
        for label_id in email_dict['labels']:
            label = Label.objects.get(user=self.user, google_id=label_id)
            serializer = self.email_label_serializer(label)
            serialized_labels.append(serializer.data)

        email_dict['labels'] = serialized_labels

    def assign_labels_to_email(self, email_dict):
        """
        Clear any labels for the email defined by the email dict and re-assign
        all labels.

        This method is called after calling `update_labels()` that populates the
        database with any new label from the GMail API.

        :param email_dict: The dict that contains all the info about the email.

        :return: The updated email instance.
        """
        email = Email.objects.get(user=self.user, google_id=email_dict['google_id'])
        email.labels.clear()

        for label_id in email_dict['labels']:
            label = Label.objects.get(user=self.user, google_id=label_id)
            email.labels.add(label)

        return email

    def update_labels(self):
        """
        Retrieve a list of User's labels.
        """
        labels = self.gmail_service.list_user_labels()

        for label in labels:
            Label.objects.get_or_create(user=self.user,
                                        google_id=label['id'],
                                        name=label['name'],
                                        type=label['type'],
                                        text_color=label.get('color', {}).get('textColor', ''),
                                        background_color=label.get('color', {}).get('backgroundColor', ''))

    @staticmethod
    def create_email_from_dict(email_dict):
        """
        Create an Email instance from a dict with all necessary data.
        :param email_dict: A dictionary with email details.
        :return: Newly reated Email instance.
        """
        return Email.from_dict(email_dict)

    def modify_emails(self, payload):
        """
        Initiate a call to GMail API to change labels for the given emails.

        :param payload: A dict that has the "ids", "addLabelIds" and
                        "removeLabelIds" props, all lists with data to
                        be modified on GMail servers.
        """
        errs = self.gmail_service.batch_modify_emails(payload)

        if not errs:
            emails = self.user.emails.filter(google_id__in=payload['ids'])
            add_labels = Label.objects.filter(user=self.user, google_id__in=payload['addLabelIds'])
            remove_labels = Label.objects.filter(user=self.user, google_id__in=payload['removeLabelIds'])
            for email in emails:
                email.labels.add(*add_labels)
                email.labels.remove(*remove_labels)
        else:
            return errs

