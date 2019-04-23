from django.db import connection, transaction

from google.auth.exceptions import RefreshError
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response

from gcleaner.emails.services import EmailService
from gcleaner.utils.mixins import APIJWTDecoderMixin


def set_rollback():
    atomic_requests = connection.settings_dict.get('ATOMIC_REQUESTS', False)
    if atomic_requests and connection.in_atomic_block:
        transaction.set_rollback(True)


def emails_exception_handler(exc, context):
    """
    Returns the response that should be used for any given exception.

    Additionally to standard rest framework exception handling, it handles
    RefreshError from GMail API that indicates the access token needs to
    be refreshed.

    Any unhandled exceptions may return `None`, which will cause a 500 error
    to be raised.
    """
    if isinstance(exc, RefreshError):
        headers = {'X-Reason': 'Token Expired'}
        data = {'detail': 'token_expired'}

        set_rollback()

        return Response(data, status=status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED, headers=headers)
    else:
        return exception_handler(exc, context)


class EmailMixin(APIJWTDecoderMixin):
    """
    Allows for creation of an EmailService instance based on the request.
    """
    service_class = EmailService

    def get_service(self):
        """
        Return the service instance that should be used to retrieve user emails.
        """
        service = self.service_class(self.get_google_credentials(self.request), self.request.user)

        return service

    def get_exception_handler(self):
        """
        Return the augmented standard exception handler with GMail API related
        error handling.
        :return: The exception handler function.
        """
        return emails_exception_handler
