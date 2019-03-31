from django.conf import settings

from google_auth_oauthlib.flow import Flow


def obtain_google_oauth_credentials(request):
    """
    Get Google credentials in exchange of authorization token.
    """
    authorization_code = request.data.get('authorization_code')
    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_AUTH_SETTINGS['CREDENTIALS'],
        scopes=settings.GOOGLE_AUTH_SETTINGS['SCOPES'],
        redirect_uri='postmessage')

    flow.fetch_token(code=authorization_code)

    return flow.credentials
