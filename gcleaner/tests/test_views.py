import mock

from gcleaner.emails.services import EmailService
from gcleaner.emails.views import EmailListView


@mock.patch('gcleaner.emails.views.APIJWTDecoderMixin.get_google_credentials')
def test_email_list_view_get_service(api_decoder_mixin_mock, mocker, user, google_credentials):
    view = EmailListView()
    email_service = EmailService(credentials=google_credentials, user=user)

    # test setup and mocking
    api_decoder_mixin_mock.return_value = google_credentials
    view.request = mocker.Mock()
    view.service_class = mocker.Mock()
    view.service_class.return_value = email_service

    # method call
    service = view.get_service()

    # assertions
    assert isinstance(service, EmailService)


def test_email_list_view_get_queryset_uses_email_service_to_retrieve_unread_emails(mocker, email, google_credentials, user):
    # test setup and mocking
    view = EmailListView()
    email_service = mocker.Mock()
    view.get_service = mocker.Mock()
    view.get_service.return_value = email_service
    view.request = mocker.Mock()
    email_service.retrieve_unread_emails.return_value = user.emails.all()

    # method call
    queryset = view.get_queryset()

    # assertions
    assert list(queryset) == list(user.emails.all())
    email_service.retrieve_unread_emails.assert_called_once_with()
