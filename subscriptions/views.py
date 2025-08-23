# check subscription status
# subscriptions/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class SubscriptionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub = getattr(request.user, "subscription", None)
        if sub and sub.is_valid():
            return Response({
                "is_active": True,
                "start_date": sub.start_date,
                "end_date": sub.end_date
            })
        return Response({"is_active": False})
