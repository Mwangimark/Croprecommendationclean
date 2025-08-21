from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import uuid
from .services import handle_message
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated

class ChatbotAPIView(APIView):
    """
    POST /api/chatbot/  payload: { "message": "...", "session_id": "optional" }
    Returns: { "reply": "...", "session_id": "..." }
    """
    permission_classes = [IsAuthenticated]  # add authentication if needed

    def post(self, request):
        payload = request.data
        user_message = payload.get("message", "").strip()
        if not user_message:
            return Response({"error": "message is required"}, status=status.HTTP_400_BAD_REQUEST)

        session_id = payload.get("session_id") or str(uuid.uuid4())
        user = None
        if request.user and request.user.is_authenticated:
            user = request.user

        try:
            reply = handle_message(session_id=session_id, user_message=user_message, user=user)
            return Response({"reply": reply, "session_id": session_id}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




