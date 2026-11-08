"""Trích xuất & phân nhóm kỹ năng từ CV bằng từ điển kỹ năng (skill taxonomy).

Cách làm: chuẩn hoá văn bản (bỏ dấu, chữ thường) rồi tìm các cụm từ đồng nghĩa
của từng kỹ năng theo ranh giới từ. Kết quả được dùng để:
  * phân nhóm kỹ năng của ứng viên (Ngôn ngữ lập trình, Dữ liệu & BI, ...)
  * đối chiếu với yêu cầu của JD (độ phủ kỹ năng – KHÔNG phải điểm xếp hạng con người)
"""
from __future__ import annotations

import re
from collections import Counter
from functools import lru_cache

from app.utils import normalize_key

SKILL_TAXONOMY: dict[str, dict[str, list[str]]] = {
    "Ngôn ngữ lập trình": {
        "Python": ["python", "python3"],
        "Java": ["java"],
        "JavaScript": ["javascript", "js", "es6"],
        "TypeScript": ["typescript", "ts"],
        "C#": ["c#", "csharp", ".net", "dotnet", "asp net"],
        "C++": ["c++", "cpp"],
        "PHP": ["php", "laravel"],
        "Go": ["golang"],
        "R": ["r language", "ngon ngu r", "rstudio"],
    },
    "Dữ liệu & BI": {
        "SQL": ["sql", "t sql", "pl sql", "truy van sql"],
        "Excel": ["excel", "ms excel", "microsoft excel", "pivot table", "vlookup"],
        "Power BI": ["power bi", "powerbi", "dax"],
        "Tableau": ["tableau"],
        "Looker Studio": ["looker", "looker studio", "google data studio", "data studio"],
        "Pandas": ["pandas"],
        "NumPy": ["numpy"],
        "Thống kê": ["thong ke", "statistics", "statistical", "xac suat thong ke", "kiem dinh gia thuyet", "a b testing"],
        "Data Visualization": ["data visualization", "truc quan hoa", "truc quan hoa du lieu", "dashboard"],
    },
    "Kỹ thuật dữ liệu": {
        "ETL": ["etl", "elt", "data pipeline", "pipeline du lieu"],
        "Airflow": ["airflow", "apache airflow"],
        "Spark": ["spark", "pyspark", "apache spark"],
        "Kafka": ["kafka"],
        "Data Warehouse": ["data warehouse", "kho du lieu", "dwh", "star schema", "luoc do hinh sao"],
        "dbt": ["dbt"],
    },
    "AI / Machine Learning": {
        "Machine Learning": ["machine learning", "hoc may", "ml"],
        "Deep Learning": ["deep learning", "hoc sau", "neural network", "mang no ron"],
        "NLP": ["nlp", "xu ly ngon ngu tu nhien", "natural language processing", "text classification"],
        "Computer Vision": ["computer vision", "thi giac may tinh", "opencv", "yolo"],
        "PyTorch": ["pytorch", "torch"],
        "TensorFlow": ["tensorflow", "keras"],
        "Scikit-learn": ["scikit learn", "sklearn"],
        "LLM": ["llm", "large language model", "chatgpt", "generative ai", "genai", "rag", "prompt engineering"],
        "MLOps": ["mlops", "mlflow", "kubeflow"],
    },
    "Web & Backend": {
        "FastAPI": ["fastapi", "fast api"],
        "Django": ["django"],
        "Flask": ["flask"],
        "Node.js": ["nodejs", "node js", "expressjs", "express js"],
        "Spring Boot": ["spring boot", "spring"],
        "REST API": ["rest api", "restful", "restful api", "api rest"],
        "Microservices": ["microservices", "microservice"],
    },
    "Frontend & UI": {
        "ReactJS": ["react", "reactjs", "react js", "redux"],
        "Next.js": ["nextjs", "next js"],
        "Vue.js": ["vue", "vuejs", "vue js"],
        "HTML/CSS": ["html", "css", "html5", "css3", "tailwind", "bootstrap", "sass"],
        "UI/UX": ["ui ux", "ux ui", "user interface", "user experience", "thiet ke giao dien"],
        "Figma": ["figma"],
    },
    "Cơ sở dữ liệu": {
        "PostgreSQL": ["postgresql", "postgres"],
        "MySQL": ["mysql", "mariadb"],
        "MongoDB": ["mongodb", "mongo"],
        "Redis": ["redis"],
        "SQL Server": ["sql server", "mssql"],
        "Oracle": ["oracle"],
    },
    "Cloud & DevOps": {
        "Docker": ["docker", "docker compose"],
        "Kubernetes": ["kubernetes", "k8s"],
        "AWS": ["aws", "amazon web services", "s3", "ec2"],
        "Azure": ["azure"],
        "GCP": ["gcp", "google cloud", "bigquery"],
        "CI/CD": ["ci cd", "github actions", "gitlab ci", "jenkins"],
        "Linux": ["linux", "ubuntu", "bash"],
        "Git": ["git", "github", "gitlab"],
    },
    "Kiểm thử phần mềm": {
        "Manual testing": ["manual test", "manual testing", "kiem thu thu cong", "test thu cong"],
        "Test case": ["test case", "testcase", "kich ban kiem thu", "test plan"],
        "Automation test": ["automation test", "automation testing", "kiem thu tu dong", "auto test", "test tu dong"],
        "Selenium": ["selenium"],
        "Postman": ["postman"],
        "Jira": ["jira"],
    },
    "Nhân sự & Tuyển dụng": {
        "Tuyển dụng": ["tuyen dung", "recruitment", "recruiting", "headhunt", "sourcing ung vien", "talent acquisition"],
        "Phỏng vấn": ["phong van", "interview", "interviewing"],
        "ATS": ["ats", "applicant tracking"],
        "Employer branding": ["employer branding", "thuong hieu tuyen dung"],
        "Onboarding": ["onboarding", "hoi nhap nhan vien"],
    },
    "Kinh doanh & Marketing": {
        "Bán hàng B2B": ["b2b", "ban hang b2b", "nhan vien ban hang", "ky nang ban hang", "sales", "telesales",
                         "tu van khach hang doanh nghiep"],
        "Đàm phán": ["dam phan", "negotiation", "thuong luong"],
        "CRM": ["crm", "salesforce", "hubspot"],
        "SEO": ["seo"],
        "Facebook Ads": ["facebook ads", "fb ads", "meta ads", "quang cao facebook"],
        "Google Ads": ["google ads", "adwords", "quang cao google"],
        "Content Marketing": ["content marketing", "content", "copywriting", "viet bai", "san xuat noi dung"],
        "Google Analytics": ["google analytics", "ga4"],
    },
    "Tài chính – Kế toán": {
        "Kế toán": ["ke toan", "accounting", "hach toan"],
        "MISA": ["misa"],
        "Thuế": ["quyet toan thue", "ke khai thue", "thue tncn", "thue gtgt", "thue tndn", "tax"],
        "Báo cáo tài chính": ["bao cao tai chinh", "financial statement", "bctc", "financial report"],
        "SAP": ["sap erp", "sap fico", "sap b1", "sap s 4hana"],
    },
    "Ngoại ngữ": {
        "Tiếng Anh": ["tieng anh", "english", "ielts", "toeic", "toefl"],
        "Tiếng Nhật": ["tieng nhat", "japanese", "jlpt"],
        "Tiếng Trung": ["tieng trung", "chinese", "hsk"],
    },
    "Kỹ năng mềm": {
        "Giao tiếp": ["giao tiep", "communication"],
        "Làm việc nhóm": ["lam viec nhom", "teamwork", "team work"],
        "Thuyết trình": ["thuyet trinh", "presentation"],
        "Quản lý thời gian": ["quan ly thoi gian", "time management"],
        "Giải quyết vấn đề": ["giai quyet van de", "problem solving", "tu duy phan bien", "critical thinking"],
        "Lãnh đạo": ["lanh dao", "leadership", "quan ly nhom", "team lead", "teamlead"],
    },
}


