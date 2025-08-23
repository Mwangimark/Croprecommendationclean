from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.conf import settings
from django.utils import timezone

from .models import PaymentTransaction
from .mpesa import initiate_stk_push, normalize_msisdn

class SubscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        amount = int(settings.SUBSCRIPTION_PRICE)
        phone  = normalize_msisdn(request.data.get("phone") or getattr(request.user, "phone", ""))

        if not phone:
            return Response({"error": "Phone number required"}, status=400)

        # Create pending transaction
        pt = PaymentTransaction.objects.create(
            user=request.user,
            amount=amount,
            phone=phone,
        )
        try:
            resp = initiate_stk_push(amount=amount, phone=phone, account_ref=f"SUB-{request.user.id}")
            pt.merchant_request_id = resp.get("MerchantRequestID")
            pt.checkout_request_id = resp.get("CheckoutRequestID")
            pt.result_desc = resp.get("ResponseDescription", "")
            pt.save(update_fields=["merchant_request_id", "checkout_request_id", "result_desc", "updated_at"])

            return Response({
                "message": "STK push sent. Enter PIN on your phone.",
                "checkout_request_id": pt.checkout_request_id,
                "merchant_request_id": pt.merchant_request_id,
                "amount": amount,
                "phone": phone
            }, status=200)
        except Exception as e:
            pt.status = PaymentTransaction.Status.FAILED
            pt.result_desc = f"init_error: {e}"
            pt.save(update_fields=["status", "result_desc", "updated_at"])
            return Response({"error": "Failed to initiate STK push"}, status=502)
