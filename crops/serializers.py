from rest_framework import serializers
from .models import Crop,Nutrients


class CropSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Crop
        fields = '__all__'  # Keeps all fields from Crop model
        extra_fields = ['image_url']  # For clarity, not required

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None




class NutrientsSerializer(serializers.ModelSerializer):
    # Add a read-only field for the full photo URL
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Nutrients
        fields = '__all__'  # This will include photo_url
        read_only_fields = ('id', 'created_at', 'updated_at', 'photo_url')

    def validate_image_url(self, value):
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Image URL must start with http:// or https://")
        return value

    def get_photo_url(self, obj):
        """Return absolute URL for the photo if it exists."""
        request = self.context.get('request')
        if obj.photo:
            return request.build_absolute_uri(obj.photo.url)
        return None
 