import json

from django.conf import settings


def get_credentials_config_json():
    """
    Read the credentials.json file and return its contents as a dict.

    :TODO: adjust this method to account for encrypted credentials.json file.

    :return: The credentials.json content
    :rtype: dict
    """
    with open(settings.GOOGLE_AUTH_SETTINGS['CREDENTIALS'], 'r') as c:
        config = json.load(c)['web']

    return config
