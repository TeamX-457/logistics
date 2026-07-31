from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Django's built-in admin site is moved off /admin/ so that path can
    # serve the test console's Admin Dashboard instead (far more relevant
    # here than Django's model-admin UI, which most people never touch).
    path("django-admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("deliveries.urls")),
    path("api/", include("tracking.urls")),
    path("api/admin/", include("admin_panel.urls")),
    path("api/trips/", include("trips.urls")),
    path("", include("frontend.urls")),
]
