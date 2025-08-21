from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import CropViewSet
from crops.views import SoilInputsRetrieval

router = DefaultRouter()
router.register(r'crops',CropViewSet)

urlpatterns = [

    path('',include(router.urls)),
    path('soil-inputs/', SoilInputsRetrieval.as_view(), name='soil-inputs'),
]