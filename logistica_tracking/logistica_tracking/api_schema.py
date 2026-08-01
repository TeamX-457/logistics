"""
Small helpers for the drf-spectacular annotations on the API views.

Most endpoints are plain APIViews that return ad-hoc dicts (`{"detail": ...}`,
or a serializer payload merged with a JWT pair) instead of a single serializer,
so drf-spectacular cannot infer their request/response bodies on its own. These
builders produce the throwaway inline serializers those annotations need, so the
@extend_schema decorators on the views stay readable.

Every `name` passed in has to be unique across the whole schema — spectacular
registers inline serializers as named components.
"""
from drf_spectacular.utils import inline_serializer
from rest_framework import serializers


def detail_response(name, **extra_fields):
    """`{"detail": "..."}`, plus any extra fields the view merges alongside it."""
    return inline_serializer(
        name=name,
        fields={"detail": serializers.CharField(), **extra_fields},
    )


def auth_response(name):
    """The login/register payload: the user object plus a JWT refresh/access pair."""
    from accounts.serializers import UserSerializer

    return inline_serializer(
        name=name,
        fields={
            "user": UserSerializer(),
            "refresh": serializers.CharField(),
            "access": serializers.CharField(),
        },
    )
