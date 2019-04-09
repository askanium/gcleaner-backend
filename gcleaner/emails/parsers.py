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

    _actor_props = {'sender'}

    @classmethod
    def parse(cls, email, user):
        """
        Parse the email into a dict that can easily be transformed
        into an Email instance.

        :param {dict} email: The email object returned from GMail API.
        :param {User} user: The owner of the email.

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

                        if local_header_name in cls._actor_props:
                            result[local_header_name] = cls.parse_actor(header['value'])
                        else:
                            result[local_header_name] = header['value']

        if 'receiver' not in result:
            result['receiver'] = user.email

        return result

    @classmethod
    def date_from_timestamp(cls, timestamp):
        """
        Convert a date timestamp into a `datetime.datetime` object instance.

        :param {int} timestamp: Date timestamp.

        :return: Datetime instance.
        """
        return datetime.datetime.fromtimestamp(int(timestamp) / 1000, tz=pytz.UTC)

    @classmethod
    def parse_actor(cls, actor_str: str):
        """
        Parse an actor string that represents an entity that can send/receive emails.

        GMail can send an actor string in 2 formats:
            - "Name Surname <name@email.com>"
            - "name@email.com"

        The returning dict contains 3 keys: name, email and domain of the actor email.
        In case there is no name, it will get substituted by the email.

        :param actor_str: The string to be parsed.

        :return: A dict "name", "email" and "domain" keys.
        """
        result = {}
        space = ' '

        if space in actor_str:
            result['name'] = actor_str.rsplit(' ', maxsplit=1)[0].replace("`", "'")
            result['email'] = actor_str.rsplit(' ', maxsplit=1)[1][1:-1]
        else:
            result['name'] = actor_str
            result['email'] = actor_str

        if result['name'][0] in ['"', "'"] and result['name'][-1] in ['"', "'"]:
            result['name'] = result['name'][1:-1]

        result['domain'] = result['email'].split('@')[1]

        return result
