from django.contrib import admin
from .models import RankingBatch, RankingResult

@admin.register(RankingBatch)
class RankingBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "created_by", "status", "created_at", "completed_at")
    list_filter = ("status", "created_at")

@admin.register(RankingResult)
class RankingResultAdmin(admin.ModelAdmin):
    list_display = ("id", "batch", "job", "resume", "score", "created_at")
    ordering = ("-score",)
    list_filter = ("job", "batch", "created_at")
