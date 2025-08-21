from rest_framework import viewsets
from .models import RecommendationCrop
from .serializers import RecommendationCropSerializer

class RecommendationCropViewSet(viewsets.ModelViewSet):
    queryset = RecommendationCrop.objects.all()
    serializer_class = RecommendationCropSerializer