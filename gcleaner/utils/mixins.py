from django.conf import settings

from google.oauth2.credentials import Credentials
from rest_framework.authentication import get_authorization_header
from rest_framework_jwt.utils import jwt_decode_handler

from gcleaner.utils.readers import get_credentials_config_json


class APIJWTDecoderMixin(object):
    """
    Extracts and builds a `google.oauth2.credentials.Credentials`
    instance based on the Authorization request header.

    As this is a mixin for the protected endpoints, the assumption
    is that the JWT tokens are going to be valid as they will pass
    the validity checks within the REST framework, so no additional
    validation of JWT token is needed within this mixin.
    """

    def get_google_credentials(self, request):
        """
        Build a `google.oauth2.credentials.Credentials` instance from JWT token.

        JWT token along `GOOGLE_AUTH_SETTINGS` property within django settings
        contain all the necessary info necessary to build a credentials instance.

        :param {Request} request: The API request.

        :return: The Credentials instance.
        """
        auth = get_authorization_header(request).split()
        if not auth:
            return None

        payload = jwt_decode_handler(auth[1])

        config = get_credentials_config_json()

        credentials = Credentials(payload.get('access_token'),
                                  refresh_token=payload.get('refresh_token'),
                                  token_uri=settings.GOOGLE_AUTH_SETTINGS['OAUTH2_TOKEN_ENDPOINT'],
                                  client_id=config.get('client_id'),
                                  client_secret=config.get('client_secret'),
                                  scopes=settings.GOOGLE_AUTH_SETTINGS['SCOPES'])

        return credentials
