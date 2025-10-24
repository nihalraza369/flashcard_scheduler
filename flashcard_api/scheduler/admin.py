# Register your models here.
from django.contrib import admin
from .models import UserCardState, ReviewRecord

@admin.register(UserCardState)
class UserCardStateAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'card_id', 'next_review', 'last_interval_seconds')

@admin.register(ReviewRecord)
class ReviewRecordAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'card_id', 'rating', 'reviewed_at', 'idempotency_key')
