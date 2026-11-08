"""Dữ liệu tham chiếu (master data) & bảng ánh xạ chuẩn hoá.

Mọi giá trị "bẩn" từ form, email, ATS, Excel đều được ánh xạ về các mã chuẩn ở đây.
"""
from __future__ import annotations

from datetime import date

DEPARTMENTS: list[tuple[str, str]] = [
    ("TECH", "Khối Công nghệ"),
    ("DATA", "Khối Dữ liệu & AI"),
    ("HR", "Phòng Nhân sự"),
    ("SALES", "Phòng Kinh doanh"),
    ("MKT", "Phòng Marketing"),
    ("FIN", "Phòng Tài chính – Kế toán"),
]

# (code, tên hiển thị, kênh, các biến thể thường gặp – so khớp sau khi bỏ dấu)
SOURCES: list[tuple[str, str, str, list[str]]] = [
    ("TOPCV", "TopCV", "job_board", ["topcv", "top cv", "topcv vn", "topcv.vn"]),
    ("VIETNAMWORKS", "VietnamWorks", "job_board", ["vietnamworks", "vietnam works", "vnw", "vietnamwork"]),
    ("ITVIEC", "ITviec", "job_board", ["itviec", "it viec", "itviec com"]),
    ("LINKEDIN", "LinkedIn", "social", ["linkedin", "linked in", "linkedin com", "lnkd"]),
    ("FACEBOOK", "Facebook / Group tuyển dụng", "social",
     ["facebook", "fb", "fb group", "group facebook", "facebook tuyen dung", "nhom facebook"]),
    ("REFERRAL", "Nhân viên giới thiệu", "referral",
     ["referral", "gioi thieu", "nhan vien gioi thieu", "nguoi quen gioi thieu", "ban be gioi thieu", "employee referral"]),
    ("CAREER_SITE", "Website tuyển dụng công ty", "owned",
     ["website", "website cong ty", "career site", "careers page", "trang tuyen dung", "web cong ty"]),
    ("JOB_FAIR", "Ngày hội việc làm", "event", ["job fair", "ngay hoi viec lam", "hoi cho viec lam", "career fair"]),
    ("DIRECT_EMAIL", "Email ứng tuyển trực tiếp", "direct", ["email", "email truc tiep", "gui mail", "direct email"]),
    ("OTHER", "Nguồn khác", "other", ["khac", "other", "unknown"]),
]

# (code, tên, thứ tự, SLA ngày, là vòng kết thúc, biến thể)
STAGES: list[tuple[str, str, int, int, bool, list[str]]] = [
    ("APPLIED", "Nộp hồ sơ", 1, 2, False, ["applied", "nop ho so", "new", "moi", "application", "ung tuyen"]),
    ("SCREENING", "Sàng lọc CV", 2, 3, False,
     ["screening", "sang loc", "sang loc cv", "loc cv", "cv screening", "duyet cv", "review cv"]),
    ("HR_INTERVIEW", "Phỏng vấn HR", 3, 4, False,
     ["hr interview", "phong van hr", "pv hr", "phone screen", "phong van vong 1", "pv vong 1", "vong 1"]),
    ("TECH_INTERVIEW", "Phỏng vấn chuyên môn", 4, 4, False,
     ["technical interview", "tech interview", "phong van chuyen mon", "pv chuyen mon", "phong van ky thuat",
      "pv ky thuat", "phong van vong 2", "pv vong 2", "vong 2", "bai test", "technical test"]),
    ("FINAL_INTERVIEW", "Phỏng vấn cuối (Quản lý)", 5, 3, False,
     ["final interview", "phong van cuoi", "pv cuoi", "phong van quan ly", "pv quan ly", "manager interview",
      "phong van vong 3", "vong 3", "pv vong 3"]),
    ("OFFER", "Đề nghị nhận việc (Offer)", 6, 5, False, ["offer", "de nghi", "thu moi nhan viec", "gui offer", "offer letter"]),
    ("HIRED", "Nhận việc", 7, 0, True, ["hired", "nhan viec", "da nhan viec", "onboard", "onboarded", "di lam"]),
]

