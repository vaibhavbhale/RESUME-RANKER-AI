from django.db import models
from django.conf import settings

class JobDescription(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="job_descriptions")
    title = models.CharField(max_length=255)
    raw_text = models.TextField()

    extracted = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
