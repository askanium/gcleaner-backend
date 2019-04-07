from gcleaner.emails.services import EmailService
from gcleaner.utils.mixins import APIJWTDecoderMixin


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
