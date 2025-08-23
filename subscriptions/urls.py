from django.urls import path

from .views import SubscriptionStatusView
from .api import SubscribeView
from .callbacks import mpesa_callback

urlpatterns = [
    path("billing/subscribe/", SubscribeView.as_view(), name="subscribe"),
    path("callback/", mpesa_callback, name="mpesa-callback"),
    path("subscription-status/", SubscriptionStatusView.as_view(), name="subscription-status"),

]
