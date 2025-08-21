from django.db import models
from users.models import User

# Create your models here.
class Message(models.Model):
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table = 'messages'

    def __str__(self):
        return f"Message from {self.sender.name} to {self.receiver.name}"
