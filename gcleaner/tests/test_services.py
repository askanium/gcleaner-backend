import datetime

from django.conf import settings

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource
from mock import call

from gcleaner.emails.services import GoogleAPIService


credentials = Credentials('')


def test_google_resource_service_initialization():
    google_api_service = GoogleAPIService(credentials)

    assert isinstance(google_api_service.credentials, Credentials)
    assert isinstance(google_api_service.service, Resource)


def test_google_resource_get_nr_of_unread_emails(mocker):
    label_ids = ['UNREAD']
    emails = [
        {'id': 'a1'},
        {'id': 'a2'}
    ]
    response = {
        'messages': emails
    }
    dt = datetime.date(2019, 1, 1)
    google_api_service = GoogleAPIService(credentials)
    google_api_service.service = mocker.Mock()
    google_api_service.service.users.return_value.messages.return_value.list.return_value.execute.return_value = response

    unread_emails = google_api_service.get_unread_emails_since_date(dt)

    google_api_service.service\
        .users.return_value\
        .messages.return_value\
        .list.assert_called_once_with(userId='me', labelIds=label_ids, maxResults=1000, q='after:{}'.format(dt))
    assert unread_emails == emails


def test_google_resource_create_and_run_a_batch_api_call(mocker):
    emails = [
        {'id': 'a1'},
        {'id': 'a2'}
    ]

    callback_stub = mocker.stub(name='batch_callback')
    batch = mocker.Mock()
    get_request_1 = mocker.Mock()
    get_request_2 = mocker.Mock()
    google_api_service = GoogleAPIService(credentials)
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
