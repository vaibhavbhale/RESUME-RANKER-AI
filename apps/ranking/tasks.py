from __future__ import annotations

import json

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from openai import OpenAI
from openai import AuthenticationError, RateLimitError, APIConnectionError

from apps.ranking.models import RankingBatch, RankingResult
from apps.resumes.services.extraction import extract_text
from apps.resumes.services.parsing import parse_resume_heuristic


def _norm_set(items) -> set[str]:
    return {str(x).strip().lower() for x in (items or []) if str(x).strip()}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / (len(a | b) or 1)


def _infer_years_required(title: str) -> int | None:
    t = (title or "").lower()
    if "fresher" in t or "entry" in t:
        return 0
    if "experienced" in t or "mid" in t or "senior" in t:
        return 2
    return None


def _experience_fit(job_years_required: int | None, resume_years: float | None) -> float:
    """
    0..1 experience fit score.
    Fresher JD (0 years): fresher is best; highly experienced is slightly penalized (overqualified).
    Experienced JD (>=2): below requirement gets proportional score; meeting/exceeding gets 1.0.
    """
    ry = 0.0 if resume_years is None else float(resume_years)

    if job_years_required is None:
        return 0.7  # neutral

    jy = int(job_years_required)

    # Fresher job
    if jy <= 0:
        if ry <= 1.0:
            return 1.0
        if ry <= 2.0:
            return 0.7
        if ry <= 4.0:
            return 0.4
        return 0.2

    # Experienced job
    if ry >= jy:
        return 1.0
    return max(0.0, min(1.0, ry / float(jy)))


def _score(job_skills: set[str], res_skills: set[str], job_years_required: int | None, res_years: float | None):
    overlap = _jaccard(job_skills, res_skills)         # 0..1
    expfit = _experience_fit(job_years_required, res_years)  # 0..1
    final01 = 0.70 * overlap + 0.30 * expfit
    score = int(round(final01 * 100))

    breakdown = {
        "skill_overlap": round(overlap, 4),
        "experience_fit": round(expfit, 4),
        "job_years_required": job_years_required,
        "resume_years": res_years,
        "weights": {"skills": 0.70, "experience": 0.30},
    }
    return score, breakdown


def _openai_suggest(job_text: str, resume_text: str, score: int, missing: list[str]) -> dict:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    model = getattr(settings, "OPENAI_CHAT_MODEL", "gpt-4.1-mini")

    system = "You are an expert recruiter. Return ONLY JSON."
    user = f"""Return JSON:
{{"reasoning":"...", "strengths":["..."], "candidate_suggestions":["..."]}}

match_score: {score}
missing_skills: {missing}

JOB DESCRIPTION:
<<<{job_text[:8000]}>>>

RESUME TEXT:
<<<{resume_text[:8000]}>>>
""".strip()

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    data = json.loads(resp.choices[0].message.content or "{}")
    return {
        "reasoning": data.get("reasoning", ""),
        "strengths": data.get("strengths", []) or [],
        "candidate_suggestions": data.get("candidate_suggestions", []) or [],
        "model_meta": {"model": model},
    }


@shared_task(bind=True)
def run_batch_ranking(self, batch_id: int):
    batch = RankingBatch.objects.select_related("job").prefetch_related("resumes").get(id=batch_id)
    batch.status = "running"
    batch.save(update_fields=["status"])

    job = batch.job
    job_text = job.raw_text or ""
    job_title = job.title or "Job"

    # Derive job skills from JD text (heuristic keywords)
    jd_struct = parse_resume_heuristic(job_text)
    job_skills = _norm_set(jd_struct.get("skills", []))

    job_years_required = None
    if isinstance(job.extracted, dict):
        job_skills |= _norm_set(job.extracted.get("required_skills", []))
        job_skills |= _norm_set(job.extracted.get("preferred_skills", []))
        job_years_required = job.extracted.get("years_required", None)

    if job_years_required is None:
        job_years_required = _infer_years_required(job_title)

    use_openai = (
        bool(getattr(settings, "USE_OPENAI", False))
        and bool(getattr(settings, "OPENAI_API_KEY", ""))
        and settings.OPENAI_API_KEY != "your-openai-api-key"
    )

    for resume in batch.resumes.all():
        try:
            if not resume.extracted_text:
                resume.status = "extracting"
                resume.save(update_fields=["status"])
                resume.extracted_text = extract_text(resume)
                resume.save(update_fields=["extracted_text"])

            # Always parse/refresh extracted so experience stays correct
            resume.extracted = parse_resume_heuristic(resume.extracted_text)
            resume.status = "parsed"
            resume.save(update_fields=["extracted", "status"])

            res_skills = _norm_set(resume.extracted.get("skills", []))
            res_years = resume.extracted.get("total_years_experience", None)

            matched = sorted(list(job_skills & res_skills))
            missing = sorted(list(job_skills - res_skills))

            score, breakdown = _score(job_skills, res_skills, job_years_required, res_years)

            resume_level = "Fresher" if (res_years is None or float(res_years) <= 0.5) else "Experienced"
            job_level = "Fresher" if (job_years_required is not None and int(job_years_required) <= 0) else "Experienced"
            breakdown.update({
                "resume_level": resume_level,
                "job_level": job_level,
                "matched_skills_count": len(matched),
                "missing_skills_count": len(missing),
            })

            reasoning = (
                f"Score based on skill overlap (70%) + experience fit (30%). "
                f"Job level: {job_level}, Resume level: {resume_level}."
            )

            strengths = []
            suggestions = [
                f"Tailor your summary to '{job_title}' keywords.",
                "Quantify impact in projects/experience using numbers.",
                "Add 2–4 relevant projects with GitHub links and tech stack.",
                "Move the most relevant skills/projects to page 1.",
            ]
            model_meta = {"mode": "skills_plus_experience_v1", "use_openai": use_openai, "matched_skills": matched[:12]}

            if use_openai:
                try:
                    ai = _openai_suggest(job_text, resume.extracted_text, score, missing)
                    if ai.get("reasoning"):
                        reasoning = ai["reasoning"]
                    strengths = ai.get("strengths", []) or strengths
                    suggestions = ai.get("candidate_suggestions", []) or suggestions
                    model_meta.update(ai.get("model_meta", {}))
                except AuthenticationError as e:
                    model_meta["openai_error"] = f"auth_error: {str(e)}"
                except (RateLimitError, APIConnectionError) as e:
                    model_meta["openai_error"] = f"temporary_error: {str(e)}"
                except Exception as e:
                    model_meta["openai_error"] = f"other_error: {str(e)}"

            RankingResult.objects.update_or_create(
                batch=batch, job=job, resume=resume,
                defaults={
                    "score": score,
                    "score_breakdown": breakdown,
                    "reasoning": reasoning,
                    "missing_required": missing,
                    "strengths": strengths,
                    "candidate_suggestions": suggestions,
                    "model_meta": model_meta,
                }
            )

        except Exception as e:
            resume.status = "failed"
            resume.error_message = str(e)
            resume.save(update_fields=["status", "error_message"])

    batch.status = "completed"
    batch.completed_at = timezone.now()
    batch.save(update_fields=["status", "completed_at"])