from django.conf import settings


def google_client_id(request):
    """Exposes the Google OAuth client ID to templates for Sign in with Google.

    Client IDs are not secret (they're baked into every Google Sign-In web
    button), unlike GOOGLE_CLIENT_SECRET which must never reach the browser.
    """
    return {"GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID}
