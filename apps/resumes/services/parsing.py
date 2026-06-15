import re
from datetime import date

SKILL_KEYWORDS = [
    "python","django","flask","fastapi","rest","api","celery","redis","postgresql","mysql","sqlite","mongodb",
    "docker","kubernetes","aws","gcp","azure",
    "javascript","typescript","react","angular","vue","html","css","bootstrap","tailwind",
    "pandas","numpy","scikit-learn","tensorflow","pytorch","power bi","tableau","excel",
    "pytest","unittest","selenium","postman","git","github","linux",
]

CATEGORY_RULES = {
    "Backend": ["django","flask","fastapi","rest","api","postgresql","mysql","redis","celery"],
    "Frontend": ["react","angular","vue","javascript","typescript","html","css","bootstrap","tailwind"],
    "Cloud/DevOps": ["aws","gcp","azure","docker","kubernetes","ci/cd","jenkins","github actions","terraform"],
    "Data/Analytics": ["power bi","tableau","pandas","numpy","excel","analytics","dashboard","sql"],
    "AI/ML": ["machine learning","deep learning","tensorflow","pytorch","scikit-learn","nlp","computer vision"],
    "Testing/QA": ["selenium","postman","pytest","qa","test case","jira"],
    "Mobile": ["android","kotlin","flutter","dart","firebase"],
}

MONTHS = {"jan":1,"january":1,"feb":2,"february":2,"mar":3,"march":3,"apr":4,"april":4,"may":5,"jun":6,"june":6,
          "jul":7,"july":7,"aug":8,"august":8,"sep":9,"sept":9,"september":9,"oct":10,"october":10,"nov":11,"november":11,"dec":12,"december":12}

def _norm(s: str) -> str:
    return re.sub(r"\s+"," ",(s or "").strip().lower())

def extract_skills(text: str) -> list[str]:
    t = _norm(text)
    found = []
    for kw in SKILL_KEYWORDS:
        if _norm(kw) in t:
            found.append(kw)
    uniq, seen = [], set()
    for s in found:
        k = _norm(s)
        if k not in seen:
            uniq.append(s.title() if s.islower() else s)
            seen.add(k)
    return uniq

SECTION_START = re.compile(r"^(work\s+experience|experience|employment|professional\s+experience)\b", re.I)
SECTION_END = re.compile(r"^(education|projects?|skills?|certifications?|summary|profile|achievements?)\b", re.I)

DATE_RANGE_RE = re.compile(
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|"
    r"january|february|march|april|june|july|august|september|october|november|december)\s+\d{4}|\d{4})"
    r"\s*(?:-|–|to)\s*"
    r"(present|current|"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|"
    r"january|february|march|april|june|july|august|september|october|november|december)\s+\d{4}|\d{4})",
    re.I
)

def _exp_lines(text: str) -> list[str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    in_exp = False
    out = []
    for ln in lines:
        if SECTION_START.search(ln):
            in_exp = True
            continue
        if in_exp and SECTION_END.search(ln):
            break
        if in_exp:
            out.append(ln)
    return out

def _parse_my(tok: str):
    tok = _norm(tok)
    if re.fullmatch(r"\d{4}", tok):
        return (int(tok), 1)
    m = re.fullmatch(r"([a-z]+)\s+(\d{4})", tok)
    if not m:
        return None
    mon = MONTHS.get(m.group(1))
    if not mon:
        return None
    return (int(m.group(2)), mon)

def _mi(y,m): return y*12+(m-1)

def estimate_total_years_experience(text: str):
    raw = (text or "").strip()
    low = raw.lower()

    says_fresher = any(k in low for k in ["fresher","entry level","recent graduate","seeking entry-level"])

    explicit = re.findall(r"total\s+experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:years|yrs)\b", low)
    if explicit:
        return max(float(x) for x in explicit)

    lines = _exp_lines(raw)
    if not lines:
        return 0.0 if says_fresher else None

    today = date.today()
    month_set = set()
    for ln in lines:
        for start, end in DATE_RANGE_RE.findall(ln):
            s = _parse_my(start)
            if not s: continue
            if end.lower() in ("present","current"):
                e = (today.year, today.month)
            else:
                e = _parse_my(end)
                if not e: continue
            s_i = _mi(s[0], s[1])
            e_i = _mi(e[0], e[1])
            if e_i <= s_i: continue
            if (e_i - s_i) > 12*50: continue
            for i in range(s_i, e_i):
                month_set.add(i)

    if not month_set:
        return 0.0 if says_fresher else None
    return round(len(month_set)/12.0, 1)

def extract_project_categories(text: str, skills: list[str]) -> list[str]:
    signals = _norm(text) + " " + " ".join(_norm(s) for s in (skills or []))
    cats = []
    for cat, keys in CATEGORY_RULES.items():
        if any(_norm(k) in signals for k in keys):
            cats.append(cat)
    return sorted(set(cats))

def parse_resume_heuristic(text: str) -> dict:
    skills = extract_skills(text)
    years = estimate_total_years_experience(text)
    cats = extract_project_categories(text, skills)
    return {"skills": skills, "total_years_experience": years, "project_categories": cats}
