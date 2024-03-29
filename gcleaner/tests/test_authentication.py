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


@mock.patch('gcleaner.authentication.jwt.jwt_payload_handler')
@mock.patch('gcleaner.authentication.jwt.jwt_encode_handler')
def test_get_jwt_token_method(encode_mock, payload_mock, user, google_credentials):
    # test setup and mocking
    view = JSONWebTokenAPIView()
    payload_mock.return_value = {'user': user.pk}
    encode_mock.return_value = 1

    # method call
    jwt_token = view.get_jwt_token(user, google_credentials)

    # assertions
    assert jwt_token == 1
    payload_mock.assert_called_once_with(user)
    encode_mock.assert_called_once_with({
        'user': user.pk,
        'access_token': google_credentials.token,
        'refresh_token': google_credentials.refresh_token
    })


@mock.patch('gcleaner.authentication.jwt.jwt_response_payload_handler')
@mock.patch('gcleaner.authentication.jwt.build')
@mock.patch('gcleaner.authentication.jwt.obtain_google_oauth_credentials')
def test_jwt_api_view_post(google_oauth_credentials_mock, build_mock, response_payload_mock, mocker, google_credentials, user):
    view = JSONWebTokenAPIView()
    jwt_token = 'jwt token'
    request = mocker.Mock()
    view.get_user = mocker.Mock()
    view.get_user.return_value = (user, False)
    view.get_jwt_token = mocker.Mock()
    view.get_jwt_token.return_value = jwt_token
    google_oauth_credentials_mock.return_value = google_credentials
    service_mock = mocker.Mock()
    build_mock.return_value = service_mock
    service_mock.users.return_value.getProfile.return_value.execute.return_value = {'emailAddress': 'me@email.com'}
    response_payload_mock.return_value = {'token': jwt_token}

    # method call
    response = view.post(request)

    # assertions
    build_mock.assert_called_once_with('gmail', 'v1', credentials=google_credentials)
    service_mock.users.return_value.getProfile.assert_called_once_with(userId='me')
    view.get_jwt_token.assert_called_once_with(user, google_credentials)
    response_payload_mock.assert_called_once_with(jwt_token, user, request)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {'token': jwt_token, 'user': 'me@email.com', 'show_tour': False}


@mock.patch('gcleaner.authentication.jwt.obtain_google_oauth_credentials')
def test_jwt_user_did_not_allow_proper_scopes_to_modify_emails_returns_message(google_oauth_credentials_mock, mocker):
    view = JSONWebTokenAPIView()
    request = mocker.Mock()
    warning = Warning('message')
    warning.old_scope = ['user', 'email', 'openid']
    warning.new_scope = ['user', 'openid']
    google_oauth_credentials_mock.side_effect = warning

    # method call
    response = view.post(request)

    # assertions
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {'message': 'It seems you did not give GCleaner permission to modify emails. Please try again.'}
