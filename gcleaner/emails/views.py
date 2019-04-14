from rest_framework.response import Response
from rest_framework.views import APIView

from gcleaner.emails.mixins import EmailMixin


class EmailListView(EmailMixin, APIView):
    """
    API view to list user emails.
    """

    def get(self, request):
        service = self.get_service()

        emails = service.retrieve_unread_emails()

        return Response(data=emails)


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

        return Response(data=batch_body['ids'])
