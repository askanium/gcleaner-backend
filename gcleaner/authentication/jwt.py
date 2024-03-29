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

        :return: A tuple consisting of the User instance and whether
        it was created or retrieved.
        """
        user, created = User.objects.get_or_create(username=user_email, email=user_email)
        return user, created

    def get_jwt_token(self, user, credentials):
        """
        Compute the payload and encode it into a JWT.
        :param user: The User instance for which to encode the JWT token.
        :param credentials: User credentials ot use with GMail API.
        :return: The JWT token.
        """
        payload = jwt_payload_handler(user)
        payload['access_token'] = credentials.token
        payload['refresh_token'] = credentials.refresh_token

        return jwt_encode_handler(payload)

    def post(self, request, *args, **kwargs):
        try:
            credentials = obtain_google_oauth_credentials(request)
        except Warning as w:
            if hasattr(w, 'old_scope') and hasattr(w, 'new_scope') and set(w.old_scope).difference(set(w.new_scope)) != set():
                return Response(
                    {'message': 'It seems you did not give GCleaner permission to modify emails. Please try again.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                raise w

        if credentials.token:
            user, created = self.get_user(self.get_google_user_profile(credentials))

            jwt_token = self.get_jwt_token(user, credentials)

            response_data = jwt_response_payload_handler(jwt_token, user, request)
            response_data['user'] = user.email
            response_data['show_tour'] = created

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
