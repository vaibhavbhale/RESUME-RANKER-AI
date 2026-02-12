from django.contrib import admin
from .models import Resume

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("id", "original_filename", "uploaded_by", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("original_filename",)
