# Create your tests here.
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
import datetime
from .models import ReviewRecord, UserCardState

class SchedulerTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def post_review(self, payload):
        return self.client.post('/api/reviews/', payload, format='json')

    def test_rating_zero_immediate_retry(self):
        resp = self.post_review({"user_id": "u1", "card_id": "c1", "rating": 0})
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        next_dt = timezone.datetime.fromisoformat(data['next_review_at'].replace('Z', '+00:00'))
        now = timezone.now()
        diff = (next_dt - now).total_seconds()
        self.assertTrue(diff <= 90)  # should be ~60s

    def test_first_review_rating2_long(self):
        resp = self.post_review({"user_id": "u2", "card_id": "c2", "rating": 2})
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        next_dt = timezone.datetime.fromisoformat(data['next_review_at'].replace('Z', '+00:00'))
        now = timezone.now()
        diff_days = (next_dt - now).days
        self.assertTrue(diff_days >= 28)  # ~30 days

    def test_monotonicity(self):
        # first give rating 2 -> long interval
        r1 = self.post_review({"user_id": "u3", "card_id": "c3", "rating": 2})
        self.assertEqual(r1.status_code, 201)
        old = r1.json()['next_review_at']
        # now later give rating 1; monotonicity should not shorten
        r2 = self.post_review({"user_id": "u3", "card_id": "c3", "rating": 1})
        self.assertEqual(r2.status_code, 201)
        self.assertTrue(r2.json()['next_review_at'] >= old)

    def test_idempotency(self):
        key = "idem-key-123"
        p = {"idempotency_key": key, "user_id": "u4", "card_id": "c4", "rating": 1}
        r1 = self.post_review(p)
        r2 = self.post_review(p)
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 200)  # duplicate returns existing record
        self.assertEqual(r1.json()['next_review_at'], r2.json()['next_review_at'])
