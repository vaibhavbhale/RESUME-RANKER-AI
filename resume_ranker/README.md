# Resume Ranking AI (Django + OpenAI)

## Features
- Login (username/password) using Django Auth
- Create Job Description (Admin or dashboard)
- Upload multiple resumes (PDF/DOCX)
- Rank resumes (0–100), store results in DB
- Extract: Skills, Total Experience, Project Categories
- Strengths + Suggestions (OpenAI when enabled; heuristic fallback otherwise)
- Dashboard: ranked results table + detail page

## Setup (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

copy .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Login:
- /accounts/login/
Ranking page:
- /rank/

## Enable OpenAI suggestions
Edit `.env`:
```env
USE_OPENAI=True
OPENAI_API_KEY=sk-...
```
Restart server and run a NEW ranking batch.
