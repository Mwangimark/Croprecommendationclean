from rest_framework import serializers
from .models import User
from .utils import send_verification_email
from django.contrib.auth.hashers import make_password

from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User
from .utils import send_verification_email  # your helper

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        read_only_fields = ['id', 'role', 'created_at', 'is_deleted']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        user = super().create(validated_data)
        send_verification_email(user, self.context['request'])
        return user

    def update(self, instance, validated_data):
        # Prevent rehashing password if not provided
        password = validated_data.get('password', None)
        if password:
            validated_data['password'] = make_password(password)
        else:
            validated_data.pop('password', None)

        return super().update(instance, validated_data)

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

# users/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data['user'] = {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'phone': user.phone,
            'role': user.role,
        }
        return data




# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'email', 'name', 'created_at', 'updated_at']  # or all fields you want
