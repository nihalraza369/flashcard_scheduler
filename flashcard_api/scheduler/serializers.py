from rest_framework import serializers
from .models import ReviewRecord, UserCardState

class ReviewRequestSerializer(serializers.Serializer):
    idempotency_key = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    user_id = serializers.CharField()
    card_id = serializers.CharField()
    rating = serializers.IntegerField(min_value=0, max_value=2)
    reviewed_at = serializers.DateTimeField(required=False)

class ReviewResponseSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    card_id = serializers.CharField()
    next_review_at = serializers.DateTimeField()
    last_interval_seconds = serializers.IntegerField(allow_null=True)
