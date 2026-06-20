from rest_framework.routers import DefaultRouter

from .views import FleetVerificationViewSet

router = DefaultRouter()
router.register("verifications", FleetVerificationViewSet, basename="fleet-verification")

urlpatterns = router.urls
