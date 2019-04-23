from django.conf import settings
from google.auth.exceptions import RefreshError

from google.oauth2.credentials import Credentials
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework_jwt.utils import jwt_payload_handler, jwt_encode_handler

from gcleaner.emails.mixins import EmailMixin, emails_exception_handler
from gcleaner.emails.services import EmailService
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


def test_email_mixin_get_service_returns_email_service(mocker, google_credentials, user):
    # test setup and mocking
    request = mocker.Mock()
    request.user = user
    mixin = EmailMixin()
    mixin.get_google_credentials = mocker.Mock()
    mixin.request = request
    mixin.get_google_credentials.return_value = google_credentials

    # method call
    service = mixin.get_service()

    # assertions
    assert isinstance(service, EmailService)
    mixin.get_google_credentials.assert_called_once_with(request)


def test_email_mixin_get_exception_handler_returns_improved_handler():
    # test setup and mocking
    mixin = EmailMixin()

    # method call
    exc_handler = mixin.get_exception_handler()

    # assertions
    assert exc_handler == emails_exception_handler


def test_exception_handler_handles_google_token_expired_error():
    # test setup and mocking
    error_dict = {
        "error": "invalid_grant",
        "error_description": "Token has been expired or revoked."
    }
    exception = RefreshError('invalid_grant: Token has been expired or revoked.', error_dict)

    # function call
    response = emails_exception_handler(exception, {})

    # assertions
    assert isinstance(response, Response)
    assert response.data == {'detail': 'token_expired'}
    assert response.has_header('X-Reason')
    assert response.status_code == 407
