from django.db import models
from django.conf import settings

class RankingBatch(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    job = models.ForeignKey("jobs.JobDescription", on_delete=models.CASCADE, related_name="batches")
    resumes = models.ManyToManyField("resumes.Resume", related_name="batches")

    status = models.CharField(
        max_length=30,
        default="queued",
        choices=[("queued","queued"),("running","running"),("completed","completed"),("failed","failed")],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class RankingResult(models.Model):
    batch = models.ForeignKey(RankingBatch, on_delete=models.CASCADE, related_name="results")
    job = models.ForeignKey("jobs.JobDescription", on_delete=models.CASCADE, related_name="results")
    resume = models.ForeignKey("resumes.Resume", on_delete=models.CASCADE, related_name="results")

    score = models.PositiveSmallIntegerField()
    score_breakdown = models.JSONField(default=dict, blank=True)

    reasoning = models.TextField(blank=True)
    missing_required = models.JSONField(default=list, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    candidate_suggestions = models.JSONField(default=list, blank=True)
    model_meta = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["batch", "job", "resume"], name="uniq_result_per_batch"),
        ]
