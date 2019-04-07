from rest_framework.test import APIClient

from gcleaner.emails.mixins import EmailMixin
from gcleaner.emails.services import EmailService
from gcleaner.emails.views import EmailListView, EmailModifyView


def test_email_list_view_get_queryset_uses_email_service_to_retrieve_unread_emails(mocker, email, google_credentials, user):
    # test setup and mocking
    view = EmailListView()
    email_service = mocker.Mock()
    view.get_service = mocker.Mock()
    view.get_service.return_value = email_service
    email_service.retrieve_unread_emails.return_value = user.emails.all()

    # method call
    queryset = view.get_queryset()

    # assertions
    assert list(queryset) == list(user.emails.all())
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
        'addLabelIds': ['TRASH'],
        'removeLabelIds': ['INBOX']
    }
    email_service.modify_emails.return_value = None
    client = APIClient()
    client.force_authenticate(user)

    # method call
    response = client.put('/api/v1/messages/modify/', data=payload, format='json')

    # assertions
    assert response.status_code == 200
    assert response.data is None
    email_service.modify_emails.assert_called_once_with(payload)