# mpesa/serializers.py
from rest_framework import serializers

class InitiatePaymentSerializer(serializers.Serializer):
    phone = serializers.CharField()
    amount = serializers.IntegerField(min_value=1, default=100)  # demo fee
