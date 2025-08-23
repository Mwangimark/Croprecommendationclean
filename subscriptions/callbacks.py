import json
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
import logging

from .models import PaymentTransaction, Subscribe

def parse_callback_dt(s: str):
    # e.g. "20250823132711"
    try:
        dt = datetime.strptime(str(s), "%Y%m%d%H%M%S")
        return timezone.make_aware(dt, timezone.get_current_timezone())
    except Exception:
        return timezone.now()
    
logger = logging.getLogger(__name__)


@csrf_exempt
def mpesa_callback(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    try:
        data = json.loads(request.body.decode("utf-8"))
        stk = data["Body"]["stkCallback"]
        result_code = int(stk.get("ResultCode", -1))
        result_desc = stk.get("ResultDesc", "")
        checkout_id = stk.get("CheckoutRequestID")
        items = stk.get("CallbackMetadata", {}).get("Item", [])
        meta = {i.get("Name"): i.get("Value") for i in items}


        try:
            pt = PaymentTransaction.objects.select_related("user").get(checkout_request_id=checkout_id)
        except PaymentTransaction.DoesNotExist:
            # Unknown checkout: accept to stop retries but log/monitor this
            return JsonResponse({"ResultCode": 0, "ResultDesc": "OK"})

        if result_code == 0:
            receipt = meta.get("MpesaReceiptNumber")
            amount  = meta.get("Amount")
            phone   = meta.get("PhoneNumber")
            trans_dt = parse_callback_dt(meta.get("TransactionDate"))

            # Mark paid ONCE
            changed = pt.mark_paid_once(
                receipt=receipt,
                trans_dt=trans_dt,
                result_code=result_code,
                result_desc=result_desc,
                raw=data
            )

            if changed:
                # Activate/extend subscription
                sub, _ = Subscribe.objects.get_or_create(user=pt.user)
                sub.activate_subscription(
                    days=int(getattr(settings, "SUBSCRIPTION_DAYS", 30)),
                    amount=amount,
                    receipt=receipt,
                    phone=phone,
                    when=trans_dt
                )
        else:
            # failure path
            pt.status = PaymentTransaction.Status.FAILED
            pt.result_code = result_code
            pt.result_desc = result_desc
            pt.raw_callback = data
            pt.processed_at = timezone.now()
            pt.save(update_fields=["status","result_code","result_desc","raw_callback","processed_at","updated_at"])

        return JsonResponse({"ResultCode": 0, "ResultDesc": "OK"})
    except Exception as e:
        # Always ack to avoid repeated retries; but log the error
        return JsonResponse({"ResultCode": 0, "ResultDesc": f"err:{e}"})
