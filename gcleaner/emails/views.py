from rest_framework.generics import ListAPIView

from gcleaner.emails.models import Email
from gcleaner.emails.serializers import EmailSerializer
from gcleaner.emails.services import EmailService
from gcleaner.utils.mixins import APIJWTDecoderMixin


class EmailListView(APIJWTDecoderMixin, ListAPIView):
    """
    API view to list user emails.
    """
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
    service_class = EmailService

    def get_service(self):
        """
        Return the service instance that should be used to retrieve user emails.
        """
        service = self.service_class(self.get_google_credentials(self.request), self.request.user)

        return service

    def get_queryset(self):
        """
        Filter queryset to operate only on emails of the User
        that has initiated the request.

        :return: The filtered queryset.
        """
        service = self.get_service()

        queryset = service.retrieve_unread_emails()

        return queryset
