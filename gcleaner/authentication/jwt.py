from googleapiclient.discovery import build
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from datetime import datetime
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.utils import jwt_payload_handler, jwt_encode_handler, jwt_response_payload_handler

from gcleaner.authentication.google import obtain_google_oauth_credentials
from gcleaner.users.models import User


class JSONWebTokenAPIView(APIView):
    """
    Base API View that various JWT interactions inherit from.
    """
    permission_classes = ()
    authentication_classes = ()

    def get_google_user_profile(self, credentials):
        """
        Retrieves the user email from GMail API.

        :param credentials: User credentials to use with GMail API.

        :return: User email address.
        """
        service = build('gmail', 'v1', credentials=credentials)
        profile = service.users().getProfile(userId='me').execute()

        return profile.get('emailAddress', None)

    def get_user(self, user_email):
        """
        Retrieve the user based on the email address.

        :return: User instance.
        """
        user, created = User.objects.get_or_create(username=user_email, email=user_email)
        return user

    def post(self, request, *args, **kwargs):
        credentials = obtain_google_oauth_credentials(request)

        if credentials.token:
            user = self.get_user(self.get_google_user_profile(credentials))

            payload = jwt_payload_handler(user)
            payload['access_token'] = credentials.token
            payload['refresh_token'] = credentials.refresh_token

            jwt_token = jwt_encode_handler(payload)

            response_data = jwt_response_payload_handler(jwt_token, user, request)
            response = Response(response_data)
            if api_settings.JWT_AUTH_COOKIE:
                expiration = (datetime.utcnow() +
                              api_settings.JWT_EXPIRATION_DELTA)
                response.set_cookie(api_settings.JWT_AUTH_COOKIE,
                                    jwt_token,
                                    expires=expiration,
                                    httponly=True)
            return response

        return Response(
            {'message': 'Could not authenticate'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ObtainJSONWebToken(JSONWebTokenAPIView):
    """
    API View that receives a POST with a user's authorization code from Google.

    Returns a JSON Web Token that can be used for authenticated requests.
    """
    ...


obtain_jwt_token = ObtainJSONWebToken.as_view()
