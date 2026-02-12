from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from apps.jobs.models import JobDescription


COMMON_SKILLS = """
Common & Important for All IT Roles:
- Data Structures & Algorithms (basic)
- Git & GitHub
- Communication Skills
- Problem Solving
- SQL Basics
- Understanding of APIs
""".strip()

HIGH_DEMAND_2026 = """
High Demand Roles in 2026:
- AI / ML Engineer
- Data Scientist
- DevOps Engineer
- Cloud Engineer
- Full Stack Developer
- Cybersecurity Analyst
""".strip()


def jd(title: str, required: list[str], preferred: list[str] | None = None, responsibilities: list[str] | None = None) -> str:
    preferred = preferred or []
    responsibilities = responsibilities or []

    req_txt = "\n".join([f"- {x}" for x in required])
    pref_txt = "\n".join([f"- {x}" for x in preferred]) if preferred else "- (Not specified)"
    resp_txt = "\n".join([f"- {x}" for x in responsibilities]) if responsibilities else "- Build features aligned to business requirements\n- Collaborate with team and follow best practices"

    return f"""
Role: {title}

Skills Required:
{req_txt}

Preferred Skills:
{pref_txt}

Responsibilities:
{resp_txt}

{COMMON_SKILLS}

{HIGH_DEMAND_2026}
""".strip()


