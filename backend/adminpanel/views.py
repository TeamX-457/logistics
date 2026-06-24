from rest_framework import filters, generics
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminRole

from .registry import RESOURCES, get_resource
from .schema import build_field_schema
from .serializers import build_serializer


class AdminCatalogView(APIView):
    """Lists every resource the panel can manage, for the sidebar."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response([
            {"key": key, "label": config["label"], "creatable": config.get("creatable", True)}
            for key, config in RESOURCES.items()
        ])


class AdminResourceSchemaView(APIView):
    """Field metadata for one resource, used to render its list columns + edit form."""

    permission_classes = [IsAdminRole]

    def get(self, request, resource):
        config = get_resource(resource)
        return Response({
            "key": resource,
            "label": config["label"],
            "list_fields": config["list_fields"],
            "fields": build_field_schema(config),
            "creatable": config.get("creatable", True),
        })


class AdminResourceListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    filter_backends = [filters.SearchFilter]

    def get_config(self):
        return get_resource(self.kwargs["resource"])

    def get_queryset(self):
        config = self.get_config()
        queryset = config["model"].objects.all()
        ordering = config.get("ordering")
        return queryset.order_by(ordering) if ordering else queryset

    def get_serializer_class(self):
        return build_serializer(self.get_config())

    @property
    def search_fields(self):
        return self.get_config().get("search_fields", [])

    def create(self, request, *args, **kwargs):
        if not self.get_config().get("creatable", True):
            raise MethodNotAllowed("POST")
        return super().create(request, *args, **kwargs)


class AdminResourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminRole]

    def get_config(self):
        return get_resource(self.kwargs["resource"])

    def get_queryset(self):
        return self.get_config()["model"].objects.all()

    def get_serializer_class(self):
        return build_serializer(self.get_config())
