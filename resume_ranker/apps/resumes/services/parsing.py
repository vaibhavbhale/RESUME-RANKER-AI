import re
from datetime import date

# ---------- Skill keywords (lightweight heuristic) ----------
SKILL_KEYWORDS = [
    # Backend
    "python", "django", "flask", "fastapi", "rest", "api", "graphql",
    "celery", "redis", "postgresql", "mysql", "sqlite", "mongodb",
    "docker", "kubernetes", "aws", "gcp", "azure",
    # Frontend
    "javascript", "typescript", "react", "angular", "vue", "html", "css",
    "bootstrap", "tailwind",
    # Data/AI
    "pandas", "numpy", "scikit-learn", "sklearn", "tensorflow", "pytorch",
    "power bi", "tableau", "excel", "nlp", "computer vision",
    # Testing / tools
    "pytest", "unittest", "selenium", "postman",
    "git", "github", "linux",
]

CATEGORY_RULES = {
    "Backend": ["django", "flask", "fastapi", "rest", "api", "postgresql", "mysql", "redis", "celery"],
    "Frontend": ["react", "angular", "vue", "javascript", "typescript", "html", "css", "bootstrap", "tailwind"],
    "Cloud/DevOps": ["aws", "gcp", "azure", "docker", "kubernetes", "ci/cd", "jenkins", "github actions", "terraform"],
    "Data/Analytics": ["power bi", "tableau", "pandas", "numpy", "excel", "analytics", "dashboard", "sql"],
    "AI/ML": ["machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn", "nlp", "computer vision"],
    "Testing/QA": ["selenium", "postman", "pytest", "qa", "test case", "jira"],
    "Mobile": ["android", "kotlin", "flutter", "dart", "firebase"],
    "Cybersecurity": ["kali", "siem", "firewall", "pentest", "vulnerability", "ethical hacking"],
}

MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def extract_skills(text: str) -> list[str]:
    t = _normalize(text)
    found = []
    for kw in SKILL_KEYWORDS:
        if _normalize(kw) in t:
            found.append(kw)

    # de-dup while keeping order
    uniq, seen = [], set()
    for s in found:
        key = _normalize(s)
        if key not in seen:
            uniq.append(s.title() if s.islower() else s)
            seen.add(key)
    return uniq


def extract_project_categories(text: str, skills: list[str]) -> list[str]:
    signals = _normalize(text) + " " + " ".join(_normalize(s) for s in (skills or []))
    cats = []
    for cat, keys in CATEGORY_RULES.items():
        if any(_normalize(k) in signals for k in keys):
            cats.append(cat)
    return sorted(set(cats))


# ---------------- Experience Estimation (FIXED) ----------------

SECTION_START = re.compile(r"^(work\s+experience|experience|employment|professional\s+experience)\b", re.I)
SECTION_END = re.compile(r"^(education|projects?|skills?|certifications?|achievements?|summary|profile)\b", re.I)

DATE_RANGE_RE = re.compile(
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|"
    r"january|february|march|april|june|july|august|september|october|november|december)\s+\d{4}|\d{4})"
    r"\s*(?:-|–|to)\s*"
    r"(present|current|"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|"
    r"january|february|march|april|june|july|august|september|october|november|december)\s+\d{4}|\d{4})",
    re.I
)


def _extract_experience_section_lines(text: str) -> list[str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    in_exp = False
    exp_lines = []

    for ln in lines:
        if SECTION_START.search(ln):
            in_exp = True
            continue
        if in_exp and SECTION_END.search(ln):
            break
        if in_exp:
            exp_lines.append(ln)

    return exp_lines


def _parse_month_year(token: str) -> tuple[int, int] | None:
    """
    Accepts: 'Jan 2022', 'January 2022', '2022'
    Returns: (year, month)
    """
    tok = _normalize(token)
    if re.fullmatch(r"\d{4}", tok):
        return int(tok), 1

    m = re.fullmatch(r"([a-z]+)\s+(\d{4})", tok)
    if not m:
        return None
    mon = MONTHS.get(m.group(1))
    if not mon:
        return None
    return int(m.group(2)), mon


def _month_index(y: int, m: int) -> int:
    return y * 12 + (m - 1)


def estimate_total_years_experience(text: str) -> float | None:
    """
    Stronger heuristic to avoid wrong experience for freshers:
    1) Accept ONLY "Total Experience: X years" (strict).
    2) Else compute from date ranges ONLY inside Experience/Employment section.
    3) If no experience section and resume says "fresher" => return 0.0
    """
    raw = (text or "").strip()
    low = raw.lower()

    # If resume explicitly says fresher (common)
    says_fresher = any(k in low for k in ["fresher", "entry level", "recent graduate", "seeking entry-level"])

    # (1) Strict explicit total experience
    explicit = re.findall(
        r"total\s+experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:years|yrs)\b",
        low
    )
    if explicit:
        return max(float(x) for x in explicit)

    # (2) Only look at Experience section for date ranges
    exp_lines = _extract_experience_section_lines(raw)
    if not exp_lines:
        return 0.0 if says_fresher else None

    today = date.today()
    month_set: set[int] = set()

    for ln in exp_lines:
        for start, end in DATE_RANGE_RE.findall(ln):
            s = _parse_month_year(start)
            if not s:
                continue

            if end.lower() in ("present", "current"):
                e = (today.year, today.month)
            else:
                e = _parse_month_year(end)
                if not e:
                    continue

            s_i = _month_index(s[0], s[1])
            e_i = _month_index(e[0], e[1])

            # sanity checks
            if e_i <= s_i:
                continue
            if (e_i - s_i) > 12 * 50:
                continue

            # union months so overlaps don't double count
            for mi in range(s_i, e_i):
                month_set.add(mi)

    if not month_set:
        return 0.0 if says_fresher else None

    return round(len(month_set) / 12.0, 1)


def parse_resume_heuristic(text: str) -> dict:
    skills = extract_skills(text)
    years = estimate_total_years_experience(text)
    categories = extract_project_categories(text, skills)

    return {
        "skills": skills,
        "total_years_experience": years,
        "project_categories": categories,
        # extend later:
        "education": [],
        "certifications": [],
        "projects": [],
    }