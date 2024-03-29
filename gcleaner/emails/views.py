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


class EmailStatsView(EmailMixin, APIView):
    """
    API view to get email stats for the user.
    """
    def get(self, request):
        service = self.get_service()

        nr_of_emails = service.retrieve_nr_of_unread_emails()

        data = {
            'unread': nr_of_emails['gmail']
        }

        return Response(data=data)


class EmailLockView(EmailMixin, APIView):
    """
    API view to lock emails in order to not do anything with them accidentally.
    """
    def post(self, request):
        service = self.get_service()

        service.lock_email(request.data)

        return Response()
