from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from gcleaner.emails.mixins import EmailMixin
from gcleaner.emails.models import Email
from gcleaner.emails.serializers import EmailSerializer


class EmailListView(EmailMixin, ListAPIView):
    """
    API view to list user emails.
    """
    queryset = Email.objects.all()
    serializer_class = EmailSerializer

    def get_queryset(self):
        """
        Filter queryset to operate only on emails of the User
        that has initiated the request.

        :return: The filtered queryset.
        """
        service = self.get_service()

        queryset = service.retrieve_unread_emails()

        return queryset


class EmailModifyView(EmailMixin, APIView):
    """
    API view to modify labels on user emails.
    """
    http_method_names = ['put', 'options']

    def put(self, request):
        service = self.get_service()

        batch_body = {
            'ids': request.data.get('ids', []),
            'addLabelIds': request.data.get('addLabelIds', []),
            'removeLabelIds': request.data.get('removeLabelIds', [])
        }

        errors = service.modify_emails(batch_body)

        if errors:
            pass
            # TODO handle errors

        return Response()
