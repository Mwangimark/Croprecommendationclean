from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from message.permissions.is_admin import IsAdmin

from .models import Message
from .serializers import MessageSerializer

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.filter(is_deleted=False)
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        message = self.get_object()
        if message.sender != request.user:
            return Response({
                'detail':'You can only delete your own message'
            },status=status.HTTP_403_FORBIDDEN)
        
        message.is_deleted = True
        message.save()
        return Response({'message': 'Message successfully deleted'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='conversations')
    def user_conversation(self, request):
        user_id  = request.user.id

        messages = Message.objects.filter(
            Q(sender_id=user_id) | Q(receiver_id=user_id),
            is_deleted=False
        ).order_by('-sent_at')

        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

    # messages/views.py

    def perform_create(self, serializer):
        sender = self.request.user
        receiver = serializer.context.get('receiver')

        print("🧾 SENDER ID:", sender.id)
        print("👤 SENDER ROLE:", sender.role)
        print("📥 RECEIVER ID:", receiver.id if receiver else "None")

        if not receiver:
            raise ValidationError("Receiver is required.")

        if sender.role == 'admin':
            serializer.save(sender=sender, receiver=receiver)
        elif receiver.role == 'admin':
            serializer.save(sender=sender, receiver=receiver)

        else:
            raise ValidationError("Users can only send messages to the admin.")

        
    def create(self, request, *args, **kwargs):
        print("🔧 Inside create view")
        print("Request data:", request.data)

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("❌ Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        print("✅ Serializer valid")
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

    def get_queryset(self):
        user = self.request.user
        queryset = Message.objects.filter(is_deleted =False)

        if user.role == 'admin':
            sender_id = self.request.query_params.get('sender')
            if sender_id:
                queryset = queryset.filter(sender_id = sender_id)
        else:
            queryset = queryset.filter(Q(sender = user) | Q(receiver = user))
        return queryset.order_by('-sent_at')
    
       
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        elif self.action == 'list':
            return [IsAuthenticated(),IsAdmin()]
        elif self.action in ['retrieve','update','destroy','user_conversation','my_conversation']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]



