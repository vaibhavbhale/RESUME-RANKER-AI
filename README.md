# Resume Ranker AI 🚀  
**Django + OpenAI Powered Resume Ranking System**

Recruiter-focused web app that lets you upload multiple PDF/DOCX resumes, select or paste a job description, and generate a ranked shortlist with a **0–100 match score**, extracted insights, and explainable AI feedback.

---

## 🔹 Key Features

- 📂 **Multi-resume upload** (PDF/DOCX)  
- 📝 **Job Description management** (supports *Fresher* & *Experienced* variants)  
- 🧠 **Automated text extraction & structured parsing**
  - Skills  
  - Total Experience (fresher-safe detection)  
  - Project Categories (Backend / Frontend / Data / DevOps, etc.)
- 📊 **Resume–JD match scoring (0–100)** with **score breakdown**
- ✅ **Missing-skill insights** to highlight gaps vs JD requirements  
- 🏆 **Ranked results dashboard** (sorted by score)
- 🔎 **Detailed candidate analysis page**
  - Match reasoning, strengths, suggestions
  - Skills & categories shown as tags/chips
- 🤖 **OpenAI-powered reasoning & resume improvement suggestions** *(optional toggle via `.env`)*
- 💾 **SQLite** for development

---

## 🔐 Demo Login (Local)
**Username:** `admin`  
**Password:** `admin@12345`  
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



> Note: Demo credentials are for local testing only. In production, use your own accounts and secure secrets via environment variables.
