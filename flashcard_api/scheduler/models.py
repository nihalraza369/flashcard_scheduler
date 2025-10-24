from django.db import models
from django.utils import timezone

class UserCardState(models.Model):
    """
    Stores the scheduling state per user + card.
    """
    user_id = models.CharField(max_length=128, db_index=True)
    card_id = models.CharField(max_length=128, db_index=True)
    next_review = models.DateTimeField(null=True, blank=True, db_index=True)
    last_interval_seconds = models.BigIntegerField(null=True, blank=True)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_id', 'card_id')

    def __str__(self):
        return f"{self.user_id}:{self.card_id}"

class ReviewRecord(models.Model):
    """
    Immutable record for each review. idempotency_key ensures duplicate requests handled once.
    """
    idempotency_key = models.CharField(max_length=256, unique=True, null=True, blank=True)
    user_id = models.CharField(max_length=128, db_index=True)
    card_id = models.CharField(max_length=128, db_index=True)
    rating = models.IntegerField()  # 0,1,2
    reviewed_at = models.DateTimeField(default=timezone.now)
    next_review_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user_id', 'card_id']),
        ]
