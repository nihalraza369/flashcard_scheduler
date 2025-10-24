from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import transaction, IntegrityError
from .models import ReviewRecord, UserCardState
from .serializers import ReviewRequestSerializer, ReviewResponseSerializer
from datetime import timedelta

# Tunable parameters
INITIAL_INTERVAL_2_DAYS = 30      # first-review rating 2 => 30 days
INITIAL_INTERVAL_1_DAYS = 3       # first-review rating 1 => 3 days
RETRY_INTERVAL_SECONDS = 60       # rating 0 => retry in 60 seconds
MUL_2 = 4                         # multiply factor for rating 2
MUL_1 = 2                         # multiply factor for rating 1

def compute_next_interval(prev_interval_seconds, rating, is_first):
    """
    Compute next interval in seconds given previous interval and rating.
    Enforces monotonicity by caller.
    """
    if rating == 0:
        return RETRY_INTERVAL_SECONDS

    if is_first:
        if rating == 2:
            return INITIAL_INTERVAL_2_DAYS * 86400
        else:  # rating == 1
            return INITIAL_INTERVAL_1_DAYS * 86400

    # subsequent reviews
    if rating == 2:
        candidate = (prev_interval_seconds or (INITIAL_INTERVAL_2_DAYS * 86400)) * MUL_2
    else:  # rating == 1
        candidate = (prev_interval_seconds or (INITIAL_INTERVAL_1_DAYS * 86400)) * MUL_1

    new_interval = int(candidate)
    # monotonicity handled by caller (max with prev)
    return new_interval

class ReviewView(APIView):
    """
    POST /api/reviews/
    """
    def post(self, request):
        serializer = ReviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        idemp = data.get('idempotency_key') or None
        user_id = data['user_id']
        card_id = data['card_id']
        rating = data['rating']
        reviewed_at = data.get('reviewed_at') or timezone.now()

        # If idempotency_key provided and existing record, return it (idempotency)
        if idemp:
            try:
                existing = ReviewRecord.objects.get(idempotency_key=idemp)
                resp = {
                    "user_id": existing.user_id,
                    "card_id": existing.card_id,
                    "next_review_at": existing.next_review_at,
                    "last_interval_seconds": int((existing.next_review_at - existing.reviewed_at).total_seconds()) if existing.next_review_at and existing.reviewed_at else None
                }
                return Response(ReviewResponseSerializer(resp).data)
            except ReviewRecord.DoesNotExist:
                pass

        # ACID operation: lock the state row for update to avoid race
        with transaction.atomic():
            state, created = UserCardState.objects.select_for_update().get_or_create(
                user_id=user_id, card_id=card_id,
                defaults={'next_review': None, 'last_interval_seconds': None, 'last_reviewed_at': None}
            )

            prev_interval = state.last_interval_seconds
            is_first = (prev_interval is None and state.last_reviewed_at is None)

            # compute candidate interval
            next_interval = compute_next_interval(prev_interval, rating, is_first)

            # enforce monotonicity: new interval >= prev_interval (if exists)
            if prev_interval:
                next_interval = max(prev_interval, int(next_interval))

            next_review_at = reviewed_at + timedelta(seconds=int(next_interval))

            # If the state already has a later next_review (someone else set), maintain monotonicity:
            if state.next_review and next_review_at < state.next_review:
                # Keep the later next_review; adjust interval accordingly
                next_review_at = state.next_review
                next_interval = int((next_review_at - reviewed_at).total_seconds())

            # Save ReviewRecord; idempotency key unique constraint avoids duplicates
            record = ReviewRecord(
                idempotency_key=idemp,
                user_id=user_id,
                card_id=card_id,
                rating=rating,
                reviewed_at=reviewed_at,
                next_review_at=next_review_at
            )
            try:
                record.save()
            except IntegrityError:
                # race: another request saved same idempotency_key
                existing = ReviewRecord.objects.get(idempotency_key=idemp)
                resp = {
                    "user_id": existing.user_id,
                    "card_id": existing.card_id,
                    "next_review_at": existing.next_review_at,
                    "last_interval_seconds": int((existing.next_review_at - existing.reviewed_at).total_seconds()) if existing.next_review_at and existing.reviewed_at else None
                }
                return Response(ReviewResponseSerializer(resp).data)

            # update state
            state.next_review = next_review_at
            state.last_interval_seconds = int(next_interval)
            state.last_reviewed_at = reviewed_at
            state.save()

        resp = {
            "user_id": user_id,
            "card_id": card_id,
            "next_review_at": next_review_at,
            "last_interval_seconds": int(next_interval)
        }
        return Response(ReviewResponseSerializer(resp).data, status=status.HTTP_201_CREATED)


class DueCardsView(APIView):
    """
    GET /api/users/{id}/due-cards?until=ISO8601
    """
    def get(self, request, user_id):
        until = request.query_params.get('until')
        if not until:
            return Response({"detail": "Missing 'until' query parameter (ISO8601). Example: ?until=2025-10-30T00:00:00Z"}, status=400)

        from django.utils.dateparse import parse_datetime
        until_dt = parse_datetime(until)
        from django.utils import timezone as djtz
        if until_dt is None:
            return Response({"detail": "Invalid datetime format for 'until'."}, status=400)
        if djtz.is_naive(until_dt):
            until_dt = djtz.make_aware(until_dt, djtz.utc)

        qs = UserCardState.objects.filter(user_id=user_id, next_review__lte=until_dt)
        results = [{"card_id": s.card_id, "next_review": s.next_review, "last_interval_seconds": s.last_interval_seconds} for s in qs]
        return Response(results)
