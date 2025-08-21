from rest_framework import serializers
from users.models import User
from crops.models import Crop
from message.models import Message
from recommendation.models import Recommendation
from recommendationcrop.models import RecommendationCrop

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class CropSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crop
        fields = '__all__'

class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = '__all__'

class RecommendationCropSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationCrop
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
