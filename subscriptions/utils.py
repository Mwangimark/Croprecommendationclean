# mpesa/utils.py
import base64
import datetime
import re
import requests
from django.conf import settings

class MpesaError(Exception):
    pass

def get_access_token() -> str:
    """Fetch OAuth token using your Consumer Key/Secret."""
    url = f"{settings.MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    resp = requests.get(url, auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET), timeout=15)
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise MpesaError(f"Failed to get access token: {data}")
    return token

def normalize_msisdn(phone: str) -> str:
    """
    Convert common Kenyan formats to 2547XXXXXXXX.
    Accepts: 07XXXXXXXX, 7XXXXXXXX, +2547XXXXXXXX, 2547XXXXXXXX.
    """
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("0") and len(digits) == 10:
        return "254" + digits[1:]
    if digits.startswith("7") and len(digits) == 9:
        return "254" + digits
    if digits.startswith("254") and len(digits) == 12:
        return digits
    if phone.startswith("+254") and len(digits) == 12:
        return digits  # +2547... becomes 2547...
    raise MpesaError("Invalid phone number format. Use e.g. 07XXXXXXXX or 2547XXXXXXXX")

def _generate_password(shortcode: str, passkey: str, timestamp: str) -> str:
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")

def stk_push(*, phone: str, amount: int, account_reference: str, transaction_desc: str, callback_url: str = None) -> dict:
    """
    Initiate STK Push (Lipa na M-Pesa Online).
    Returns Daraja API JSON (MerchantRequestID / CheckoutRequestID / ResponseCode, etc.)
    """
    msisdn = normalize_msisdn(phone)
    token = get_access_token()

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password = _generate_password(settings.MPESA_SHORTCODE, settings.MPESA_PASSKEY, timestamp)

    url = f"{settings.MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": msisdn,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": msisdn,
        "CallBackURL": callback_url or settings.MPESA_CALLBACK_URL,
        "AccountReference": account_reference[:12] or "SUBSCRIPTION",
        "TransactionDesc": (transaction_desc or "Subscription Payment")[:60],
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    # Optional basic sanity check
    if str(data.get("ResponseCode")) != "0":
        # Daraja sometimes returns e.g. "200" HTTP but non-zero ResponseCode
        raise MpesaError(f"STK push failed: {data}")

    return data
