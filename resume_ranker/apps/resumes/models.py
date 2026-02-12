from django.db import models
from django.conf import settings

class Resume(models.Model):
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resumes")

    file = models.FileField(upload_to="resumes/%Y/%m/%d/")
    original_filename = models.CharField(max_length=255, blank=True)

    extracted_text = models.TextField(blank=True)
    extracted = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=30,
        default="uploaded",
        choices=[
            ("uploaded", "uploaded"),
            ("extracting", "extracting"),
            ("parsed", "parsed"),
            ("failed", "failed"),
        ],
    )
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_filename or self.file.name
