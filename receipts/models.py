from django.db import models
from django.contrib.auth.models import User


class Receipt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receipts')
    image = models.ImageField(upload_to='receipts/raw/')
    raw_text = models.TextField(blank=True)
    extracted_data = models.JSONField(default=dict, blank=True)
    transaction = models.OneToOneField(
        'transactions.Transaction', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='receipt_obj'
    )
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receipt #{self.pk} — {self.user.username} ({self.created_at.date()})"
