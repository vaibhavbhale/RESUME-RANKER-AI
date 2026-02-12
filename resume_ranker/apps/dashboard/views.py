from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

from apps.jobs.models import JobDescription
from apps.resumes.models import Resume
from apps.ranking.models import RankingBatch, RankingResult
from apps.ranking.tasks import run_batch_ranking
from .forms import RankUploadForm


@login_required
def home(request):
    return redirect("dashboard:upload")


@login_required
def upload_and_rank(request):
    if request.method == "POST":
        form = RankUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            job = form.cleaned_data["job"]

            if (not request.user.is_superuser) and job.created_by_id != request.user.id:
                return HttpResponseForbidden("You do not have access to this Job Description.")

            files = form.cleaned_data["resumes"]

            resume_ids = []
            for f in files:
                r = Resume.objects.create(
                    uploaded_by=request.user,
                    file=f,
                    original_filename=getattr(f, "name", ""),
                )
                resume_ids.append(r.id)

            batch = RankingBatch.objects.create(created_by=request.user, job=job, status="queued")
            batch.resumes.add(*resume_ids)

            run_batch_ranking.delay(batch.id)

            messages.success(request, f"Uploaded {len(files)} resume(s). Ranking started.")
            return redirect("dashboard:results", batch_id=batch.id)

    else:
        form = RankUploadForm(user=request.user)

    return render(request, "dashboard/upload.html", {"form": form})


@login_required
def results(request, batch_id: int):
    batch = get_object_or_404(RankingBatch, id=batch_id, created_by=request.user)
    qs = batch.results.select_related("resume").order_by("-score", "id")
    return render(request, "dashboard/results.html", {"batch": batch, "results": qs})


@login_required
def result_detail(request, result_id: int):
    result = get_object_or_404(
        RankingResult.objects.select_related("job", "resume", "batch"),
        id=result_id,
        batch__created_by=request.user,
    )
    return render(request, "dashboard/result_detail.html", {"r": result})