STATUS_ALIASES: dict[str, list[str]] = {
    "active": ["active", "in progress", "dang xu ly", "dang phong van", "cho phong van", "cho ket qua", "pending",
               "dang cho", "dang tuyen", "open"],
    "hired": ["hired", "da tuyen", "nhan viec", "da nhan viec", "onboard", "trung tuyen"],
    "rejected": ["rejected", "loai", "truot", "khong dat", "tu choi", "fail", "failed", "khong phu hop"],
    "withdrawn": ["withdrawn", "rut ho so", "ung vien rut", "huy", "khong tham gia", "tu choi offer", "declined"],
    "on_hold": ["on hold", "tam dung", "hold", "bao luu"],
}

OUTCOME_ALIASES: dict[str, list[str]] = {
    "passed": ["passed", "pass", "dat", "qua", "dau", "ok", "accepted", "chap nhan", "dong y"],
    "failed": ["failed", "fail", "truot", "khong dat", "loai", "rejected"],
    "withdrawn": ["withdrawn", "rut", "tu choi", "declined", "huy"],
    "no_show": ["no show", "vang", "khong den", "vang mat", "khong tham du"],
    "pending": ["pending", "cho", "dang cho", "chua co"],
}

CITY_ALIASES: dict[str, list[str]] = {
    "TP. Hồ Chí Minh": ["hcm", "tp hcm", "tphcm", "ho chi minh", "tp ho chi minh", "sai gon", "saigon", "hcmc",
                        "thanh pho ho chi minh"],
    "Hà Nội": ["ha noi", "hanoi", "hn", "tp ha noi"],
    "Đà Nẵng": ["da nang", "danang", "dn"],
    "Cần Thơ": ["can tho"],
    "Bình Dương": ["binh duong"],
    "Đồng Nai": ["dong nai", "bien hoa"],
    "Hải Phòng": ["hai phong"],
}

EDUCATION_ALIASES: dict[str, list[str]] = {
    "Tiến sĩ": ["tien si", "phd", "doctor"],
    "Thạc sĩ": ["thac si", "master", "cao hoc", "mba"],
    "Đại học": ["dai hoc", "cu nhan", "ky su", "bachelor", "university", "dh"],
    "Cao đẳng": ["cao dang", "college", "cd"],
    "Trung cấp": ["trung cap", "vocational"],
    "THPT": ["thpt", "12/12", "pho thong", "high school"],
}

