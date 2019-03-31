from django.conf import settings

from google.oauth2.credentials import Credentials
from rest_framework.test import APIRequestFactory
from rest_framework_jwt.utils import jwt_payload_handler, jwt_encode_handler

from gcleaner.users.models import User
from gcleaner.utils.mixins import APIJWTDecoderMixin


ACCESS_TOKEN = 'access_token'
REFRESH_TOKEN = 'refresh_token'
EXPIRES_AT = 'expires_at'
USER = User(pk=1, email='me@email.com', username='me@email.com')

PAYLOAD = jwt_payload_handler(USER)
PAYLOAD['access_token'] = ACCESS_TOKEN
PAYLOAD['refresh_token'] = REFRESH_TOKEN

JWT_TOKEN = jwt_encode_handler(PAYLOAD)


def test_api_jwt_decoder_mixin_yields_credentials_instance():
    rf = APIRequestFactory()
    request = rf.get('/', HTTP_AUTHORIZATION='JWT {}'.format(JWT_TOKEN))
    instance = APIJWTDecoderMixin()
    credentials = instance.get_google_credentials(request)

    assert isinstance(credentials, Credentials)
    assert credentials.token == ACCESS_TOKEN
    assert credentials.refresh_token == REFRESH_TOKEN
    assert credentials.token_uri == settings.GOOGLE_AUTH_SETTINGS['OAUTH2_TOKEN_ENDPOINT']
    assert credentials.scopes == settings.GOOGLE_AUTH_SETTINGS['SCOPES']


def test_api_jwt_decoder_mixin_returns_no_credentials_if_no_authorization_header():
    rf = APIRequestFactory()
    request = rf.get('/')
    instance = APIJWTDecoderMixin()
    credentials = instance.get_google_credentials(request)

    assert credentials is None