@lru_cache
def _compiled() -> list[tuple[str, str, re.Pattern]]:
    items = []
    for group, skills in SKILL_TAXONOMY.items():
        for skill, aliases in skills.items():
            keys = sorted({normalize_key(a) for a in aliases} | {normalize_key(skill)}, key=len, reverse=True)
            pattern = re.compile(r"(?<![a-z0-9+#])(?:" + "|".join(re.escape(k) for k in keys if k) + r")(?![a-z0-9+#])")
            items.append((group, skill, pattern))
    return items


def skill_group_of(skill: str) -> str | None:
    for group, skills in SKILL_TAXONOMY.items():
        if skill in skills:
            return group
    return None


def extract_skills(text: str | None) -> list[str]:
    """Trả về danh sách kỹ năng chuẩn, sắp xếp theo số lần xuất hiện."""
    if not text:
        return []
    key = normalize_key(text.replace(".net", " dotnet ").replace("C#", " c# "))
    counts: Counter[str] = Counter()
    for _group, skill, pattern in _compiled():
        hits = len(pattern.findall(key))
        if hits:
            counts[skill] += hits
    return [skill for skill, _ in counts.most_common()]


def group_skills(skills: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for skill in skills:
        group = skill_group_of(skill) or "Khác"
        groups.setdefault(group, []).append(skill)
    return groups


def match_jd(candidate_skills: list[str], required: list[str], nice_to_have: list[str] | None = None) -> dict:
    """Đối chiếu kỹ năng ứng viên với JD → độ phủ yêu cầu (chỉ mang tính tham khảo)."""
    have = set(candidate_skills)
    required = required or []
    nice_to_have = nice_to_have or []
    matched = [s for s in required if s in have]
    missing = [s for s in required if s not in have]
    nice_matched = [s for s in nice_to_have if s in have]
    coverage = round(len(matched) / len(required) * 100) if required else 0
    return {
        "required_coverage_pct": coverage,
        "matched_required": matched,
        "missing_required": missing,
        "matched_nice_to_have": nice_matched,
    }
