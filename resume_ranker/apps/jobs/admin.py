from django.contrib import admin
from .models import JobDescription

@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_by", "created_at")
    search_fields = ("title", "raw_text")
    list_filter = ("created_at",)

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
