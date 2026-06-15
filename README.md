# Resume Ranker AI 🚀
Django + OpenAI powered resume ranking system.

## Features
- Login (username/password)
- Seed Job Descriptions (Fresher + Experienced variants)
- Upload multiple resumes (PDF/DOCX)
- Extract text, parse skills/experience/categories
- Score 0–100 with fresher/experienced-aware scoring
- Ranked results + detail view
- OpenAI reasoning & suggestions (optional)

## Run
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_jds --username admin --overwrite
python manage.py runserver
```
