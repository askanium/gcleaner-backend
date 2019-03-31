from rest_framework.generics import ListAPIView

from gcleaner.emails.models import Email
from gcleaner.emails.serializers import EmailSerializer


class EmailListView(ListAPIView):
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
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        return queryset
