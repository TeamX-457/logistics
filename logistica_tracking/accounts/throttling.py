from rest_framework.throttling import AnonRateThrottle


class RegisterThrottle(AnonRateThrottle):
    """Limits public registration endpoints to DEFAULT_THROTTLE_RATES['register'] per IP (5/hour)."""

    scope = "register"


class LoginThrottle(AnonRateThrottle):
    """Limits public login endpoints to DEFAULT_THROTTLE_RATES['login'] per IP (10/hour)."""

    scope = "login"
