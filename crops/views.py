from rest_framework import viewsets
from .models import Crop, Nutrients
from .serializers import CropSerializer, NutrientsSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from users.permission import IsAdmin
from rest_framework.views import APIView


class CropViewSet(viewsets.ModelViewSet):
    queryset = Crop.objects.all()
    serializer_class = CropSerializer

    def destroy(self, request, *args, **kwargs):
        crop = self.get_object()
        crop.delete()
        return Response({'message':'crops successfully delete'},status = status.HTTP_200_OK)
    
    def get_permissions(self):
          if self.action in ['create']:
                return [AllowAny()]
          elif self.action == 'list':
                return [IsAuthenticated()]
          elif self.action in 'retrieve':
                return[IsAuthenticated()]
          return [IsAuthenticated( )]
    
class SoilInputsRetrieval(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        soil_inputs = Nutrients.objects.all()
        data = [
            {
                "name": nutrient.name,
                "intro": nutrient.intro,
                "description": nutrient.description,
                "links": nutrient.links.split(',') if nutrient.links else [],
                "image_url": nutrient.image_url,
                "photo_url": request.build_absolute_uri(nutrient.photo.url) if nutrient.photo else None
            }
            for nutrient in soil_inputs
        ]
        return Response(data, status=status.HTTP_200_OK)
