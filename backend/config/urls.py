from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health", views.health, name="health"),
    path("api/health/", views.health),
    path("api/", include("accounts.urls")),
    path("api/", include("fleet.urls")),
    path("api/", include("deliveries.urls")),
    path("api/", include("disputes.urls")),
    path("api/", include("wallet.urls")),
    path("api/", include("dashboard.urls")),
    path("api/", include("adminpanel.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Frontend — served straight from templates/ so the whole app runs on one origin/port.
    path("", views.page, name="home"),
    path("<str:page>", views.page, name="page"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
