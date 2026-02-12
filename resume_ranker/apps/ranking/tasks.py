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


def _normalize_set(items) -> set[str]:
    return {str(x).strip().lower() for x in (items or []) if str(x).strip()}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / (len(a | b) or 1)


def _heuristic_suggestions(missing: list[str], job_title: str, categories: list[str]) -> list[str]:
    tips = []
    if missing:
        tips.append("Add evidence for missing skills: " + ", ".join(missing[:8]) + ("..." if len(missing) > 8 else ""))

    tips += [
        f"Tailor your resume summary to the '{job_title}' role using the same JD keywords.",
        "Quantify impact in projects/experience (e.g., latency reduced 30%, served 10k users/day).",
        "Add 2–4 relevant projects with tech stack + outcome + GitHub link.",
        "Move the most relevant skills/projects to page 1.",
        "Use consistent formatting and short bullets (1–2 lines) for readability.",
    ]

    if "Backend" in categories:
        tips.append("Highlight backend depth: REST APIs, auth (JWT/OAuth), DB schema/indexing, caching, testing.")
    if "Cloud/DevOps" in categories:
        tips.append("Add deployment details: Docker, CI/CD, cloud services used, monitoring/logging.")
    if "Data/Analytics" in categories or "AI/ML" in categories:
        tips.append("Mention datasets, metrics, evaluation approach, and any deployment/inference details.")

    return tips[:10]


def _openai_explain_and_suggest(*, job_text: str, resume_text: str, score: int, missing: list[str]) -> dict:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    model = getattr(settings, "OPENAI_CHAT_MODEL", "gpt-4.1-mini")

    system = (
        "You are an expert technical recruiter and resume reviewer. "
        "Return ONLY valid JSON. No markdown. No extra keys."
    )

    user = f"""
Given the JOB DESCRIPTION and RESUME TEXT, produce:
- reasoning: short paragraph explaining the match score
- strengths: 3-7 bullets (with evidence from resume)
- candidate_suggestions: 6-10 actionable improvements to better match the JD

Return JSON:
{{
  "reasoning": "...",
  "strengths": ["..."],
  "candidate_suggestions": ["..."]
}}

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

    content = resp.choices[0].message.content or "{}"
    data = json.loads(content)
    return {
        "reasoning": data.get("reasoning", ""),
        "strengths": data.get("strengths", []) or [],
        "candidate_suggestions": data.get("candidate_suggestions", []) or [],
        "model_meta": {"model": model},
    }


@shared_task(bind=True)
def run_batch_ranking(self, batch_id: int):
    batch = (
        RankingBatch.objects
        .select_related("job")
        .prefetch_related("resumes")
        .get(id=batch_id)
    )

    batch.status = "running"
    batch.save(update_fields=["status"])

    job = batch.job
    job_title = job.title or "Job"
    job_text = job.raw_text or ""

    jd_struct = parse_resume_heuristic(job_text)
    jd_skills = _normalize_set(jd_struct.get("skills", []))

    use_openai = bool(getattr(settings, "USE_OPENAI", False)) and bool(getattr(settings, "OPENAI_API_KEY", "")) \
        and settings.OPENAI_API_KEY != "your-openai-api-key"

    for resume in batch.resumes.all():
        try:
            if not resume.extracted_text:
                resume.status = "extracting"
                resume.save(update_fields=["status"])
                resume.extracted_text = extract_text(resume)
                resume.save(update_fields=["extracted_text"])

            needs_parse = (
                not resume.extracted
                or "skills" not in resume.extracted
                or "project_categories" not in resume.extracted
                or "total_years_experience" not in resume.extracted
            )
            if needs_parse:
                resume.extracted = parse_resume_heuristic(resume.extracted_text)
                resume.status = "parsed"
                resume.save(update_fields=["extracted", "status"])

            res_skills = _normalize_set(resume.extracted.get("skills", []))
            matched = sorted(jd_skills & res_skills)
            missing = sorted(jd_skills - res_skills)

            overlap = _jaccard(jd_skills, res_skills)
            score = int(round(overlap * 100))

            categories = resume.extracted.get("project_categories", []) or []
            exp_years = resume.extracted.get("total_years_experience", None)

            reasoning = "Score computed using skill overlap between job description keywords and extracted resume skills."
            strengths = []
            suggestions = _heuristic_suggestions(missing, job_title, categories)
            model_meta = {"mode": "heuristic_with_optional_openai", "matched_skills": matched[:12]}

            if use_openai:
                try:
                    ai = _openai_explain_and_suggest(
                        job_text=job_text,
                        resume_text=resume.extracted_text,
                        score=score,
                        missing=missing,
                    )
                    if ai.get("reasoning"):
                        reasoning = ai["reasoning"]
                    strengths = ai.get("strengths", []) or strengths
                    suggestions = ai.get("candidate_suggestions", []) or suggestions
                    model_meta.update(ai.get("model_meta", {}))
                except (AuthenticationError,) as e:
                    model_meta["openai_error"] = f"auth_error: {str(e)}"
                except (RateLimitError, APIConnectionError) as e:
                    model_meta["openai_error"] = f"temporary_error: {str(e)}"
                except Exception as e:
                    model_meta["openai_error"] = f"other_error: {str(e)}"

            if exp_years is not None and strengths:
                strengths.append(f"Estimated experience: ~{exp_years} years")

            RankingResult.objects.update_or_create(
                batch=batch,
                job=job,
                resume=resume,
                defaults={
                    "score": score,
                    "score_breakdown": {
                        "skill_overlap": overlap,
                        "matched_skills_count": len(matched),
                        "missing_skills_count": len(missing),
                    },
                    "reasoning": reasoning,
                    "missing_required": missing,
                    "strengths": strengths,
                    "candidate_suggestions": suggestions,
                    "model_meta": model_meta,
                },
            )

        except Exception as e:
            resume.status = "failed"
            resume.error_message = str(e)
            resume.save(update_fields=["status", "error_message"])

    batch.status = "completed"
    batch.completed_at = timezone.now()
    batch.save(update_fields=["status", "completed_at"])
