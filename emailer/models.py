from django.db import models
import uuid
from django.utils import timezone


class BulkCampaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    template_used = models.CharField(max_length=50)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({'Completed' if self.is_completed else 'Pending'})"


class Recipient(models.Model):
    campaign = models.ForeignKey(BulkCampaign, on_delete=models.CASCADE, related_name='recipients')
    email = models.EmailField()
    recipient_name = models.CharField(max_length=100)  # Can be company name or individual name
    last_name = models.CharField(max_length=50, blank=True)  # Optional for individuals
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='pending')  # 'pending', 'sent', 'failed'
    
    class Meta:
        ordering = ['-campaign__created_at']
        
    def __str__(self):
        full_name = f"{self.recipient_name} {self.last_name}".strip()
        return f"{full_name} <{self.email}>"