from rest_framework.test import APIClient

from gcleaner.emails.constants import LABEL_INBOX, LABEL_TRASH
from gcleaner.emails.mixins import EmailMixin
from gcleaner.emails.parsers import GMailEmailParser
from gcleaner.emails.services import EmailService
from gcleaner.emails.views import EmailModifyView, EmailListView, EmailStatsView, EmailLockView


def test_email_list_view_get_queryset_uses_email_service_to_retrieve_unread_emails(mocker, email, google_credentials, user, gmail_api_get_1_response, gmail_api_get_2_response, gmail_api_get_3_response):
    # test setup and mocking
    mocker.patch.object(EmailListView, 'get_service')

    expected_emails = []
    for email in [gmail_api_get_1_response, gmail_api_get_2_response, gmail_api_get_3_response]:
        expected_emails.append(GMailEmailParser.parse(email, user))

    email_service = mocker.Mock()
    email_service.retrieve_unread_emails.return_value = expected_emails
    EmailListView.get_service.return_value = email_service

    client = APIClient()
    client.force_authenticate(user)

    # method call
    response = client.get('/api/v1/messages/')

    # assertions
    assert response.status_code == 200
    assert response.data == expected_emails
    email_service.retrieve_unread_emails.assert_called_once_with()


def test_email_mixin_get_service(mocker, email, google_credentials, user):
    # test setup and mocking
    mixin = EmailMixin()
    mixin.request = mocker.Mock()
    mixin.get_google_credentials = mocker.Mock()
    mixin.get_google_credentials.return_value = google_credentials
    mixin.request.user = user

    # method call
    service = mixin.get_service()

    # assertions
    assert isinstance(service, EmailService)


def test_email_modify_view_return_401_if_user_not_authenticated(db):
    # test setup and mocking
    client = APIClient()

    # method call
    response = client.put('/api/v1/messages/modify/', data={})

    # assertions
    assert response.status_code == 401


def test_email_modify_view(mocker, user, db):
    # test setup and mocking
    mocker.patch.object(EmailModifyView, 'get_service')
    email_service = mocker.Mock()
    EmailModifyView.get_service.return_value = email_service
    payload = {
        'ids': ['a', 'b', 'c'],
        'addLabelIds': [LABEL_TRASH],
        'removeLabelIds': [LABEL_INBOX]
    }
    email_service.modify_emails.return_value = None
    client = APIClient()
    client.force_authenticate(user)

    # method call
    response = client.put('/api/v1/messages/modify/', data=payload, format='json')

    # assertions
    assert response.status_code == 200
    assert response.data == ['a', 'b', 'c']
    email_service.modify_emails.assert_called_once_with(payload)


def test_email_stats_view(mocker, user, db):
    # test setup and mocking
    mocker.patch.object(EmailStatsView, 'get_service')
    email_service = mocker.Mock()
    email_service.retrieve_nr_of_unread_emails.return_value = {'gmail': 21}
    EmailStatsView.get_service.return_value = email_service
    client = APIClient()
    client.force_authenticate(user)

    # method call
    response = client.get('/api/v1/messages/stats/')

    # assertions
    assert response.status_code == 200
    assert response.data == {'unread': 21}


def test_email_lock_view(mocker, user, db):
    # test setup and mocking
    mocker.patch.object(EmailLockView, 'get_service')
    payload = {'google_id': 'g123', 'thread_id': 't123', 'locked': True}
    email_service = mocker.Mock()
    EmailLockView.get_service.return_value = email_service
    client = APIClient()
    client.force_authenticate(user)

    # method call
    response = client.post(f'/api/v1/messages/lock/', data=payload, format='json')

    # assertions
    assert response.status_code == 200
    email_service.lock_email.assert_called_once_with(payload)
