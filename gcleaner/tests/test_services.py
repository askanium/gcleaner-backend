import datetime
import json
import os

import mock
from django.conf import settings

import pytest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpMockSequence, HttpMock, RequestMockBuilder
from mock import call

from gcleaner.emails.constants import LABEL_UNREAD, LABEL_INBOX, LABEL_TRASH, ACTION_TRASH
from gcleaner.emails.models import Label, LockedEmail, ModifiedEmailBatch
from gcleaner.emails.parsers import GMailEmailParser
from gcleaner.emails.serializers import LabelSerializer
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
    messages = google_api_service.get_labeled_emails([LABEL_UNREAD], None)

    # assertions
    assert messages == []


def test_google_resource_get_nr_of_unread_emails_since_a_specific_date(mocker, google_credentials):
    label_ids = [LABEL_UNREAD, LABEL_INBOX]
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
    label_ids = [LABEL_UNREAD, LABEL_INBOX]
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
    google_api_service = GoogleAPIService(credentials=google_credentials)
    google_api_service.service = mocker.Mock()
    google_api_service.service.users.return_value.messages.return_value.batchModify.return_value.execute.return_value = None
    payload = {
        'ids': ['1', '2', '3'],
        'addLabelIds': [LABEL_TRASH],
        'removeLabelIds': [LABEL_INBOX]
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
        {'id': LABEL_INBOX, 'name': 'INBOX', 'type': 'system'},
        {'id': LABEL_UNREAD, 'name': 'UNREAD', 'type': 'system'},
        {'id': LABEL_TRASH, 'name': 'TRASH', 'type': 'system'},
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


def test_email_service_initialization_when_no_latest_email_exists(user, google_credentials):
    service = EmailService(credentials=google_credentials, user=user)

    assert isinstance(service.gmail_service, GoogleAPIService)
    assert service.user == user
    assert service.email_label_serializer == LabelSerializer
    assert service.last_saved_email is None
    assert service.emails == []
    assert service.email_ids == []
    assert service.failed_requests == {}
    assert service.exponential_backoff_delay == 1
    assert service.max_backoff_delay == 16


def test_email_service_initialization_when_latest_email_exists(user, google_credentials, latest_email):
    service = EmailService(credentials=google_credentials, user=user)

    assert isinstance(service.gmail_service, GoogleAPIService)
    assert service.user == user
    assert service.email_label_serializer == LabelSerializer
    assert service.last_saved_email == latest_email.email
    assert service.emails == []
    assert service.email_ids == []
    assert service.failed_requests == {}
    assert service.exponential_backoff_delay == 1
    assert service.max_backoff_delay == 16


def test_email_service_get_date_to_retrieve_emails_returns_none_if_no_latest_email(user, google_credentials):
    service = EmailService(credentials=google_credentials, user=user)

    date = service.get_date_to_retrieve_new_emails()

    assert date is None


def test_email_service_get_date_to_retrieve_emails_returns_date_of_latest_email(latest_email, user, google_credentials):
    service = EmailService(credentials=google_credentials, user=latest_email.user)

    date = service.get_date_to_retrieve_new_emails()

    assert date == '2019-03-19'


def test_email_service_retrieve_number_of_emails_a_user_has(mocker, user, google_credentials, gmail_api_list_response):
    service = EmailService(credentials=google_credentials, user=user)
    service.gmail_service = mocker.Mock()
    service.gmail_service.get_unread_emails_ids.return_value = gmail_api_list_response

    # method call
    response = service.retrieve_nr_of_unread_emails()

    # assertions
    assert response['gmail'] == 3
    assert len(response.keys()) == 1
    service.gmail_service.get_unread_emails_ids.assert_called_once_with()


@pytest.mark.skip(reason='Currently saving emails from GMail API is disabled on the backend')
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


def test_email_service_retrieve_user_emails_for_the_first_time(mocker, user, all_labels, google_credentials, gmail_api_list_response, gmail_batch_response, gmail_api_get_1_response, gmail_api_get_2_response, gmail_api_get_3_response):
    # test setup and mocking
    service = EmailService(credentials=google_credentials, user=user)
    service._handle_failed_requests = mocker.Mock()
    http = HttpMockSequence([
        ({'status': 200}, open(os.path.join(DATA_DIR, 'gmail.json'), 'rb').read()),
        ({'status': 200}, json.dumps({'messages': gmail_api_list_response})),
        ({'status': 200, 'content-type': 'multipart/mixed; boundary=batch_ygSpAcfQXdA_AAfKEo9rkX4'}, gmail_batch_response),
    ])
    service.gmail_service.service = build('gmail', 'v1', http=http)
    expected_emails = []
    for email in [gmail_api_get_1_response, gmail_api_get_2_response, gmail_api_get_3_response]:
        email_dict = GMailEmailParser.parse(email, user)
        service._populate_with_serialized_labels(email_dict)
        expected_emails.append(email_dict)

    # method call
    emails = service.retrieve_unread_emails()

    # post call assertions
    assert user.emails.all().count() == 0
    assert hasattr(user, 'latest_email') is False
    assert emails == expected_emails
    service._handle_failed_requests.assert_called_once_with()


def test_email_service_retrieve_user_emails_with_existing_locked_emails(mocker, user, all_labels, google_credentials, gmail_api_list_response, gmail_batch_response, gmail_api_get_1_response, gmail_api_get_2_response, gmail_api_get_3_response, locked_email):
    # test setup and mocking
    service = EmailService(credentials=google_credentials, user=user)
    service._handle_failed_requests = mocker.Mock()
    http = HttpMockSequence([
        ({'status': 200}, open(os.path.join(DATA_DIR, 'gmail.json'), 'rb').read()),
        ({'status': 200}, json.dumps({'messages': gmail_api_list_response})),
        ({'status': 200, 'content-type': 'multipart/mixed; boundary=batch_ygSpAcfQXdA_AAfKEo9rkX4'}, gmail_batch_response),
    ])
    service.gmail_service.service = build('gmail', 'v1', http=http)
    expected_emails = []
    for email in [gmail_api_get_1_response, gmail_api_get_2_response, gmail_api_get_3_response]:
        email_dict = GMailEmailParser.parse(email, user)
        service._populate_with_serialized_labels(email_dict)
        expected_emails.append(email_dict)
        if email_dict['google_id'] == locked_email.google_id:
            email_dict['locked'] = True

    # method call
    emails = service.retrieve_unread_emails()

    # post call assertions
    assert user.emails.all().count() == 0
    assert hasattr(user, 'latest_email') is False
    assert emails == expected_emails
    service._handle_failed_requests.assert_called_once_with()


def test_email_service_retrieves_email_details_for_previously_failed_batch_requests(mocker, google_credentials, user):
    # test setup and mocking
    service = EmailService(credentials=google_credentials, user=user)
    service.failed_requests = {'1': {'id': 'a'}}
    service.gmail_service = mocker.Mock()

    # method call
    service.retrieve_unread_emails()

    # assertions
    assert service.failed_requests == {}
    service.gmail_service.get_emails_details.assert_called_once_with([{'id': 'a'}], service.gmail_service_batch_callback)


@mock.patch('gcleaner.emails.services.sleep')
def test_email_service_handle_failed_requests_returns_if_no_failed_requests(sleep_mock, mocker, google_credentials, user):
    # test setup and mocking
    service = EmailService(credentials=google_credentials, user=user)
    service.retrieve_unread_emails = mocker.Mock()

    # method call
    service._handle_failed_requests()

    # assertions
    sleep_mock.assert_not_called()
    service.retrieve_unread_emails.assert_not_called()


@mock.patch('gcleaner.emails.services.sleep')
def test_email_service_handle_failed_requests_returns_if_backoff_delay_exceeded_max_value(sleep_mock, mocker, google_credentials, user):
    # test setup and mocking
    service = EmailService(credentials=google_credentials, user=user)
    service.retrieve_unread_emails = mocker.Mock()
    service.max_backoff_delay = 32

    # method call
    service._handle_failed_requests()

    # assertions
    sleep_mock.assert_not_called()
    service.retrieve_unread_emails.assert_not_called()


@mock.patch('gcleaner.emails.services.sleep')
def test_email_service_handle_failed_requests_retrieve_email_details(sleep_mock, mocker, google_credentials, user):
    # test setup and mocking
    service = EmailService(credentials=google_credentials, user=user)
    service.retrieve_unread_emails = mocker.Mock()
    service.failed_requests = {
        '1': {'id': 'a'}
    }

    # method call
    service._handle_failed_requests()

    # assertions
    assert service.exponential_backoff_delay == 2
    sleep_mock.asser_called_once_with(1)
    service.retrieve_unread_emails.assert_called_once_with()


@pytest.mark.skip(reason='Currently saving emails from GMail API is disabled on the backend')
def test_email_service_retrieve_subsequent_user_emails(user, all_labels, latest_email, google_credentials, gmail_api_list_response, gmail_batch_small_response):
    # pre call assertions
    assert user.emails.exclude(labels__google_id=LABEL_TRASH).count() == 1
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
    assert user.emails.exclude(labels__google_id=LABEL_TRASH).count() == 3
    assert user.latest_email.email == user.emails.order_by('-date').first()
    assert user.latest_email.email_id != latest_email_email_pk
    assert list(emails) == list(user.emails.exclude(labels__google_id=LABEL_TRASH))


def test_email_service_batch_callback_populate_failed_requests_on_429_error(mocker, google_credentials, user):
    # test setup and mocking
    service = EmailService(credentials=google_credentials, user=user)
    service.email_ids = [{'id': 'a'}]
    service._populate_with_serialized_labels = mocker.Mock()
    exception = mocker.Mock()
    exception.resp.status = 429

    # method call
    service.gmail_service_batch_callback('1', None, exception)

    # assertions
    assert len(service.emails) == 0
    assert service.failed_requests == {'1': {'id': 'a'}}
    assert not service._populate_with_serialized_labels.called


def test_email_service_batch_callback_populate_failed_requests_on_403_error(mocker, google_credentials, user):
    # test setup and mocking
    service = EmailService(credentials=google_credentials, user=user)
    service.email_ids = [{'id': 'a'}]
    service._populate_with_serialized_labels = mocker.Mock()
    exception = mocker.Mock()
    exception.resp.status = 403

    # method call
    service.gmail_service_batch_callback('1', None, exception)

    # assertions
    assert len(service.emails) == 0
    assert service.failed_requests == {'1': {'id': 'a'}}
    assert not service._populate_with_serialized_labels.called


def test_email_service_batch_callback_marks_email_as_locked_if_locked_email_in_database(mocker, google_credentials, locked_email, gmail_api_get_1_response, all_labels, user):
    # test setup and mocking
    service = EmailService(credentials=google_credentials, user=user)
    service.email_ids = [{'id': locked_email.google_id}]
    service._populate_with_serialized_labels = mocker.Mock()

    # method call
    service.gmail_service_batch_callback('1', gmail_api_get_1_response, None)

    # assertions
    assert len(service.emails) == 1
    assert service.emails[0]['locked'] is True


@pytest.mark.skip(reason='Currently saving emails from GMail API is disabled on the backend')
def test_email_service_does_not_duplicate_emails(mocker, user, all_labels, google_credentials, gmail_api_get_3_response, gmail_api_list_response, gmail_batch_response):
    service = EmailService(credentials=google_credentials, user=user)
    service._populate_with_serialized_labels = mocker.Mock()
    service.gmail_service_batch_callback(1, gmail_api_get_3_response, None)

    # pre call assertions
    assert user.emails.exclude(labels__google_id=LABEL_TRASH).count() == 1

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
    assert user.emails.exclude(labels__google_id=LABEL_TRASH).count() == 3
    assert list(emails) == list(user.emails.exclude(labels__google_id=LABEL_TRASH))
    service._populate_with_serialized_labels.assert_called_once()


def test_email_service_automatically_updates_labels_from_api(user, all_labels, google_credentials, gmail_api_get_3_response, gmail_api_list_response, gmail_batch_response):
    Label.objects.get(google_id='Label_35').delete()

    service = EmailService(credentials=google_credentials, user=user)

    # pre call assertions
    assert user.labels.filter(google_id='Label_35').count() == 0

    # test setup and mocking
    labels = [
        {'id': LABEL_INBOX, 'name': 'INBOX', 'type': 'system'},
        {'id': LABEL_UNREAD, 'name': 'UNREAD', 'type': 'system'},
        {'id': LABEL_TRASH, 'name': 'TRASH', 'type': 'system'},
        {'id': 'Label_35', 'name': 'Custom Label', 'type': 'user', 'color': {'textColor': '#cccccc', 'backgroundColor': '#ffffff'}}
    ]
    http = HttpMockSequence([
        ({'status': 200}, open(os.path.join(DATA_DIR, 'gmail.json'), 'rb').read()),
        ({'status': 200}, json.dumps({'messages': gmail_api_list_response})),
        ({'status': 200, 'content-type': 'multipart/mixed; boundary=batch_ygSpAcfQXdA_AAfKEo9rkX4'}, gmail_batch_response),
        ({'status': 200}, json.dumps({'labels': labels}))
    ])
    service.gmail_service.service = build('gmail', 'v1', http=http)

    # method call
    service.retrieve_unread_emails()

    # post call assertions
    assert user.labels.filter(google_id='Label_35').count() == 1
    assert user.labels.filter(google_id=LABEL_INBOX).count() == 1


def test_email_service_update_labels_from_api_response(mocker, user, google_credentials, label_inbox):
    service = EmailService(credentials=google_credentials, user=user)

    # pre call assertions
    assert user.labels.all().count() == 1

    # test setup and mocking
    labels = [
        {'id': LABEL_INBOX, 'name': 'INBOX', 'type': 'system'},
        {'id': LABEL_UNREAD, 'name': 'UNREAD', 'type': 'system'},
        {'id': LABEL_TRASH, 'name': 'TRASH', 'type': 'system'},
        {'id': 'Label_35', 'name': 'Custom Label', 'type': 'user', 'color': {'textColor': '#cccccc', 'backgroundColor': '#ffffff'}}
    ]
    service.gmail_service = mocker.Mock()
    service.gmail_service.list_user_labels.return_value = labels

    # method call
    service.update_labels()

    # post call assertions
    assert user.labels.all().count() == 4


@pytest.mark.skip(reason='Currently saving emails from GMail API is disabled on the backend')
def test_email_service_assign_labels_to_email(email, user, all_labels, google_credentials):
    service = EmailService(credentials=google_credentials, user=user)

    # test setup and mocking
    labels = [all_labels[-2].google_id, all_labels[-1].google_id]
    email_dict = {
        'google_id': email.google_id,
        'labels': labels
    }
    assert list(email.labels.all().values_list('google_id', flat=True)) == [LABEL_UNREAD, LABEL_INBOX]

    # method call
    service.assign_labels_to_email(email_dict)

    # assertions
    assert list(email.labels.all().values_list('google_id', flat=True)) == labels


def test_email_service_modify_emails(mocker, user, all_labels, google_credentials):
    # test setup and mocking
    service = EmailService(credentials=google_credentials, user=user)
    service.gmail_service = mocker.Mock()
    service.gmail_service.batch_modify_emails.return_value = None
    payload = {
        'ids': ['a', 'b', 'c'],
        'addLabelIds': [LABEL_TRASH],
        'removeLabelIds': [LABEL_INBOX]
    }

    # method call
    service.modify_emails(payload)

    # assertions
    modified_batch = ModifiedEmailBatch.objects.last()
    assert user.emails.all().count() == 0
    assert modified_batch.nr_of_emails == 3
    assert modified_batch.action == ACTION_TRASH
    service.gmail_service.batch_modify_emails.assert_called_once_with(payload)


def test_email_service_populate_email_dict_with_serialized_labels(user, google_credentials, gmail_api_get_2_response, all_labels):
    # test setup and mocking
    service = EmailService(credentials=google_credentials, user=user)
    email_dict = GMailEmailParser.parse(gmail_api_get_2_response, user)

    # method call
    service._populate_with_serialized_labels(email_dict)

    # assertions
    assert email_dict['labels'] == [
        {
            'google_id': 'CATEGORY_PERSONAL',
            'name': 'CATEGORY_PERSONAL',
            'type': 'system',
            'text_color': '',
            'background_color': ''
        },
        {
            'google_id': LABEL_UNREAD,
            'name': 'UNREAD',
            'type': 'system',
            'text_color': '',
            'background_color': ''
        },
        {
            'google_id': LABEL_INBOX,
            'name': 'INBOX',
            'type': 'system',
            'text_color': '',
            'background_color': ''
        },
        {
            'google_id': 'Label_35',
            'name': 'Custom Label',
            'type': 'user',
            'text_color': '#222',
            'background_color': '#ddd'
        }
    ]


def test_email_service_lock_email_create_locked_email(user, google_credentials):
    # test setup
    service = EmailService(credentials=google_credentials, user=user)
    payload = {
        'google_id': 'g123',
        'thread_id': 't123',
        'locked': True
    }

    # method call
    service.lock_email(payload)
    locked_email = LockedEmail.objects.last()

    # assertions
    assert LockedEmail.objects.count() == 1
    assert locked_email.google_id == 'g123'
    assert locked_email.thread_id == 't123'
    assert locked_email.locked is True
    assert locked_email.user == user


def test_email_service_lock_email_update_existing_locked_email(user, google_credentials):
    # test setup
    service = EmailService(credentials=google_credentials, user=user)
    payload = {
        'google_id': 'g123',
        'thread_id': 't123',
        'locked': True,
    }
    LockedEmail.objects.create(user=user, **payload)
    payload['locked'] = False

    # method call
    service.lock_email(payload)
    locked_email = LockedEmail.objects.last()

    # assertions
    assert LockedEmail.objects.count() == 1
    assert locked_email.locked is False
