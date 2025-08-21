from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import RecommendationCropViewSet

router = DefaultRouter()
router.register(r'recommendationcrop',RecommendationCropViewSet)

urlpatterns = [
    path('',include(router.urls))
]