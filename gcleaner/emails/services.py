from django.conf import settings

from googleapiclient.discovery import build


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

        response = self.service.users().messages().list(**list_filters).execute()
        return response['messages']

    def get_unread_emails(self, d=None):
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
                                                              metadataHeaders=settings.GOOGLE_AUTH_SETTINGS['METADATA_HEADERS'])
            batch.add(get_request)

        batch.execute()


class EmailService(object):
    """

    """
    def __init__(self, credentials):
        self.gmail_service = GoogleAPIService(credentials)

