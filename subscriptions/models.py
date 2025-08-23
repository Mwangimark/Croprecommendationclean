from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, F, JSONField

class Subscribe(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription"
    )
    start_date = models.DateTimeField(null=True, blank=True)
    end_date   = models.DateTimeField(null=True, blank=True)
    is_active  = models.BooleanField(default=False, db_index=True)

    # Snapshot
    name  = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)

    # M-Pesa last transaction snapshot (optional)
    mpesa_receipt    = models.CharField(max_length=50, unique=True, null=True, blank=True)
    amount           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    phone_number     = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    transaction_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "subscriptions_subscription"
        indexes = [
            models.Index(fields=["end_date"]),
            models.Index(fields=["is_active", "end_date"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(end_date__gte=F("start_date")) | Q(end_date__isnull=True) | Q(start_date__isnull=True),
                name="end_after_start_or_null",
            ),
        ]

    def activate_subscription(self, days=30, *, amount=None, receipt=None, phone=None, when=None):
        now = when or timezone.now()
        # If active, extend from current end_date; else start now
        base = self.end_date if (self.is_active and self.end_date and self.end_date >= now) else now
        self.start_date = self.start_date or now
        self.end_date   = base + timedelta(days=days)
        self.is_active  = True

        # Snapshot
        self.name  = getattr(self.user, "name", "") or ""
        self.email = getattr(self.user, "email", "") or ""
        if amount is not None:
            self.amount = amount
        if receipt:
            self.mpesa_receipt = receipt
        if phone:
            self.phone_number = phone
        self.transaction_date = now
        self.save()

    def is_valid(self):
        return bool(self.is_active and self.end_date and self.end_date >= timezone.now())

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["is_active"])

    def __str__(self):
        status = "Active" if self.is_valid() else "Expired"
        return f"{getattr(self.user, 'email', self.user_id)} — {status}"


class PaymentTransaction(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        PAID = "PAID"
        FAILED = "FAILED"
        CANCELLED = "CANCELLED"
        EXPIRED = "EXPIRED"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone  = models.CharField(max_length=20)

    # IDs from STK push
    merchant_request_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    checkout_request_id = models.CharField(max_length=100, null=True, blank=True, unique=True)

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    result_code = models.IntegerField(null=True, blank=True)
    result_desc = models.CharField(max_length=255, blank=True)

    mpesa_receipt = models.CharField(max_length=50, null=True, blank=True, unique=True)
    transaction_datetime = models.DateTimeField(null=True, blank=True)

    raw_callback = JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def mark_paid_once(self, *, receipt, trans_dt, result_code=0, result_desc="OK", raw=None):
        """Idempotent: only process first successful payment."""
        with transaction.atomic():
            pt = PaymentTransaction.objects.select_for_update().get(pk=self.pk)
            if pt.status == PaymentTransaction.Status.PAID:
                return False  # already processed
            pt.status = PaymentTransaction.Status.PAID
            pt.result_code = result_code
            pt.result_desc = result_desc
            pt.mpesa_receipt = receipt
            pt.transaction_datetime = trans_dt
            pt.raw_callback = raw or pt.raw_callback
            pt.processed_at = timezone.now()
            pt.save(update_fields=[
                "status","result_code","result_desc","mpesa_receipt",
                "transaction_datetime","raw_callback","processed_at","updated_at"
            ])
            return True
