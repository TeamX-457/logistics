from django.urls import path

from . import views

urlpatterns = [
    path("admin-panel/resources/", views.AdminCatalogView.as_view(), name="admin-panel-catalog"),
    path("admin-panel/resources/<str:resource>/", views.AdminResourceListCreateView.as_view(), name="admin-panel-resource-list"),
    path("admin-panel/resources/<str:resource>/schema/", views.AdminResourceSchemaView.as_view(), name="admin-panel-resource-schema"),
    path("admin-panel/resources/<str:resource>/<int:pk>/", views.AdminResourceDetailView.as_view(), name="admin-panel-resource-detail"),
]
