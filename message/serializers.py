from rest_framework import serializers
from .models import Message
from users.models import User

class MessageSerializer(serializers.ModelSerializer):
    receiver_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['id', 'sender', 'receiver', 'sent_at', 'is_read', 'is_deleted']

    def validate_receiver_id(self, value):
        try:
            receiver = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Receiver does not exist.")
        self.context['receiver'] = receiver
        return value
