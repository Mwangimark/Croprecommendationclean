from rest_framework import serializers
from .models import RecommendationCrop
from crops.models import Crop

# class CropSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Crop
#         fields = ['id','name','image','description']


class RecommendationCropSerializer(serializers.ModelSerializer):
    crop = serializers.PrimaryKeyRelatedField(queryset=Crop.objects.all())

    class Meta:
        model = RecommendationCrop
        fields = '__all__'
        extra_kwargs = {
            'recommendation': {'required': False}
        }