JOB_TEMPLATES = [
    {
        "title": "Python Developer",
        "raw_text": jd(
            "Python Developer",
            required=[
                "Python (OOP, Exception Handling)",
                "Django / Flask / FastAPI",
                "REST APIs",
                "SQL (MySQL/PostgreSQL/SQLite)",
                "Git & GitHub",
                "Basic Linux",
            ],
            preferred=[
                "Docker basics",
                "Unit testing (pytest/unittest)",
                "Celery / background jobs (optional)",
            ],
            responsibilities=[
                "Develop backend modules, APIs, and integrations",
                "Write clean, reusable, testable code",
                "Work with SQL databases and optimize queries",
            ],
        ),
    },
    {
        "title": "Frontend Developer",
        "raw_text": jd(
            "Frontend Developer",
            required=[
                "HTML, CSS, JavaScript",
                "React / Angular / Vue",
                "Responsive Design",
                "API Integration",
                "Git",
            ],
            preferred=[
                "TypeScript",
                "Bootstrap/Tailwind",
                "Testing (Jest/Cypress)",
            ],
            responsibilities=[
                "Build responsive UI and reusable components",
                "Integrate frontend with REST APIs",
                "Improve performance and user experience",
            ],
        ),
    },
    {
        "title": "Full Stack Developer",
        "raw_text": jd(
            "Full Stack Developer",
            required=[
                "Frontend + Backend",
                "Django / Node.js",
                "SQL / NoSQL",
                "REST APIs",
                "Deployment (AWS/Render)",
                "Git",
            ],
            preferred=[
                "Docker",
                "CI/CD basics",
                "Redis / caching (optional)",
            ],
            responsibilities=[
                "Deliver end-to-end features (UI + API + DB)",
                "Design scalable APIs and data models",
                "Deploy and monitor applications",
            ],
        ),
    },
    {
        "title": "Java Developer",
        "raw_text": jd(
            "Java Developer",
            required=[
                "Core Java",
                "Spring Boot",
                "Hibernate",
                "REST APIs",
                "SQL",
            ],
            preferred=[
                "Microservices basics",
                "Maven/Gradle",
                "Docker basics",
            ],
            responsibilities=[
                "Build REST services using Spring Boot",
                "Implement persistence using Hibernate/JPA",
                "Write unit tests and ensure code quality",
            ],
        ),
    },
    {
        "title": "Data Analyst",
        "raw_text": jd(
            "Data Analyst",
            required=[
                "Python / R",
                "Pandas, NumPy",
                "SQL",
                "Excel",
                "Power BI / Tableau",
                "Statistics",
            ],
            preferred=[
                "ETL basics",
                "KPI design and reporting",
            ],
            responsibilities=[
                "Analyze datasets and generate insights",
                "Build dashboards and recurring reports",
                "Write SQL queries for data extraction",
            ],
        ),
    },
    {
        "title": "Data Scientist",
        "raw_text": jd(
            "Data Scientist",
            required=[
                "Python",
                "Machine Learning (Scikit-learn)",
                "Deep Learning (TensorFlow / PyTorch)",
                "Data Cleaning & Preprocessing",
                "Statistics & Probability",
                "Feature Engineering",
                "Model Evaluation",
                "NLP / Computer Vision (Optional)",
            ],
            preferred=[
                "Experiment tracking (MLflow/W&B)",
                "Deployment exposure (FastAPI/Django)",
            ],
            responsibilities=[
                "Build and evaluate ML/DL models",
                "Perform feature engineering and experiments",
                "Communicate results to stakeholders",
            ],
        ),
    },
    {
        "title": "AI / ML Engineer",
        "raw_text": jd(
            "AI / ML Engineer",
            required=[
                "Python",
                "Machine Learning Algorithms",
                "Model Deployment (FastAPI / Django)",
                "Docker",
                "Cloud (AWS / GCP / Azure)",
                "REST APIs",
                "CI/CD for ML",
                "Model Monitoring",
            ],
            preferred=[
                "Kubernetes basics",
                "Model optimization (latency/cost)",
            ],
            responsibilities=[
                "Deploy ML models as APIs/services",
                "Build CI/CD pipelines for model delivery",
                "Implement monitoring for drift and performance",
            ],
        ),
    },
    {
        "title": "Android Developer",
        "raw_text": jd(
            "Android Developer",
            required=[
                "Java / Kotlin",
                "Android Studio",
                "Firebase",
                "REST APIs",
                "MVVM Architecture",
                "SQLite / Room DB",
            ],
            preferred=[
                "Jetpack components",
                "Unit/UI testing",
            ],
            responsibilities=[
                "Develop Android apps and integrate APIs",
                "Implement MVVM and clean architecture patterns",
                "Publish and maintain app releases",
            ],
        ),
    },
    {
        "title": "Flutter Developer",
        "raw_text": jd(
            "Flutter Developer",
            required=[
                "Dart",
                "Flutter Framework",
                "API Integration",
                "Firebase",
                "State Management (Provider / Bloc)",
                "App Deployment (Play Store)",
            ],
            preferred=[
                "iOS build/deployment exposure",
                "Performance optimization",
            ],
            responsibilities=[
                "Build cross-platform apps using Flutter",
                "Integrate REST APIs and Firebase",
                "Deploy releases and fix production issues",
            ],
        ),
    },
    {
        "title": "DevOps Engineer",
        "raw_text": jd(
            "DevOps Engineer",
            required=[
                "Linux",
                "Docker",
                "Kubernetes",
                "CI/CD (Jenkins / GitHub Actions)",
                "AWS / Azure / GCP",
                "Git",
                "Monitoring (Prometheus/Grafana)",
            ],
            preferred=[
                "Terraform (IaC)",
                "Security best practices",
            ],
            responsibilities=[
                "Build CI/CD pipelines and automate deployments",
                "Manage container infrastructure (Docker/K8s)",
                "Improve monitoring, reliability, and cost",
            ],
        ),
    },
    {
        "title": "Cloud Engineer",
        "raw_text": jd(
            "Cloud Engineer",
            required=[
                "AWS / Azure / GCP",
                "Networking Basics",
                "Linux",
                "Cloud Security",
                "Infrastructure as Code (Terraform)",
                "Deployment & Scaling",
            ],
            preferred=[
                "Kubernetes basics",
                "Observability tooling",
            ],
            responsibilities=[
                "Design and manage cloud infrastructure",
                "Implement IAM/security best practices",
                "Support deployments, scaling, and cost optimization",
            ],
        ),
    },
    {
        "title": "QA Engineer",
        "raw_text": jd(
            "QA Engineer",
            required=[
                "Manual Testing",
                "Test Case Writing",
                "Selenium (Automation Testing)",
                "API Testing (Postman)",
                "Basic SQL",
                "Bug Tracking (JIRA)",
            ],
            preferred=[
                "CI integration for tests",
                "Performance testing basics",
            ],
            responsibilities=[
                "Write and execute test cases",
                "Automate key regression scenarios",
                "Report defects and validate fixes",
            ],
        ),
    },
    {
        "title": "Cybersecurity Analyst",
        "raw_text": jd(
            "Cybersecurity Analyst",
            required=[
                "Networking Fundamentals",
                "Ethical Hacking Basics",
                "Kali Linux",
                "Firewalls",
                "SIEM Tools",
                "Vulnerability Assessment",
                "Security Monitoring",
            ],
            preferred=[
                "SOC workflows and incident response",
                "Cloud security basics",
            ],
            responsibilities=[
                "Monitor SIEM alerts and triage incidents",
                "Assist with vulnerability scanning and remediation",
                "Document findings and improve security posture",
            ],
        ),
    },
    {
        "title": "System Administrator",
        "raw_text": jd(
            "System Administrator",
            required=[
                "Linux / Windows Server",
                "Networking",
                "Troubleshooting",
                "Hardware Knowledge",
                "Backup & Recovery",
                "Server Maintenance",
            ],
            preferred=[
                "Scripting (Bash/Python)",
                "Monitoring tools",
            ],
            responsibilities=[
                "Maintain servers, backups, and user access",
                "Monitor uptime and troubleshoot issues",
                "Patch management and security updates",
            ],
        ),
    },
    {
        "title": "Business Analyst",
        "raw_text": jd(
            "Business Analyst",
            required=[
                "Requirement Gathering",
                "Documentation (BRD, SRS)",
                "SQL",
                "Communication Skills",
                "Agile / Scrum",
                "Stakeholder Management",
            ],
            preferred=[
                "Wireframing tools",
                "Basic analytics/dashboarding",
            ],
            responsibilities=[
                "Gather requirements and write user stories",
                "Coordinate with stakeholders and engineering",
                "Support sprint planning and acceptance criteria",
            ],
        ),
    },
]


class Command(BaseCommand):
    help = "Seed JobDescription records (15 IT roles) for a given username."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True, help="Owner username for JobDescriptions (created_by)")
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="If set, update raw_text if JobDescription with same title already exists.",
        )

    def handle(self, *args, **options):
        username = options["username"]
        overwrite = options["overwrite"]

        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' not found. Create the user first.")

        created, updated = 0, 0
        for item in JOB_TEMPLATES:
            title = item["title"]
            raw_text = item["raw_text"]

            obj, is_new = JobDescription.objects.get_or_create(
                created_by=user,
                title=title,
                defaults={"raw_text": raw_text},
            )
            if is_new:
                created += 1
            elif overwrite and obj.raw_text != raw_text:
                obj.raw_text = raw_text
                obj.save(update_fields=["raw_text"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete for '{username}'. Created={created}, Updated={updated}"
        ))