from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from apps.jobs.models import JobDescription


def format_jd(title: str, exp: str, required: list[str], preferred: list[str], responsibilities: list[str]) -> str:
    req = "\n".join(f"- {x}" for x in required) if required else "- (Not specified)"
    pref = "\n".join(f"- {x}" for x in preferred) if preferred else "- (Not specified)"
    resp = "\n".join(f"- {x}" for x in responsibilities) if responsibilities else "- (Not specified)"

    return f"""Role: {title}
Experience: {exp}

Skills Required:
{req}

Preferred Skills:
{pref}

Responsibilities:
{resp}
""".strip()


# Base specs per role (you can extend/modify anytime)
ROLE_SPECS = [
    {
        "base": "Python Developer",
        "required": [
            "Python (OOP, Exception Handling)",
            "Django / Flask / FastAPI",
            "REST APIs",
            "SQL (MySQL/PostgreSQL/SQLite)",
            "Git & GitHub",
            "Basic Linux",
        ],
        "preferred": ["Docker (basic)", "Unit testing (unittest/pytest)"],
        "responsibilities": [
            "Build backend modules and REST APIs",
            "Optimize SQL queries",
            "Collaborate using Git",
        ],
        "experienced_add": ["Django REST Framework (DRF)", "Database indexing & optimization", "Deployment basics"],
        "years_required_exp": 2,
    },
    {
        "base": "Frontend Developer",
        "required": ["HTML", "CSS", "JavaScript", "React / Angular / Vue", "Responsive Design", "API Integration", "Git"],
        "preferred": ["TypeScript (basic)", "Testing (Jest)"],
        "responsibilities": ["Build UI components", "Integrate with APIs", "Fix UI bugs"],
        "experienced_add": ["State management (Redux/Context)", "Performance optimization", "Accessibility (a11y) basics"],
        "years_required_exp": 2,
    },
    {
        "base": "Full Stack Developer",
        "required": ["Frontend + Backend", "Django / Node.js", "SQL / NoSQL", "REST APIs", "Deployment (AWS/Render)", "Git"],
        "preferred": ["Docker", "CI/CD basics"],
        "responsibilities": ["Deliver end-to-end features", "Deploy and maintain apps", "Improve performance"],
        "experienced_add": ["Authentication (JWT/OAuth)", "API versioning/pagination", "System design basics"],
        "years_required_exp": 2,
    },
    {
        "base": "Java Developer",
        "required": ["Core Java", "Spring Boot", "Hibernate", "REST APIs", "SQL"],
        "preferred": ["Microservices basics"],
        "responsibilities": ["Build Spring Boot APIs", "Work with Hibernate/JPA", "Write tests"],
        "experienced_add": ["Performance tuning", "REST API design best practices", "Maven/Gradle"],
        "years_required_exp": 2,
    },
    {
        "base": "Data Analyst",
        "required": ["Python / R", "Pandas, NumPy", "SQL", "Excel", "Power BI / Tableau", "Statistics"],
        "preferred": ["ETL basics"],
        "responsibilities": ["Build dashboards/reports", "Analyze data with SQL", "Present insights"],
        "experienced_add": ["Advanced SQL (window functions)", "KPI definition", "Dashboard optimization"],
        "years_required_exp": 2,
    },
    {
        "base": "Data Scientist",
        "required": [
            "Python",
            "Machine Learning (Scikit-learn)",
            "Deep Learning (TensorFlow / PyTorch)",
            "Data Cleaning & Preprocessing",
            "Statistics & Probability",
            "Feature Engineering",
            "Model Evaluation",
        ],
        "preferred": ["NLP / Computer Vision (Optional)"],
        "responsibilities": ["Train and evaluate models", "Experiment and tune features", "Communicate results"],
        "experienced_add": ["Hyperparameter tuning", "Experiment tracking (MLflow/W&B)"],
        "years_required_exp": 2,
    },
    {
        "base": "AI / ML Engineer",
        "required": [
            "Python",
            "Machine Learning Algorithms",
            "Model Deployment (FastAPI / Django)",
            "Docker",
            "Cloud (AWS / GCP / Azure)",
            "REST APIs",
            "CI/CD for ML",
            "Model Monitoring",
        ],
        "preferred": ["Kubernetes basics"],
        "responsibilities": ["Deploy models as APIs", "Monitor performance", "Automate ML delivery"],
        "experienced_add": ["Latency optimization", "Drift monitoring", "Production troubleshooting"],
        "years_required_exp": 2,
    },
    {
        "base": "Android Developer",
        "required": ["Java / Kotlin", "Android Studio", "Firebase", "REST APIs", "MVVM Architecture", "SQLite / Room DB"],
        "preferred": ["Unit/UI testing basics"],
        "responsibilities": ["Build Android features", "Integrate APIs", "Maintain releases"],
        "experienced_add": ["Performance optimization", "Release management", "Crash monitoring (Firebase Crashlytics)"],
        "years_required_exp": 2,
    },
    {
        "base": "Flutter Developer",
        "required": ["Dart", "Flutter Framework", "API Integration", "Firebase", "State Management (Provider / Bloc)", "App Deployment (Play Store)"],
        "preferred": ["iOS build knowledge (optional)"],
        "responsibilities": ["Build cross-platform apps", "Integrate APIs", "Ship releases"],
        "experienced_add": ["App performance tuning", "Offline caching", "Release automation basics"],
        "years_required_exp": 2,
    },
    {
        "base": "DevOps Engineer",
        "required": ["Linux", "Docker", "Kubernetes", "CI/CD (Jenkins / GitHub Actions)", "AWS / Azure / GCP", "Git", "Monitoring (Prometheus/Grafana)"],
        "preferred": ["Terraform (IaC)"],
        "responsibilities": ["Automate deployments", "Manage infra", "Improve reliability/monitoring"],
        "experienced_add": ["Incident response", "Security best practices", "Cost optimization"],
        "years_required_exp": 2,
    },
    {
        "base": "Cloud Engineer",
        "required": ["AWS / Azure / GCP", "Networking Basics", "Linux", "Cloud Security", "Infrastructure as Code (Terraform)", "Deployment & Scaling"],
        "preferred": ["Kubernetes basics"],
        "responsibilities": ["Manage cloud infra", "Secure IAM/network", "Scale deployments"],
        "experienced_add": ["VPC/VNet design", "IAM best practices", "Autoscaling/load balancing"],
        "years_required_exp": 2,
    },
    {
        "base": "QA Engineer",
        "required": ["Manual Testing", "Test Case Writing", "Selenium (Automation Testing)", "API Testing (Postman)", "Basic SQL", "Bug Tracking (JIRA)"],
        "preferred": ["Performance testing basics"],
        "responsibilities": ["Write test cases", "Automate regression", "Report and verify bugs"],
        "experienced_add": ["Framework design", "CI integration for tests", "Test strategy"],
        "years_required_exp": 2,
    },
    {
        "base": "Cybersecurity Analyst",
        "required": ["Networking Fundamentals", "Ethical Hacking Basics", "Kali Linux", "Firewalls", "SIEM Tools", "Vulnerability Assessment", "Security Monitoring"],
        "preferred": ["Cloud security basics"],
        "responsibilities": ["Monitor alerts", "Assist incident response", "Run vulnerability scans"],
        "experienced_add": ["Incident response workflows", "Threat hunting basics", "SIEM tuning"],
        "years_required_exp": 2,
    },
    {
        "base": "System Administrator",
        "required": ["Linux / Windows Server", "Networking", "Troubleshooting", "Hardware Knowledge", "Backup & Recovery", "Server Maintenance"],
        "preferred": ["Scripting (Bash/Python)"],
        "responsibilities": ["Maintain servers", "Handle incidents", "Backups and patching"],
        "experienced_add": ["Automation", "Monitoring tools", "Hardening/security patching"],
        "years_required_exp": 2,
    },
    {
        "base": "Business Analyst",
        "required": ["Requirement Gathering", "Documentation (BRD, SRS)", "SQL", "Communication Skills", "Agile / Scrum", "Stakeholder Management"],
        "preferred": ["Wireframing tools"],
        "responsibilities": ["Gather requirements", "Write user stories", "Support delivery"],
        "experienced_add": ["Backlog ownership", "Acceptance criteria design", "Process improvement"],
        "years_required_exp": 2,
    },
]


