import datetime
import json
import os

from django.conf import settings

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpMockSequence, HttpMock, RequestMockBuilder
from mock import call

from gcleaner.emails.services import GoogleAPIService, EmailService


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


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
    unread_emails = google_api_service.get_unread_emails_ids(dt)

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
    unread_emails = google_api_service.get_unread_emails_ids()

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
             format='metadata',
             metadataHeaders=settings.GOOGLE_AUTH_SETTINGS['METADATA_HEADERS']),
        call(userId='me',
             id='a2',
             fields=settings.GOOGLE_AUTH_SETTINGS['MESSAGE_FIELDS'],
             format='metadata',
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


def test_google_api_service_batch_modify_request(mocker, google_credentials, user):
    response = mocker.Mock()
    response.status = 204
    google_api_service = GoogleAPIService(credentials=google_credentials)
    google_api_service.service = mocker.Mock()
    google_api_service.service.users.return_value.messages.return_value.batchModify.return_value.execute.return_value = response
    payload = {
        'ids': ['1', '2', '3'],
        'addLabelIds': ['TRASH'],
        'removeLabelIds': ['INBOX']
    }

    # method call
    google_api_service.batch_modify_emails(payload)

    # assertions
    google_api_service.service.users.return_value.messages.return_value.batchModify.assert_called_once_with(userId='me', body=payload)


def test_google_api_service_retrieve_user_labels(mocker, google_credentials):
    google_api_service = GoogleAPIService(credentials=google_credentials)
    google_api_service.service = mocker.Mock()

    http = HttpMock(os.path.join(DATA_DIR, 'gmail.json'), {'status': 200})
    labels = [
        {'id': 'INBOX', 'name': 'INBOX', 'type': 'system'},
        {'id': 'UNREAD', 'name': 'UNREAD', 'type': 'system'},
        {'id': 'TRASH', 'name': 'TRASH', 'type': 'system'},
        {'id': 'Label_10', 'name': 'Custom Label', 'type': 'user', 'text_color': '#cccccc', 'background_color': '#ffffff'}
    ]

    request_builder = RequestMockBuilder({
        'gmail.users.labels.list': (None, json.dumps({'labels': labels}))
    })

    google_api_service.service = build('gmail', 'v1', http=http, requestBuilder=request_builder)

    # method call
    response = google_api_service.list_user_labels()

    # assertions
    assert response == labels


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
    user.emails.exclude.return_value.count.return_value = 0
    service = EmailService(credentials=google_credentials, user=user)
    service.gmail_service = mocker.Mock()
    service.gmail_service.get_unread_emails_ids.return_value = gmail_api_list_response
    service.get_date_to_retrieve_new_emails = mocker.Mock()
    service.get_date_to_retrieve_new_emails.return_value = None

    # method call
    response = service.retrieve_nr_of_unread_emails()

    # assertions
    assert response['gmail'] == 3
    assert response['local'] == 0
    service.get_date_to_retrieve_new_emails.assert_called_once_with()
    service.gmail_service.get_unread_emails_ids.assert_called_once_with(None)
    user.emails.exclude.assert_called_once_with(labels__google_id='TRASH')
    user.emails.exclude.return_value.count.assert_called_once_with()


def test_email_service_retrieve_number_of_emails_a_user_has_when_there_are_existing_db_emails(mocker, latest_email, google_credentials, gmail_api_list_response):
    service = EmailService(credentials=google_credentials, user=latest_email.user)
    service.gmail_service = mocker.Mock()
    service.gmail_service.get_unread_emails_ids.return_value = gmail_api_list_response

    # method call
    response = service.retrieve_nr_of_unread_emails()

    # assertions
    assert response['gmail'] == 3
    assert response['local'] == 1
    service.gmail_service.get_unread_emails_ids.assert_called_once_with('2019-03-19')


def test_email_service_retrieve_user_emails_for_the_first_time(user, all_labels, google_credentials, gmail_api_list_response, gmail_batch_response):
    # pre call assertions
    assert user.emails.exclude(labels__google_id='TRASH').count() == 0
    assert hasattr(user, 'latest_email') is False

    # test setup and mocking
    service = EmailService(credentials=google_credentials, user=user)
    http = HttpMockSequence([
        ({'status': 200}, open(os.path.join(DATA_DIR, 'gmail.json'), 'rb').read()),
        ({'status': 200}, json.dumps({'messages': gmail_api_list_response})),
        ({'status': 200, 'content-type': 'multipart/mixed; boundary=batch_ygSpAcfQXdA_AAfKEo9rkX4'}, gmail_batch_response),
    ])
    service.gmail_service.service = build('gmail', 'v1', http=http)

    # method call
    emails = service.retrieve_unread_emails()

    # post call assertions
    assert user.emails.exclude(labels__google_id='TRASH').count() == 3
    assert user.latest_email.email == user.emails.order_by('-date').first()
    assert list(emails) == list(user.emails.exclude(labels__google_id='TRASH'))


def test_email_service_retrieve_subsequent_user_emails(user, all_labels, latest_email, google_credentials, gmail_api_list_response, gmail_batch_small_response):
    # pre call assertions
    assert user.emails.exclude(labels__google_id='TRASH').count() == 1
    assert user.latest_email == latest_email

    # test setup and mocking
    latest_email_email_pk = latest_email.email_id
    service = EmailService(credentials=google_credentials, user=user)
    http = HttpMockSequence([
        ({'status': 200}, open(os.path.join(DATA_DIR, 'gmail.json'), 'rb').read()),
        ({'status': 200}, json.dumps({'messages': gmail_api_list_response[:2]})),
        ({'status': 200, 'content-type': 'multipart/mixed; boundary=batch_ygSpAcfQXdA_AAfKEo9rkX4'}, gmail_batch_small_response),
    ])
    service.gmail_service.service = build('gmail', 'v1', http=http)

    # method call
    emails = service.retrieve_unread_emails()

    # post call assertions
    assert user.emails.exclude(labels__google_id='TRASH').count() == 3
    assert user.latest_email.email == user.emails.order_by('-date').first()
    assert user.latest_email.email_id != latest_email_email_pk
    assert list(emails) == list(user.emails.exclude(labels__google_id='TRASH'))


def test_email_service_does_not_duplicate_emails(user, all_labels, google_credentials, gmail_api_get_3_response, gmail_api_list_response, gmail_batch_response):
    service = EmailService(credentials=google_credentials, user=user)
    service.gmail_service_batch_callback(1, gmail_api_get_3_response, None)

    # pre call assertions
    assert user.emails.exclude(labels__google_id='TRASH').count() == 1

    # test setup and mocking
    http = HttpMockSequence([
        ({'status': 200}, open(os.path.join(DATA_DIR, 'gmail.json'), 'rb').read()),
        ({'status': 200}, json.dumps({'messages': gmail_api_list_response})),
        ({'status': 200, 'content-type': 'multipart/mixed; boundary=batch_ygSpAcfQXdA_AAfKEo9rkX4'}, gmail_batch_response),
    ])
    service.gmail_service.service = build('gmail', 'v1', http=http)

    # method call
    emails = service.retrieve_unread_emails()

    # post call assertions
    assert user.emails.exclude(labels__google_id='TRASH').count() == 3
    assert list(emails) == list(user.emails.exclude(labels__google_id='TRASH'))


def test_email_service_modify_emails(mocker, user, all_labels, google_credentials, gmail_api_email_1, gmail_api_email_2, gmail_api_email_3):
    # pre call assertions
    assert user.emails.filter(labels__google_id='TRASH').count() == 0

    # test setup and mocking
    service = EmailService(credentials=google_credentials, user=user)
    service.gmail_service = mocker.Mock()
    service.gmail_service.batch_modify_emails.return_value = None
    payload = {
        'ids': [gmail_api_email_1.google_id, gmail_api_email_2.google_id],
        'addLabelIds': ['TRASH'],
        'removeLabelIds': ['INBOX']
    }

    # method call
    service.modify_emails(payload)

    # assertions
    assert user.emails.all().count() == 3
    service.gmail_service.batch_modify_emails.assert_called_once_with(payload)
    assert user.emails.exclude(labels__google_id='TRASH').count() == 1
    assert user.emails.filter(labels__google_id='TRASH').count() == 2
