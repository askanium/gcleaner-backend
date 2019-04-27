import mock
from django.conf import settings
from rest_framework import status

from gcleaner.authentication.google import Flow, obtain_google_oauth_credentials
from gcleaner.authentication.jwt import JSONWebTokenAPIView

AUTHORIZATION_CODE = 'auth-code'
CREDENTIALS = {'foo': 'bar'}


def test_obtain_google_oauth_credentials(mocker):
    request = mocker.Mock()
    request.data = {
        'authorization_code': AUTHORIZATION_CODE,
        'redirect_uri': 'postmessage'
    }

    flow_mock = mocker.Mock()
    mocker.patch.object(Flow, 'from_client_secrets_file')
    Flow.from_client_secrets_file.return_value = flow_mock
    flow_mock.credentials = CREDENTIALS

    # function call
    credentials = obtain_google_oauth_credentials(request)

    # assertions
    Flow.from_client_secrets_file.assert_called_once_with(settings.GOOGLE_AUTH_SETTINGS['CREDENTIALS'],
                                                          scopes=settings.GOOGLE_AUTH_SETTINGS['SCOPES'],
                                                          redirect_uri='postmessage')
    flow_mock.fetch_token.assert_called_once_with(code=AUTHORIZATION_CODE)
    assert credentials == CREDENTIALS


@mock.patch('gcleaner.authentication.jwt.jwt_response_payload_handler')
@mock.patch('gcleaner.authentication.jwt.jwt_encode_handler')
@mock.patch('gcleaner.authentication.jwt.jwt_payload_handler')
@mock.patch('gcleaner.authentication.jwt.build')
@mock.patch('gcleaner.authentication.jwt.obtain_google_oauth_credentials')
def test_jwt_api_view_post(google_oauth_credentials_mock, build_mock, payload_mock, encode_mock, response_payload_mock, mocker, google_credentials, user):
    view = JSONWebTokenAPIView()
    jwt_token = 'jwt token'
    request = mocker.Mock()
    view.get_user = mocker.Mock()
    view.get_user.return_value = user
    google_oauth_credentials_mock.return_value = google_credentials
    service_mock = mocker.Mock()
    build_mock.return_value = service_mock
    service_mock.users.return_value.getProfile.return_value.execute.return_value = {'emailAddress': 'me@email.com'}
    payload_mock.return_value = {'user': 'me@email.com'}
    encode_mock.return_value = jwt_token
    response_payload_mock.return_value = {'token': jwt_token}

    # method call
    response = view.post(request)

    # assertions
    build_mock.assert_called_once_with('gmail', 'v1', credentials=google_credentials)
    service_mock.users.return_value.getProfile.assert_called_once_with(userId='me')
    payload_mock.assert_called_once_with(user)
    encode_mock.assert_called_once_with({'user': 'me@email.com', 'access_token': google_credentials.token, 'refresh_token': google_credentials.refresh_token})
    response_payload_mock.assert_called_once_with(jwt_token, user, request)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {'token': jwt_token, 'user': 'me@email.com'}
