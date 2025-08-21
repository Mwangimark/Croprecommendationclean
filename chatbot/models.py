from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import json

class ConversationState(models.Model):
    """
    Stores conversation state for a session.
    """
    session_id = models.CharField(max_length=128, db_index=True)
    user = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL)
    history = models.JSONField(default=list, encoder=DjangoJSONEncoder)  # list of {"role":"user"/"bot","text":...}
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["session_id"]),
        ]

    def append(self, role: str, text: str):
        self.history.append({"role": role, "text": text, "ts": timezone.now().isoformat()})
        self.save()
