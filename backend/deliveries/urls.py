from rest_framework.routers import DefaultRouter

from .views import DeliveryRequestViewSet

router = DefaultRouter()
router.register("deliveries", DeliveryRequestViewSet, basename="delivery")

urlpatterns = router.urls
