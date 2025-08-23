# subscriptions/permissions.py
from rest_framework.permissions import BasePermission

class HasActiveSubscription(BasePermission):
    message = "Subscription required to use the chatbot."

    def has_permission(self, request, view):
        sub = getattr(request.user, "subscription", None)
        return bool(sub and sub.is_valid())
