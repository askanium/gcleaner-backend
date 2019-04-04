import datetime

from django.conf import settings

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError
from mock import call

from gcleaner.emails.services import GoogleAPIService, EmailService


def test_google_resource_service_initialization(google_credentials):
    google_api_service = GoogleAPIService(google_credentials)

    assert isinstance(google_api_service.credentials, Credentials)
    assert isinstance(google_api_service.service, Resource)


def test_google_resource_service_get_labeled_emails_handles_exception(mocker, google_credentials):
    google_api_service = GoogleAPIService(google_credentials)
    google_api_service.service = mocker.Mock()
    google_api_service.service.users.return_value.messages.return_value.list.return_value.execute.side_effect = mocker.Mock(side_effect=HttpError(mocker.Mock(), b''))

    # method call
    messages = google_api_service.get_labeled_emails(['UNREAD'], None)

    # assertions
    assert messages == []


def test_google_resource_get_nr_of_unread_emails_since_a_specific_date(mocker, google_credentials):
    label_ids = ['UNREAD']
    emails = [
        {'id': 'a1'},
        {'id': 'a2'}
    ]
    response = {
        'messages': emails
    }
    dt = datetime.date(2019, 1, 1)
    google_api_service = GoogleAPIService(google_credentials)
    google_api_service.service = mocker.Mock()
    google_api_service.service.users.return_value.messages.return_value.list.return_value.execute.return_value = response

    # method call
    unread_emails = google_api_service.get_unread_emails(dt)

    # assertions
    google_api_service.service\
        .users.return_value\
        .messages.return_value\
        .list.assert_called_once_with(userId='me', labelIds=label_ids, maxResults=1000, q='after:{}'.format(dt))
    assert unread_emails == emails


def test_google_resource_get_nr_of_unread_emails_from_the_beginning_of_time(mocker, google_credentials):
    label_ids = ['UNREAD']
    emails = [
        {'id': 'a1'},
        {'id': 'a2'}
    ]
    response = {
        'messages': emails
    }
    google_api_service = GoogleAPIService(google_credentials)
    google_api_service.service = mocker.Mock()
    google_api_service.service.users.return_value.messages.return_value.list.return_value.execute.return_value = response

    # method call
    unread_emails = google_api_service.get_unread_emails()

    # assertions
    google_api_service.service\
        .users.return_value\
        .messages.return_value\
        .list.assert_called_once_with(userId='me', labelIds=label_ids, maxResults=1000)
    assert unread_emails == emails


def test_google_resource_create_and_run_a_batch_api_call(mocker, google_credentials):
    emails = [
        {'id': 'a1'},
        {'id': 'a2'}
    ]

    callback_stub = mocker.stub(name='batch_callback')
    batch = mocker.Mock()
    get_request_1 = mocker.Mock()
    get_request_2 = mocker.Mock()
    google_api_service = GoogleAPIService(google_credentials)
    google_api_service.service = mocker.Mock()
    google_api_service.service.new_batch_http_request.return_value = batch
    google_api_service.service.users.return_value.messages.return_value.get.side_effect = [get_request_1, get_request_2]

    # method call
    google_api_service.get_emails_details(emails, callback_stub)

    # assertions
    google_api_service.service.new_batch_http_request.assert_called_once_with(callback=callback_stub)
    calls = [
        call(userId='me',
             id='a1',
             fields=settings.GOOGLE_AUTH_SETTINGS['MESSAGE_FIELDS'],
             metadataHeaders=settings.GOOGLE_AUTH_SETTINGS['METADATA_HEADERS']),
        call(userId='me',
             id='a2',
             fields=settings.GOOGLE_AUTH_SETTINGS['MESSAGE_FIELDS'],
             metadataHeaders=settings.GOOGLE_AUTH_SETTINGS['METADATA_HEADERS'])
    ]
    google_api_service.service\
        .users.return_value\
        .messages.return_value\
        .get.assert_has_calls(calls)

    batch.add.assert_has_calls([
        call(get_request_1),
        call(get_request_2)
    ])
    batch.execute.assert_called_once()


def test_email_service_get_date_to_retrieve_emails_returns_none_if_no_latest_email(user, google_credentials):
    service = EmailService(credentials=google_credentials, user=user)

    date = service.get_date_to_retrieve_new_emails()

    assert date is None


def test_email_service_get_date_to_retrieve_emails_returns_date_of_latest_email(latest_email, user, google_credentials):
    service = EmailService(credentials=google_credentials, user=latest_email.user)

    date = service.get_date_to_retrieve_new_emails()

    assert date == '2019-03-19'


def test_email_service_retrieve_number_of_emails_a_user_has(mocker, google_credentials, gmail_api_list_response):
    user = mocker.Mock()
    user.emails.all.return_value.count.return_value = 0
    service = EmailService(credentials=google_credentials, user=user)
    service.gmail_service = mocker.Mock()
    service.gmail_service.get_unread_emails.return_value = gmail_api_list_response
    service.get_date_to_retrieve_new_emails = mocker.Mock()
    service.get_date_to_retrieve_new_emails.return_value = None

    # method call
    response = service.retrieve_nr_of_unread_emails()

    # assertions
    assert response['gmail'] == 3
    assert response['local'] == 0
    service.get_date_to_retrieve_new_emails.assert_called_once_with()
    service.gmail_service.get_unread_emails.assert_called_once_with(None)
    user.emails.all.return_value.count.assert_called_once_with()


def test_email_service_retrieve_number_of_emails_a_user_has_when_there_are_existing_db_emails(mocker, latest_email, google_credentials, gmail_api_list_response):
    service = EmailService(credentials=google_credentials, user=latest_email.user)
    service.gmail_service = mocker.Mock()
    service.gmail_service.get_unread_emails.return_value = gmail_api_list_response

    # method call
    response = service.retrieve_nr_of_unread_emails()

    # assertions
    assert response['gmail'] == 3
    assert response['local'] == 1
    service.gmail_service.get_unread_emails.assert_called_once_with('2019-03-19')
