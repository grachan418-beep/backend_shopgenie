from django.urls import path
from .views import WorkerViewSet

worker_list = WorkerViewSet.as_view({"get": "list", "post": "create"})
worker_detail = WorkerViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})

urlpatterns = [
    path("", worker_list, name="worker-list"),
    path("<int:pk>/", worker_detail, name="worker-detail"),
]