class Command(BaseCommand):
    help = "Seed JobDescriptions for Fresher + Experienced variants (30 total). Includes years_required for scoring."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True, help="Owner username for JobDescriptions (created_by)")
        parser.add_argument("--overwrite", action="store_true", help="Overwrite existing titles for this user")

    def handle(self, *args, **opts):
        username = opts["username"]
        overwrite = opts["overwrite"]

        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' not found. Create the user first.")

        created = 0
        updated = 0

        for spec in ROLE_SPECS:
            base = spec["base"]

            # Fresher variant
            fresher_title = f"{base} (Fresher)"
            fresher_required = spec["required"]
            fresher_preferred = spec["preferred"]
            fresher_resp = spec["responsibilities"]

            fresher_raw = format_jd(
                fresher_title,
                "0–1 years (Internship/Projects acceptable)",
                fresher_required,
                fresher_preferred,
                fresher_resp,
            )
            fresher_extracted = {
                "required_skills": fresher_required,
                "preferred_skills": fresher_preferred,
                "experience_level": "junior",
                "years_required": 0,
            }

            obj, is_new = JobDescription.objects.get_or_create(
                created_by=user,
                title=fresher_title,
                defaults={"raw_text": fresher_raw, "extracted": fresher_extracted},
            )
            if is_new:
                created += 1
            elif overwrite:
                obj.raw_text = fresher_raw
                obj.extracted = fresher_extracted
                obj.save(update_fields=["raw_text", "extracted"])
                updated += 1

            # Experienced variant
            exp_title = f"{base} (Experienced)"
            exp_required = spec["required"] + (spec.get("experienced_add") or [])
            exp_preferred = spec["preferred"]
            exp_resp = spec["responsibilities"] + ["Own production fixes and performance improvements"]

            exp_raw = format_jd(
                exp_title,
                f"{spec.get('years_required_exp', 2)}+ years",
                exp_required,
                exp_preferred,
                exp_resp,
            )
            exp_extracted = {
                "required_skills": exp_required,
                "preferred_skills": exp_preferred,
                "experience_level": "mid",
                "years_required": int(spec.get("years_required_exp", 2)),
            }

            obj, is_new = JobDescription.objects.get_or_create(
                created_by=user,
                title=exp_title,
                defaults={"raw_text": exp_raw, "extracted": exp_extracted},
            )
            if is_new:
                created += 1
            elif overwrite:
                obj.raw_text = exp_raw
                obj.extracted = exp_extracted
                obj.save(update_fields=["raw_text", "extracted"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete for '{username}'. Created={created}, Updated={updated}"
        ))