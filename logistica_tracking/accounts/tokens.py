from rest_framework_simplejwt.tokens import RefreshToken


def tokens_for_user(user):
    """Issue a refresh/access token pair with role embedded as a custom claim."""
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["username"] = user.username
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
