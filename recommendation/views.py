from rest_framework import viewsets
from .models import Recommendation
from .serializers import RecommendationSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated,AllowAny
from crops.models import Crop
from recommendationcrop.models import RecommendationCrop
from django.contrib.auth import get_user_model
from .ml_model.utils import predict_top_crops
from django.core.exceptions import PermissionDenied




User = get_user_model()
class RecommendationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Recommendation.objects.filter(is_deleted = False)
    serializer_class = RecommendationSerializer

    # models
    def create(self, request, *args, **kwargs):
        try:
            user = request.user
            data = request.data.copy()

            # ✅ Extract features in correct order
            features = [
                float(data.get("nitrogen")),
                float(data.get("phosphorus")),
                float(data.get("potassium")),
                float(data.get("temperature")),
                float(data.get("humidity")),
                float(data.get("ph")),
                float(data.get("rainfall")),
            ]

            # 🔍 Predict top 3 crops
            top3 = predict_top_crops(features)  # [('mango', 0.32), ('pomegranate', 0.28), ('coffee', 0.1)]

            for name, conf in top3:
                print(f" - {name}: {round(conf * 100, 2)}% confidence")

            # ✅ Save the recommendation
            data['user'] = user.id
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            recommendation = serializer.save()

            # ✅ Link recommended crops using name match
            for name, confidence in top3:
                print(f"'looking for crop name {name}'")
                try:
                    crop = Crop.objects.get(name__iexact=name)
                    print(f"'looking for crop name {crop.name}'")
                    RecommendationCrop.objects.create(
                        recommendation=recommendation,
                        crop=crop,
                        confidence=confidence  # Store exact model confidence score
                    )
                except Crop.DoesNotExist:
                    print(f"⚠️ Crop '{name}' not found in DB. Skipping.")

            return Response(self.get_serializer(recommendation).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"❌ Exception in create: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


    # models end
    
    
    @action(detail=False, methods=['get'], url_path='my-recommendations')
    def recommendations_by_user(self, request, user_id=None):
        user = request.user

        
        recommendations = Recommendation.objects.filter(
            user = user,
            is_deleted=False
        ).order_by('-predicted_date')

        serializer = self.get_serializer(recommendations, many=True)
        return Response(serializer.data)
    
    
    def destroy(self, request, *args, **kwargs):
        recommendation = self.get_object()

        if request.user != recommendation.user and request.user.role != 'admin':
            raise PermissionDenied ("you are not allowed to view this recommendation.")


        recommendation.is_deleted = True
        recommendation.save()

        # Optional: Also soft-delete related recommended crops
        recommendation.recommended_crops.update(is_deleted=True)

        return Response({'message': 'Recommendation deleted successfully (soft delete)'}, status=status.HTTP_204_NO_CONTENT)
    
     # confirming_authentication
    def get_permissions(self):
        if self.action in ['create', 'recommendations_by_user', 'destroy']:
            return [IsAuthenticated()]
        return super().get_permissions()


    


    def list(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            raise PermissionDenied("Only admins can view all recommendations.")
        return super().list(request, *args, **kwargs)


    


    