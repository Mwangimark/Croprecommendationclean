import base64, json, requests
from datetime import datetime
from django.conf import settings

def mpesa_timestamp():
    return datetime.now().strftime("%Y%m%d%H%M%S")

def mpesa_password(shortcode, passkey, timestamp):
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode()).decode()

def normalize_msisdn(phone: str) -> str:
    p = "".join(ch for ch in phone if ch.isdigit())
    if p.startswith("0"):      # 07xx...
        return "254" + p[1:]
    if p.startswith("254"):    # already OK
        return p
    if p.startswith("+254"):
        return p[1:]
    # fallback: assume Kenyan line without 0
    if len(p) == 9:  # 7xxxxxxxx
        return "254" + p
    return p

def get_access_token():
    url = f"{settings.MPESA_BASE}/oauth/v1/generate?grant_type=client_credentials"
    resp = requests.get(url, auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET), timeout=15)
    resp.raise_for_status()
    return resp.json()["access_token"]

def initiate_stk_push(amount: int, phone: str, account_ref="SUB", tx_desc="Subscription"):
    timestamp = mpesa_timestamp()
    password  = mpesa_password(settings.MPESA_SHORTCODE, settings.MPESA_PASSKEY, timestamp)
    token     = get_access_token()

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": account_ref,
        "TransactionDesc": tx_desc
    }

    url = f"{settings.MPESA_BASE}/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(url, json=payload, headers=headers, timeout=25)
    data = resp.json()
    # Raise for non-0 ResponseCode or HTTP error
    resp.raise_for_status()
    if str(data.get("ResponseCode")) != "0":
        raise ValueError(data)
    return data  # contains MerchantRequestID, CheckoutRequestID, etc.
