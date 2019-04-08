import datetime

import pytz
from django.conf import settings


class GMailEmailParser(object):
    """
    Parse an email object returned from the GMail API.

    As a result, the parser returns an object that can be passed
    to `gcleaner.emails.models.Email.from_dict` method to create
    an Email instance.
    """

    _google_to_local_props = {
        'id': 'google_id',
        'threadId': 'thread_id',
        'labelIds': 'labels',
        'snippet': 'snippet',
        'internalDate': 'date'
    }

    _google_to_local_metadata_props = {
        'Delivered-To': 'delivered_to',
        'Subject': 'subject',
        'From': 'sender',
        'To': 'receiver',
        'List-Unsubscribe': 'list_unsubscribe'
    }

    @classmethod
    def parse(cls, email):
        """
        Parse the email into a dict that can easily be transformed
        into an Email instance.

        :param {dict} email: The email object returned from GMail API.

        :return: The parsed dict with only the necessary fields.
        """
        result = {}

        for key, value in email.items():
            if key in cls._google_to_local_props:

                if key == 'internalDate':
                    value = cls.date_from_timestamp(value)

                result[cls._google_to_local_props[key]] = value
            elif key == 'payload':
                for header in value['headers']:
                    if header['name'] in settings.GOOGLE_AUTH_SETTINGS['METADATA_HEADERS']:
                        local_header_name = cls._google_to_local_metadata_props[header['name']]
                        result[local_header_name] = header['value']

        return result

    @classmethod
    def date_from_timestamp(cls, timestamp):
        """
        Convert a date timestamp into a `datetime.datetime` object instance.

        :param {int} timestamp: Date timestamp.

        :return: Datetime instance.
        """
        return datetime.datetime.fromtimestamp(int(timestamp) / 1000, tz=pytz.UTC)
