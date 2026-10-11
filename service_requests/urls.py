from django.urls import path

from .views import RequestCollectionView, RequestDetailView, RequestStatusView

urlpatterns = [
    path("requests", RequestCollectionView.as_view()),
    path("requests/<str:pk>", RequestDetailView.as_view()),
    path("requests/<str:pk>/status", RequestStatusView.as_view()),
]