POSITIONS: list[dict] = [
    {
        "code": "DA-2026", "title": "Chuyên viên Phân tích dữ liệu (Data Analyst)", "department": "DATA",
        "level": "Junior/Middle", "location": "TP. Hồ Chí Minh", "headcount": 3, "manager": "manager.data",
        "required_skills": ["SQL", "Python", "Power BI", "Excel", "Thống kê"],
        "nice_to_have_skills": ["Tableau", "Pandas", "Giao tiếp"],
        "aliases": ["data analyst", "da", "phan tich du lieu", "chuyen vien phan tich du lieu", "nhan vien phan tich du lieu",
                    "business data analyst", "data analyst junior"],
        "jd": "Thu thập, làm sạch và phân tích dữ liệu kinh doanh; xây dựng dashboard Power BI; viết truy vấn SQL "
              "phức tạp; trình bày insight cho các phòng ban. Yêu cầu: thành thạo SQL, Python (Pandas), Excel, "
              "kiến thức thống kê; ưu tiên biết Tableau và có kỹ năng giao tiếp tốt.",
        "opened": date(2026, 7, 25),
    },
    {
        "code": "DE-2026", "title": "Kỹ sư Dữ liệu (Data Engineer)", "department": "DATA",
        "level": "Middle", "location": "TP. Hồ Chí Minh", "headcount": 2, "manager": "manager.data",
        "required_skills": ["Python", "SQL", "ETL", "PostgreSQL", "Airflow"],
        "nice_to_have_skills": ["Spark", "Docker", "AWS"],
        "aliases": ["data engineer", "de", "ky su du lieu", "etl developer", "big data engineer"],
        "jd": "Thiết kế và vận hành pipeline ETL/ELT, kho dữ liệu trên PostgreSQL; lập lịch với Airflow; "
              "đảm bảo chất lượng dữ liệu. Yêu cầu: Python, SQL, ETL, PostgreSQL, Airflow; ưu tiên Spark, Docker, AWS.",
        "opened": date(2026, 7, 28),
    },
    {
        "code": "AI-2026", "title": "Kỹ sư AI/Machine Learning", "department": "DATA",
        "level": "Middle/Senior", "location": "Hà Nội", "headcount": 1, "manager": "manager.data",
        "required_skills": ["Python", "Machine Learning", "Deep Learning", "NLP", "PyTorch"],
        "nice_to_have_skills": ["LLM", "Docker", "MLOps"],
        "aliases": ["ai engineer", "machine learning engineer", "ml engineer", "ky su ai", "ky su machine learning",
                    "ai ml engineer", "nlp engineer"],
        "jd": "Nghiên cứu, huấn luyện và triển khai mô hình học máy, xử lý ngôn ngữ tự nhiên tiếng Việt; tích hợp LLM "
              "vào sản phẩm. Yêu cầu: Python, Machine Learning, Deep Learning, NLP, PyTorch; ưu tiên LLM, MLOps, Docker.",
        "opened": date(2026, 8, 5),
    },
    {
        "code": "BE-2026", "title": "Lập trình viên Backend (Python)", "department": "TECH",
        "level": "Junior/Middle", "location": "TP. Hồ Chí Minh", "headcount": 3, "manager": "manager.tech",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "REST API", "Git"],
        "nice_to_have_skills": ["Docker", "Redis", "Django"],
        "aliases": ["backend developer", "python developer", "lap trinh vien backend", "backend engineer",
                    "python backend", "back end developer", "lap trinh vien python", "backend dev"],
        "jd": "Phát triển RESTful API bằng Python/FastAPI, thiết kế CSDL PostgreSQL, viết unit test, review code. "
              "Yêu cầu: Python, FastAPI, PostgreSQL, REST API, Git; ưu tiên Docker, Redis, Django.",
        "opened": date(2026, 7, 20),
    },
    {
        "code": "FE-2026", "title": "Lập trình viên Frontend (ReactJS)", "department": "TECH",
        "level": "Junior/Middle", "location": "TP. Hồ Chí Minh", "headcount": 2, "manager": "manager.tech",
        "required_skills": ["JavaScript", "TypeScript", "ReactJS", "HTML/CSS", "Git"],
        "nice_to_have_skills": ["Next.js", "UI/UX", "Figma"],
        "aliases": ["frontend developer", "reactjs developer", "react developer", "lap trinh vien frontend",
                    "front end developer", "front-end developer", "frontend dev", "fe developer"],
        "jd": "Xây dựng giao diện web bằng ReactJS/TypeScript, tối ưu hiệu năng và trải nghiệm người dùng. "
              "Yêu cầu: JavaScript, TypeScript, ReactJS, HTML/CSS, Git; ưu tiên Next.js, Figma.",
        "opened": date(2026, 7, 20),
    },
    {
        "code": "QA-2026", "title": "Kỹ sư Kiểm thử phần mềm (QA/Tester)", "department": "TECH",
        "level": "Junior", "location": "Đà Nẵng", "headcount": 2, "manager": "manager.tech",
        "required_skills": ["Manual testing", "Test case", "SQL", "Automation test"],
        "nice_to_have_skills": ["Selenium", "Postman", "Jira"],
        "aliases": ["tester", "qa", "qa engineer", "qc", "kiem thu phan mem", "nhan vien kiem thu", "software tester",
                    "qa tester", "qa qc"],
        "jd": "Viết test case, thực hiện kiểm thử thủ công và tự động, báo cáo lỗi trên Jira. Yêu cầu: kiểm thử thủ "
              "công, viết test case, SQL cơ bản, automation test; ưu tiên Selenium, Postman.",
        "opened": date(2026, 8, 1),
    },
    {
        "code": "HR-2026", "title": "Chuyên viên Tuyển dụng", "department": "HR",
        "level": "Junior/Middle", "location": "TP. Hồ Chí Minh", "headcount": 1, "manager": None,
        "required_skills": ["Tuyển dụng", "Phỏng vấn", "Excel", "Giao tiếp"],
        "nice_to_have_skills": ["ATS", "Employer branding"],
        "aliases": ["chuyen vien tuyen dung", "nhan vien tuyen dung", "recruiter", "hr executive", "talent acquisition",
                    "chuyen vien nhan su", "hr recruiter"],
        "jd": "Tìm kiếm nguồn ứng viên, sàng lọc CV, phỏng vấn sơ bộ, quản lý dữ liệu trên ATS và báo cáo tuyển dụng. "
              "Yêu cầu: kinh nghiệm tuyển dụng, kỹ năng phỏng vấn, Excel, giao tiếp; ưu tiên ATS, employer branding.",
        "opened": date(2026, 8, 10),
    },
    {
        "code": "SALES-2026", "title": "Chuyên viên Kinh doanh B2B", "department": "SALES",
        "level": "Junior/Middle", "location": "Hà Nội", "headcount": 4, "manager": None,
        "required_skills": ["Bán hàng B2B", "Đàm phán", "CRM", "Giao tiếp"],
        "nice_to_have_skills": ["Tiếng Anh", "Thuyết trình"],
        "aliases": ["sales executive", "nhan vien kinh doanh", "chuyen vien kinh doanh", "sales b2b", "account executive",
                    "kinh doanh b2b", "nhan vien sale"],
        "jd": "Tìm kiếm khách hàng doanh nghiệp, tư vấn giải pháp phần mềm, đàm phán hợp đồng, quản lý pipeline trên "
              "CRM. Yêu cầu: bán hàng B2B, đàm phán, CRM, giao tiếp; ưu tiên tiếng Anh, thuyết trình.",
        "opened": date(2026, 7, 15),
    },
    {
        "code": "MKT-2026", "title": "Chuyên viên Digital Marketing", "department": "MKT",
        "level": "Junior", "location": "TP. Hồ Chí Minh", "headcount": 1, "manager": None,
        "required_skills": ["SEO", "Facebook Ads", "Google Ads", "Content Marketing", "Google Analytics"],
        "nice_to_have_skills": ["Figma", "Thuyết trình"],
        "aliases": ["digital marketing", "digital marketing executive", "chuyen vien marketing", "marketing online",
                    "nhan vien marketing", "performance marketing"],
        "jd": "Lập kế hoạch và triển khai chiến dịch quảng cáo Facebook/Google Ads, tối ưu SEO, sản xuất nội dung, "
              "đo lường bằng Google Analytics.",
        "opened": date(2026, 8, 12),
    },
    {
        "code": "ACC-2026", "title": "Kế toán tổng hợp", "department": "FIN",
        "level": "Middle", "location": "TP. Hồ Chí Minh", "headcount": 1, "manager": None,
        "required_skills": ["Kế toán", "Excel", "MISA", "Thuế", "Báo cáo tài chính"],
        "nice_to_have_skills": ["SAP", "Tiếng Anh"],
        "aliases": ["ke toan tong hop", "ke toan", "accountant", "general accountant", "nhan vien ke toan"],
        "jd": "Hạch toán, lập báo cáo tài chính, quyết toán thuế, sử dụng phần mềm MISA. Yêu cầu: kế toán, Excel, "
              "MISA, thuế, báo cáo tài chính.",
        "opened": date(2026, 8, 1),
    },
]

DEMO_USERS: list[dict] = [
    {"username": "admin", "full_name": "Quản trị hệ thống", "role": "admin", "department": None,
     "email": "admin@talentlens.vn"},
    {"username": "hr.lan", "full_name": "Nguyễn Thị Lan (HR Recruiter)", "role": "hr", "department": "HR",
     "email": "lan.nguyen@talentlens.vn"},
    {"username": "hr.minh", "full_name": "Phạm Đức Minh (HR Lead)", "role": "hr", "department": "HR",
     "email": "minh.pham@talentlens.vn"},
    {"username": "manager.data", "full_name": "Trần Quốc Bảo (Trưởng khối Dữ liệu & AI)", "role": "hiring_manager",
     "department": "DATA", "email": "bao.tran@talentlens.vn"},
    {"username": "manager.tech", "full_name": "Lê Thu Hà (Trưởng khối Công nghệ)", "role": "hiring_manager",
     "department": "TECH", "email": "ha.le@talentlens.vn"},
]
