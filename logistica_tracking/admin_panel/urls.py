from django.urls import path

from .views import (
    ActivateUserView,
    AdminDeliveryListView,
    AdminTripSummaryView,
    AdminUserListView,
    CancelDeliveryView,
    DeactivateUserView,
    NotifyAllPriorityDriversView,
    NotifyEveryoneDriversView,
    NotifySpecificDriverView,
    PriorityListDeleteView,
    PriorityListView,
    ResolveConflictView,
)

urlpatterns = [
    path("deliveries/", AdminDeliveryListView.as_view(), name="admin-delivery-list"),
    path("priority/", PriorityListView.as_view(), name="admin-priority-list"),
    path("priority/<int:driver_id>/", PriorityListDeleteView.as_view(), name="admin-priority-delete"),
    path("deliveries/<int:pk>/notify/all/", NotifyAllPriorityDriversView.as_view(), name="admin-notify-all"),
    path("deliveries/<int:pk>/notify/everyone/", NotifyEveryoneDriversView.as_view(), name="admin-notify-everyone"),
    path("deliveries/<int:pk>/notify/<int:driver_id>/", NotifySpecificDriverView.as_view(), name="admin-notify-one"),
    path("deliveries/<int:pk>/resolve/", ResolveConflictView.as_view(), name="admin-resolve"),
    path("deliveries/<int:pk>/cancel/", CancelDeliveryView.as_view(), name="admin-delivery-cancel"),
    path("trips/<int:delivery_id>/summary/", AdminTripSummaryView.as_view(), name="admin-trip-summary"),
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("users/<int:pk>/deactivate/", DeactivateUserView.as_view(), name="admin-user-deactivate"),
    path("users/<int:pk>/activate/", ActivateUserView.as_view(), name="admin-user-activate"),
]
