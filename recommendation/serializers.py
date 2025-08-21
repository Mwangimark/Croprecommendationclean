from rest_framework import serializers
from .models import Recommendation
from recommendationcrop.models import RecommendationCrop
from recommendationcrop.serializers import RecommendationCropSerializer
from crops.models import Crop  # Import your Crops model

# class RecommendationSerializer(serializers.ModelSerializer):
#     recommended_crops = RecommendationCropSerializer(many=True,read_only = True)

#     class Meta:
#         model = Recommendation
#         fields = '__all__'


class RecommendationSerializer(serializers.ModelSerializer):
    predicted_crops = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = '__all__'

    def get_predicted_crops(self, obj):
        request = self.context.get('request')  # for building absolute image URLs
        crops = RecommendationCrop.objects.filter(recommendation=obj)

        return [
            {
                "name": crop.crop.name,
                "confidence": round(crop.confidence, 2),
                "description": crop.crop.description,
                "image": request.build_absolute_uri(crop.crop.image.url) if crop.crop.image else None
            }
            for crop in crops
        ]

