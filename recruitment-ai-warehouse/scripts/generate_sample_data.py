"""Sinh bộ dữ liệu tuyển dụng mẫu (giả lập) từ 4 nguồn rời rạc để chạy thử ETL.

Kết quả (thư mục data/raw):
  * google_form_responses.csv  – câu trả lời Google Form ứng tuyển
  * ats_export.json            – dữ liệu xuất từ ATS (vị trí + hồ sơ + lịch sử vòng)
  * hr_tracking.xlsx           – file Excel HR tự theo dõi (tiêu đề ở dòng 3, định dạng lộn xộn)
  * emails/*.eml               – email ứng tuyển / rút hồ sơ (kèm CV)
  * cvs/*.pdf|docx|txt         – CV của ứng viên

Dữ liệu có chủ đích chứa lỗi thường gặp: trùng ứng viên giữa các nguồn, số điện thoại/ngày tháng
nhiều định dạng, tên không dấu, vị trí/nguồn viết khác nhau, bản ghi thiếu thông tin.
Toàn bộ tên người, email, số điện thoại là GIẢ LẬP.

Chạy:  python scripts/generate_sample_data.py [--out data/raw] [--seed 2026]
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from email.utils import format_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.reference import POSITIONS  # noqa: E402

VN = ZoneInfo("Asia/Ho_Chi_Minh")
START = datetime(2026, 8, 3, 8, 0)
END = datetime(2026, 11, 7, 17, 30)
N_APPLICATIONS = 330

FAMILY = ["Nguyễn"] * 8 + ["Trần"] * 4 + ["Lê"] * 3 + ["Phạm"] * 2 + [
    "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Trương", "Đinh"]
MALE_MID = ["Văn", "Minh", "Quốc", "Đức", "Thành", "Hoàng", "Gia", "Anh", "Hữu", "Tuấn", "Trung", "Nhật"]
FEMALE_MID = ["Thị", "Ngọc", "Thu", "Thanh", "Phương", "Mai", "Bảo", "Khánh", "Minh", "Hoài", "Diệu", "Kim"]
MALE_GIVEN = ["An", "Bình", "Dũng", "Hùng", "Khang", "Long", "Nam", "Phúc", "Quân", "Sơn", "Tâm", "Thắng", "Trí",
              "Tùng", "Việt", "Huy", "Khoa", "Kiên", "Lâm", "Nhân", "Phát", "Tài", "Thịnh", "Vinh", "Đạt", "Hiếu",
              "Hưng", "Tuấn", "Duy", "Hải", "Lộc", "Nghĩa", "Toàn", "Hào"]
FEMALE_GIVEN = ["Anh", "Chi", "Dung", "Giang", "Hà", "Hạnh", "Hằng", "Hương", "Lan", "Linh", "Mai", "My", "Ngân",
                "Ngọc", "Nhi", "Oanh", "Phương", "Quyên", "Thảo", "Trang", "Trâm", "Uyên", "Vy", "Yến", "Hân", "Thư",
                "Tiên", "Như", "Diệp", "Khánh", "Loan", "Nhung", "Tâm"]
CITIES = [("TP. Hồ Chí Minh", 50, ["TP.HCM", "Hồ Chí Minh", "HCM", "Sài Gòn", "tp hcm"]),
          ("Hà Nội", 28, ["Hà Nội", "Ha Noi", "HN"]),
          ("Đà Nẵng", 10, ["Đà Nẵng", "Da Nang"]),
          ("Cần Thơ", 4, ["Cần Thơ"]), ("Bình Dương", 4, ["Bình Dương"]), ("Đồng Nai", 4, ["Đồng Nai"])]
UNIVERSITIES = ["ĐH Bách khoa – ĐHQG TP.HCM", "ĐH Kinh tế TP.HCM", "ĐH Công nghệ Thông tin – ĐHQG TP.HCM",
                "ĐH Bách khoa Hà Nội", "Học viện Hàng không Việt Nam", "ĐH Tôn Đức Thắng", "ĐH FPT",
                "ĐH Ngoại thương", "ĐH Khoa học Tự nhiên – ĐHQG TP.HCM", "ĐH Kinh tế Quốc dân", "ĐH Đà Nẵng",
                "ĐH Cần Thơ", "ĐH Sư phạm Kỹ thuật TP.HCM", "ĐH Công nghiệp TP.HCM"]
COMPANIES = ["Công ty TNHH Minh Phát", "Công ty CP Công nghệ Sao Việt", "FinViet JSC", "Công ty TNHH Logistics Hải Âu",
             "Công ty CP Bán lẻ An Khang Mart", "TechNova Việt Nam", "Công ty TNHH Phần mềm Đông Á",
             "Công ty CP Thương mại điện tử VietShop", "Ngân hàng TMCP Phương Nam (giả lập)", "EduSmart JSC",
             "Công ty TNHH Dược phẩm Thiên Ân", "Công ty CP Truyền thông Mặt Trời", "GreenData Solutions"]

SOURCE_WEIGHTS = {"TOPCV": 26, "VIETNAMWORKS": 11, "ITVIEC": 9, "LINKEDIN": 14, "FACEBOOK": 12, "REFERRAL": 9,
                  "CAREER_SITE": 10, "JOB_FAIR": 5, "DIRECT_EMAIL": 4}
SOURCE_TEXT = {
    "TOPCV": ["TopCV", "topcv.vn", "Top CV", "TOPCV"],
    "VIETNAMWORKS": ["VietnamWorks", "vietnamworks", "VNW"],
    "ITVIEC": ["ITviec", "itviec.com"],
    "LINKEDIN": ["LinkedIn", "Linkedin", "linkedin.com"],
    "FACEBOOK": ["Facebook", "FB group", "Group Facebook tuyển dụng IT", "facebook"],
    "REFERRAL": ["Giới thiệu", "Nhân viên giới thiệu", "Referral", "Bạn bè giới thiệu"],
    "CAREER_SITE": ["Website công ty", "Website", "Trang tuyển dụng công ty", "Career site"],
    "JOB_FAIR": ["Ngày hội việc làm", "Job fair ĐH Bách Khoa", "Ngày hội việc làm HUFI"],
    "DIRECT_EMAIL": ["Email", "Gửi mail trực tiếp"],
}
FORM_SOURCE_OPTIONS = {"TOPCV": "TopCV", "VIETNAMWORKS": "VietnamWorks", "ITVIEC": "ITviec", "LINKEDIN": "LinkedIn",
                       "FACEBOOK": "Facebook", "REFERRAL": "Bạn bè/người quen giới thiệu",
                       "CAREER_SITE": "Website công ty", "JOB_FAIR": "Ngày hội việc làm", "DIRECT_EMAIL": "Khác"}
POSITION_WEIGHTS = {"DA-2026": 16, "BE-2026": 16, "FE-2026": 10, "DE-2026": 8, "AI-2026": 6, "QA-2026": 8,
                    "HR-2026": 6, "SALES-2026": 14, "MKT-2026": 9, "ACC-2026": 7}
POSITION_TEXT = {
    "DA-2026": ["Data Analyst", "DA", "Chuyên viên Phân tích dữ liệu", "Data analyst (Junior)", "Phân tích dữ liệu"],
    "DE-2026": ["Data Engineer", "Kỹ sư dữ liệu", "ETL Developer"],
    "AI-2026": ["AI Engineer", "Machine Learning Engineer", "Kỹ sư AI/ML"],
    "BE-2026": ["Backend Developer", "Python Developer", "Lập trình viên Backend", "Backend Dev (Python)"],
    "FE-2026": ["Frontend Developer", "ReactJS Developer", "Lập trình viên Frontend", "Front-end Dev"],
    "QA-2026": ["Tester", "QA Engineer", "Kiểm thử phần mềm", "QC/Tester"],
    "HR-2026": ["Chuyên viên tuyển dụng", "Recruiter", "Nhân viên tuyển dụng"],
    "SALES-2026": ["Nhân viên kinh doanh", "Sales Executive", "Chuyên viên kinh doanh B2B", "Sales B2B"],
    "MKT-2026": ["Digital Marketing", "Chuyên viên Marketing", "Marketing Online"],
    "ACC-2026": ["Kế toán tổng hợp", "Kế toán", "Accountant"],
}
SALARY_RANGE = {"DA-2026": (12, 25), "DE-2026": (18, 35), "AI-2026": (25, 45), "BE-2026": (15, 35),
                "FE-2026": (12, 28), "QA-2026": (10, 18), "HR-2026": (10, 18), "SALES-2026": (8, 15),
                "MKT-2026": (10, 18), "ACC-2026": (12, 22)}
INTERVIEWERS = {"DATA": ["Trần Quốc Bảo", "Lý Minh Khôi", "Đỗ Thu Trang"],
                "TECH": ["Lê Thu Hà", "Phan Văn Toàn", "Ngô Gia Huy"],
                "HR": ["Phạm Đức Minh"], "SALES": ["Vũ Hoàng Long", "Bùi Thị Hồng"],
                "MKT": ["Đặng Mỹ Linh"], "FIN": ["Hồ Thanh Tùng"]}
HR_INTERVIEWERS = ["Nguyễn Thị Lan", "Phạm Đức Minh"]

FAMILY_PROFILE = {
    "DA-2026": dict(titles=["Data Analyst", "Business Analyst", "Chuyên viên báo cáo", "Sinh viên năm cuối HTTT"],
                    skills=["SQL", "Python", "Power BI", "Excel", "Thống kê", "Tableau", "Pandas", "Looker Studio",
                            "Giao tiếp", "Thuyết trình"],
                    bullets=["Xây dựng {n} dashboard Power BI theo dõi doanh thu và tồn kho cho ban giám đốc",
                             "Viết truy vấn SQL tổng hợp dữ liệu bán hàng, giảm {p}% thời gian lập báo cáo tuần",
                             "Làm sạch và phân tích dữ liệu khách hàng bằng Python (Pandas), phân khúc {n} nhóm khách hàng",
                             "Thiết kế báo cáo A/B testing chiến dịch khuyến mãi, kiểm định thống kê kết quả",
                             "Tự động hoá báo cáo Excel bằng Pivot Table và VBA cho phòng kinh doanh"],
                    majors=["Hệ thống thông tin quản lý", "Thống kê", "Khoa học dữ liệu", "Kinh tế lượng"],
                    certs=["Google Data Analytics Certificate", "Microsoft PL-300 (Power BI)", "IELTS 6.5", "TOEIC 750"]),
    "DE-2026": dict(titles=["Data Engineer", "ETL Developer", "Backend Developer", "BI Developer"],
                    skills=["Python", "SQL", "ETL", "PostgreSQL", "Airflow", "Spark", "Docker", "AWS", "Kafka", "Git"],
                    bullets=["Xây dựng pipeline ETL bằng Python và Airflow nạp {n} triệu bản ghi/ngày vào PostgreSQL",
                             "Thiết kế kho dữ liệu lược đồ hình sao phục vụ {n} dashboard báo cáo",
                             "Tối ưu job Spark giúp giảm {p}% thời gian xử lý dữ liệu log",
                             "Đóng gói pipeline bằng Docker, triển khai trên AWS (S3, EC2)"],
                    majors=["Khoa học máy tính", "Kỹ thuật phần mềm", "Hệ thống thông tin"],
                    certs=["AWS Certified Data Engineer – Associate", "IELTS 6.0", "Google Cloud Data Engineer"]),
    "AI-2026": dict(titles=["AI Engineer", "Machine Learning Engineer", "Data Scientist", "Nghiên cứu viên AI"],
                    skills=["Python", "Machine Learning", "Deep Learning", "NLP", "PyTorch", "TensorFlow", "LLM",
                            "Docker", "MLOps", "Scikit-learn"],
                    bullets=["Huấn luyện mô hình phân loại văn bản tiếng Việt (NLP) bằng PyTorch đạt F1 {p}%",
                             "Xây dựng chatbot RAG tích hợp LLM phục vụ {n} nghìn người dùng",
                             "Triển khai mô hình Machine Learning dự báo nhu cầu, giảm {p}% sai số",
                             "Thiết lập quy trình MLOps với MLflow và Docker"],
                    majors=["Khoa học máy tính", "Trí tuệ nhân tạo", "Toán ứng dụng"],
                    certs=["Deep Learning Specialization", "IELTS 7.0", "Bài báo hội nghị RIVF"]),
    "BE-2026": dict(titles=["Backend Developer", "Python Developer", "Software Engineer", "Fresher Developer"],
                    skills=["Python", "FastAPI", "Django", "PostgreSQL", "REST API", "Git", "Docker", "Redis", "MySQL",
                            "Linux"],
                    bullets=["Phát triển RESTful API bằng FastAPI phục vụ {n} nghìn request/ngày",
                             "Thiết kế CSDL PostgreSQL và tối ưu truy vấn giảm {p}% thời gian phản hồi",
                             "Viết unit test đạt độ phủ {p}% và thiết lập CI/CD với GitHub Actions",
                             "Tích hợp Redis cache và hàng đợi xử lý bất đồng bộ"],
                    majors=["Kỹ thuật phần mềm", "Công nghệ thông tin", "Khoa học máy tính"],
                    certs=["TOEIC 700", "Chứng chỉ Python PCAP"]),
    "FE-2026": dict(titles=["Frontend Developer", "Web Developer", "UI Developer"],
                    skills=["JavaScript", "TypeScript", "ReactJS", "HTML/CSS", "Git", "Next.js", "Figma", "UI/UX",
                            "Vue.js"],
                    bullets=["Xây dựng giao diện quản trị bằng ReactJS và TypeScript cho {n} module",
                             "Tối ưu hiệu năng trang chủ, tăng điểm Lighthouse lên {p}",
                             "Chuyển đổi thiết kế Figma thành giao diện responsive bằng HTML/CSS (Tailwind)",
                             "Phát triển website thương mại điện tử bằng Next.js"],
                    majors=["Công nghệ thông tin", "Kỹ thuật phần mềm", "Thiết kế đa phương tiện"],
                    certs=["TOEIC 650", "Meta Front-End Developer Certificate"]),
    "QA-2026": dict(titles=["Tester", "QA Engineer", "QC Executive", "Sinh viên thực tập kiểm thử"],
                    skills=["Manual testing", "Test case", "SQL", "Automation test", "Selenium", "Postman", "Jira"],
                    bullets=["Viết và thực thi hơn {n}0 test case cho ứng dụng ngân hàng di động",
                             "Xây dựng bộ automation test bằng Selenium, giảm {p}% thời gian regression",
                             "Kiểm thử API bằng Postman và quản lý lỗi trên Jira",
                             "Kiểm thử thủ công (manual testing) các luồng thanh toán"],
                    majors=["Công nghệ thông tin", "Hệ thống thông tin"],
                    certs=["ISTQB Foundation Level", "TOEIC 600"]),
    "HR-2026": dict(titles=["Chuyên viên tuyển dụng", "HR Executive", "Recruiter", "Nhân viên hành chính nhân sự"],
                    skills=["Tuyển dụng", "Phỏng vấn", "Excel", "Giao tiếp", "ATS", "Employer branding", "Onboarding"],
                    bullets=["Phụ trách tuyển dụng {n}0 vị trí/năm cho khối kinh doanh và vận hành",
                             "Tổ chức phỏng vấn, sàng lọc CV và quản lý dữ liệu ứng viên trên ATS",
                             "Triển khai chương trình employer branding tăng {p}% lượng hồ sơ",
                             "Xây dựng quy trình onboarding cho nhân viên mới"],
                    majors=["Quản trị nhân lực", "Quản trị kinh doanh", "Tâm lý học"],
                    certs=["Chứng chỉ Quản trị nhân sự", "TOEIC 650"]),
    "SALES-2026": dict(titles=["Nhân viên kinh doanh", "Sales Executive", "Account Manager", "Telesales"],
                       skills=["Bán hàng B2B", "Đàm phán", "CRM", "Giao tiếp", "Tiếng Anh", "Thuyết trình"],
                       bullets=["Đạt {p}% chỉ tiêu doanh số bán hàng B2B năm 2025",
                                "Quản lý {n}0 khách hàng doanh nghiệp trên CRM (HubSpot)",
                                "Đàm phán và chốt hợp đồng giá trị {n} tỷ đồng",
                                "Thuyết trình giải pháp phần mềm cho ban lãnh đạo khách hàng"],
                       majors=["Quản trị kinh doanh", "Marketing", "Kinh doanh quốc tế"],
                       certs=["TOEIC 600", "Chứng chỉ Kỹ năng bán hàng chuyên nghiệp"]),
    "MKT-2026": dict(titles=["Digital Marketing Executive", "Content Marketing", "Marketing Executive"],
                     skills=["SEO", "Facebook Ads", "Google Ads", "Content Marketing", "Google Analytics", "Figma"],
                     bullets=["Quản lý ngân sách Facebook Ads {n}00 triệu/tháng, giảm {p}% CPA",
                              "Tối ưu SEO đưa {n}0 từ khoá lên top 10 Google",
                              "Sản xuất content marketing cho fanpage {n}00 nghìn người theo dõi",
                              "Đo lường chiến dịch bằng Google Analytics (GA4)"],
                     majors=["Marketing", "Quan hệ công chúng", "Quản trị kinh doanh"],
                     certs=["Google Ads Certification", "Meta Blueprint"]),
    "ACC-2026": dict(titles=["Kế toán tổng hợp", "Kế toán viên", "Kế toán thuế"],
                     skills=["Kế toán", "Excel", "MISA", "Thuế", "Báo cáo tài chính", "SAP"],
                     bullets=["Hạch toán và lập báo cáo tài chính năm cho {n} đơn vị thành viên",
                              "Kê khai, quyết toán thuế GTGT, TNDN, TNCN đúng hạn",
                              "Sử dụng thành thạo phần mềm MISA và Excel nâng cao",
                              "Phối hợp kiểm toán độc lập, xử lý {n}0 bút toán điều chỉnh"],
                     majors=["Kế toán", "Tài chính – Ngân hàng", "Kiểm toán"],
                     certs=["Chứng chỉ Kế toán trưởng", "ACCA F1–F3"]),
}
SKILL_TEXT = {"SQL": "SQL", "Python": "Python", "Power BI": "Power BI", "Excel": "Excel nâng cao",
              "Thống kê": "Thống kê", "HTML/CSS": "HTML/CSS", "UI/UX": "UI/UX", "Bán hàng B2B": "Bán hàng B2B",
              "Manual testing": "Kiểm thử thủ công (manual testing)", "Test case": "Viết test case",
              "Automation test": "Automation test", "Thuế": "Quyết toán thuế", "Content Marketing": "Content marketing"}

REJECT_REASONS = {
    "SCREENING": ["CV chưa đáp ứng kinh nghiệm tối thiểu", "Kinh nghiệm chưa phù hợp với vị trí",
                  "Thiếu kỹ năng chuyên môn theo yêu cầu JD", "CV sơ sài, chưa thể hiện kỹ năng chuyên môn",
                  "Chưa có kinh nghiệm thực tế", "Overqualified – kinh nghiệm quá cao so với vị trí"],
    "HR_INTERVIEW": ["Kỳ vọng mức lương cao hơn ngân sách", "Kỹ năng giao tiếp chưa tốt", "Tiếng Anh chưa đạt yêu cầu",
                     "Không thể đi làm onsite tại văn phòng", "Chưa phù hợp văn hoá công ty",
                     "Thái độ chưa cầu tiến, động lực làm việc thấp"],
    "TECH_INTERVIEW": ["Không đạt bài test chuyên môn", "Kiến thức chuyên môn còn yếu", "Chưa nắm vững kiến thức nền tảng",
                       "Bài test logic dưới chuẩn", "Kỹ năng chuyên môn chưa đáp ứng",
                       "Thiếu kinh nghiệm thực tế với hệ thống lớn", "Coding chưa tốt, chưa xử lý được bài toán"],
    "FINAL_INTERVIEW": ["Chưa phù hợp định hướng của team", "Kinh nghiệm quản lý chưa đủ",
                        "Mức lương mong muốn vượt khung", "Kỹ năng trình bày chưa thuyết phục"],
}
NO_SHOW_REASONS = ["Ứng viên không đến phỏng vấn, không nghe máy", "Không phản hồi lịch hẹn phỏng vấn"]
OFFER_DECLINE = [("Ứng viên từ chối offer do mức lương chưa phù hợp", 5),
                 ("Ứng viên nhận offer công ty khác", 4), ("Từ chối offer vì lý do cá nhân", 1)]
WITHDRAW_REASONS_LONG = [("Đã nhận offer công ty khác trong lúc chờ phỏng vấn", 6),
                         ("Chờ lâu không có phản hồi nên không tiếp tục", 3), ("Lý do cá nhân", 1)]
WITHDRAW_REASONS_SHORT = [("Lý do cá nhân", 3), ("Địa điểm làm việc xa nhà", 2), ("Đã nhận việc nơi khác", 2)]
TECH_NOTES_PASS = ["Nắm vững kiến thức, giải được {k}/5 câu", "Tư duy logic tốt, trình bày rõ ràng",
                   "Kinh nghiệm thực tế phù hợp, cần cải thiện thêm về tối ưu", "Làm bài test tốt, code sạch"]
TECH_NOTES_FAIL = ["Giải được {k}/5 câu, kiến thức nền còn yếu", "Chưa giải thích được lựa chọn kỹ thuật",
                   "Bài test chưa hoàn thành đúng thời gian"]
BIASED_NOTES = ["Ứng viên nữ, đã lập gia đình và có con nhỏ nên khó tăng ca",
                "Ứng viên lớn tuổi so với team, có thể khó hoà nhập",
                "Giọng miền Trung hơi khó nghe khi trao đổi với khách hàng",
                "Ngoại hình ưa nhìn, phù hợp gặp khách hàng",
                "Ứng viên mới kết hôn, có thể sắp nghỉ thai sản"]


def no_accent(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


@dataclass
class Person:
    pid: int
    full_name: str
    family: str
    given: str
    gender: str
    dob: date
    email: str
    phone: str
    city: str
    city_raw: str
    years: float
    education: str
    university: str
    major: str
    title: str
    skills: list[str]
    cv_file: str | None = None
    cv_text: str | None = None


@dataclass
class Event:
    stage: str
    entered: datetime
    exited: datetime | None = None
    outcome: str | None = None
    interviewer: str | None = None
    score: float | None = None
    notes: str | None = None


@dataclass
class App:
    aid: int
    person: Person
    pos: str
    source: str
    applied: datetime
    salary: float
    events: list[Event] = field(default_factory=list)
    status: str = "active"
    closed: datetime | None = None
    reason: str | None = None
    systems: list[str] = field(default_factory=list)


class Generator:
    def __init__(self, seed: int):
        self.r = random.Random(seed)
        self.positions = {p["code"]: p for p in POSITIONS}
        self.used_emails: set[str] = set()
        self.used_phones: set[str] = set()

    # ---------------------------------------------------------------- người
    def person(self, pid: int, pos: str) -> Person:
        r = self.r
        gender = r.choice(["Nam", "Nữ"])
        family = r.choice(FAMILY)
        mid = r.choice(MALE_MID if gender == "Nam" else FEMALE_MID)
        given = r.choice(MALE_GIVEN if gender == "Nam" else FEMALE_GIVEN)
        full = f"{family} {mid} {given}"
        dob = date(r.randint(1988, 2004), r.randint(1, 12), r.randint(1, 28))
        base = f"{no_accent(given).lower()}.{no_accent(family).lower()}"
        email = f"{base}{str(dob.year)[2:]}@{r.choice(['gmail.com'] * 6 + ['yahoo.com', 'outlook.com', 'hotmail.com'])}"
        while email in self.used_emails:
            email = f"{base}{r.randint(1, 999)}@gmail.com"
        self.used_emails.add(email)
        phone = "0" + r.choice("3579") + "".join(str(r.randint(0, 9)) for _ in range(8))
        while phone in self.used_phones:
            phone = "0" + r.choice("3579") + "".join(str(r.randint(0, 9)) for _ in range(8))
        self.used_phones.add(phone)
        city, _w, variants = r.choices(CITIES, weights=[c[1] for c in CITIES])[0]
        prof = FAMILY_PROFILE[pos]
        years = max(0.0, round(r.triangular(0, 9, 2.5) * 2) / 2)
        if dob.year >= 2003:
            years = min(years, 1.0)
        req = self.positions[pos]["required_skills"]
        skills = [s for s in prof["skills"] if r.random() < (0.72 if s in req else 0.4)]
        if not skills:
            skills = [r.choice(prof["skills"])]
        edu = r.choices(["Đại học", "Thạc sĩ", "Cao đẳng"], weights=[80, 10, 10])[0]
        title = prof["titles"][-1] if years < 1 else r.choice(prof["titles"][:-1] or prof["titles"])
        return Person(pid, full, family, given, gender, dob, email, phone, city, r.choice(variants), years, edu,
                      r.choice(UNIVERSITIES), r.choice(prof["majors"]), title, skills)

    def cv_text(self, p: Person, pos: str) -> str:
        r = self.r
        prof = FAMILY_PROFILE[pos]
        lines = [p.full_name.upper(), p.title, "",
                 f"Ngày sinh: {p.dob:%d/%m/%Y} | Giới tính: {p.gender}",
                 f"Điện thoại: {p.phone[:4]} {p.phone[4:7]} {p.phone[7:]} | Email: {p.email}",
                 f"Địa chỉ: {r.choice(['Quận 7', 'Thủ Đức', 'Bình Thạnh', 'Cầu Giấy', 'Hải Châu', 'Quận 3'])}, {p.city}",
                 r.choice(["Tình trạng hôn nhân: Độc thân", "Tình trạng hôn nhân: Đã kết hôn", ""]), "",
                 "MỤC TIÊU NGHỀ NGHIỆP",
                 f"Mong muốn phát triển ở vị trí {self.positions[pos]['title']}, ứng dụng kinh nghiệm thực tế để tạo ra giá "
                 f"trị đo lường được cho doanh nghiệp.", "",
                 "KINH NGHIỆM LÀM VIỆC", f"Tổng kinh nghiệm: {p.years:g} năm"]
        n_jobs = 1 if p.years < 2 else 2 if p.years < 5 else 3
        year = 2026
        for _ in range(n_jobs if p.years > 0 else 0):
            span = max(1, int(p.years / n_jobs))
            lines.append(f"{r.choice(COMPANIES)} ({year - span}/{r.randint(1, 12):02d} – "
                         f"{'nay' if year == 2026 else str(year)}) – {p.title}")
            for b in r.sample(prof["bullets"], k=2):
                lines.append("- " + b.format(n=r.randint(2, 9), p=r.randint(15, 60)))
            year -= span
        if p.years == 0:
            lines += ["Thực tập sinh tại " + r.choice(COMPANIES) + " (06/2026 – 09/2026)",
                      "- " + prof["bullets"][0].format(n=2, p=20)]
        lines += ["", "HỌC VẤN", f"{p.university} – {p.education} {p.major} ({p.dob.year + 18} – {p.dob.year + 22})",
                  "", "KỸ NĂNG", "- " + ", ".join(SKILL_TEXT.get(s, s) for s in p.skills),
                  "- " + ", ".join(r.sample(["Giao tiếp", "Làm việc nhóm", "Quản lý thời gian", "Giải quyết vấn đề",
                                             "Thuyết trình"], k=2)), "",
                  "CHỨNG CHỈ", "- " + r.choice(prof["certs"])]
        return "\n".join(lines)

    # ----------------------------------------------------- mô phỏng pipeline
    def wait_days(self, stage: str, app: App) -> float:
        r = self.r
        dept = self.positions[app.pos]["department"]
        if stage == "SCREENING":
            return r.uniform(1.0, 5.0) if app.source in ("TOPCV", "VIETNAMWORKS") else r.uniform(0.3, 2.5)
        if stage == "HR_INTERVIEW":
            return r.uniform(1.0, 4.0)
        if stage == "TECH_INTERVIEW":  # điểm nghẽn: lịch của quản lý chuyên môn khối Công nghệ/Dữ liệu
            return r.triangular(3, 16, 10) if dept in ("TECH", "DATA") else r.triangular(2, 7, 3)
        if stage == "FINAL_INTERVIEW":
            return r.uniform(2.0, 6.0)
        if stage == "OFFER":
            return r.uniform(1.0, 4.0)
        return r.uniform(2.0, 7.0)  # HIRED

    def pass_prob(self, stage: str, app: App) -> float:
        if stage == "SCREENING":
            return {"REFERRAL": .8, "LINKEDIN": .62, "ITVIEC": .6, "CAREER_SITE": .56, "VIETNAMWORKS": .5,
                    "TOPCV": .42, "FACEBOOK": .45, "JOB_FAIR": .48, "DIRECT_EMAIL": .55}[app.source]
        if stage == "HR_INTERVIEW":
            return .78
        if stage == "TECH_INTERVIEW":
            return .66 if app.source == "REFERRAL" else .52
        if stage == "FINAL_INTERVIEW":
            return .8
        if stage == "OFFER":
            return .72
        return 1.0

    def simulate(self, app: App) -> None:
        r = self.r
        dept = self.positions[app.pos]["department"]
        t = app.applied
        app.events = [Event("APPLIED", t)]
        for stage in ["SCREENING", "HR_INTERVIEW", "TECH_INTERVIEW", "FINAL_INTERVIEW", "OFFER", "HIRED"]:
            wait = self.wait_days(stage, app)
            if stage in ("HR_INTERVIEW", "TECH_INTERVIEW", "FINAL_INTERVIEW") and \
                    r.random() < min(0.4, 0.01 + 0.02 * wait):
                tw = t + timedelta(days=wait * r.uniform(0.4, 0.9))
                if tw > END:
                    return
                pool = WITHDRAW_REASONS_LONG if wait > 7 else WITHDRAW_REASONS_SHORT
                app.status, app.closed = "withdrawn", tw
                app.reason = r.choices([p[0] for p in pool], weights=[p[1] for p in pool])[0]
                app.events[-1].exited, app.events[-1].outcome = tw, "withdrawn"
                return
            nxt = t + timedelta(days=wait, hours=r.uniform(-3, 3))
            nxt = nxt.replace(hour=r.randint(8, 17), minute=r.choice([0, 15, 30, 45]), second=0)
            if nxt <= t + timedelta(hours=2):
                nxt = t + timedelta(hours=r.randint(3, 8))
            if nxt > END:
                return
            app.events[-1].exited, app.events[-1].outcome = nxt, "passed"
            ev = Event(stage, nxt)
            app.events.append(ev)
            t = nxt
            if stage == "HIRED":
                app.status, app.closed = "hired", nxt
                return
            if stage == "HR_INTERVIEW":
                ev.interviewer = r.choice(HR_INTERVIEWERS)
            elif stage in ("TECH_INTERVIEW", "FINAL_INTERVIEW"):
                ev.interviewer = r.choice(INTERVIEWERS[dept])
            passed = r.random() < self.pass_prob(stage, app)
            if stage in ("HR_INTERVIEW", "TECH_INTERVIEW", "FINAL_INTERVIEW"):
                ev.score = round(r.uniform(3.5, 5) if passed else r.uniform(1.5, 3.2), 1)
            if stage == "TECH_INTERVIEW":
                ev.notes = r.choice(TECH_NOTES_PASS if passed else TECH_NOTES_FAIL).format(k=r.randint(3, 5) if passed
                                                                                          else r.randint(1, 2))
            if passed:
                continue
            decided = t + timedelta(days=r.uniform(0.5, 3))
            if decided > END:
                ev.outcome = "pending"
                return
            ev.exited = decided
            app.closed = decided
            if stage == "OFFER":
                app.status, ev.outcome = "withdrawn", "withdrawn"
                app.reason = r.choices([p[0] for p in OFFER_DECLINE], weights=[p[1] for p in OFFER_DECLINE])[0]
            elif stage == "HR_INTERVIEW" and r.random() < 0.12:
                app.status, ev.outcome = "rejected", "no_show"
                app.reason = r.choice(NO_SHOW_REASONS)
                ev.score = None
            else:
                app.status, ev.outcome = "rejected", "failed"
                app.reason = r.choice(REJECT_REASONS[stage])
            return

    # --------------------------------------------------------------- tổng hợp
    def build(self) -> list[App]:
        r = self.r
        apps: list[App] = []
        span = (END - START).total_seconds()
        codes, weights = zip(*POSITION_WEIGHTS.items())
        sources, sw = zip(*SOURCE_WEIGHTS.items())
        persons: list[Person] = []
        for i in range(N_APPLICATIONS):
            pos = r.choices(codes, weights=weights)[0]
            if persons and r.random() < 0.04:  # cùng ứng viên nộp thêm vị trí khác
                person = r.choice(persons)
                if any(a.person is person and a.pos == pos for a in apps):
                    continue
            else:
                person = self.person(len(persons) + 1, pos)
                persons.append(person)
            dept = self.positions[pos]["department"]
            src = r.choices(sources, weights=sw)[0]
            if src == "ITVIEC" and dept not in ("TECH", "DATA"):
                src = "TOPCV"
            # nhiều hồ sơ hơn vào giữa tháng 9 (đợt tuyển dụng lớn)
            offset = r.random() ** 0.9 * span
            applied = START + timedelta(seconds=offset)
            if r.random() < 0.18:
                applied = datetime(2026, 9, 8) + timedelta(days=r.uniform(0, 14))
            if applied.weekday() == 6:
                applied += timedelta(days=1)
            applied = applied.replace(hour=r.randint(7, 22), minute=r.randint(0, 59), second=r.randint(0, 59))
            lo, hi = SALARY_RANGE[pos]
            app = App(len(apps) + 1, person, pos, src, applied, round(r.uniform(lo, hi)))
            self.simulate(app)
            apps.append(app)
        # Vài nhận xét phỏng vấn có thiên vị (để minh hoạ bộ lọc thiên vị)
        interviews = [e for a in apps for e in a.events if e.stage in ("HR_INTERVIEW", "TECH_INTERVIEW")]
        for ev, note in zip(r.sample(interviews, k=len(BIASED_NOTES)), BIASED_NOTES):
            ev.notes = note
        return apps


# --------------------------------------------------------------------------- #
# Ghi file theo từng nguồn
# --------------------------------------------------------------------------- #
def fmt_phone(r: random.Random, phone: str) -> str | int:
    style = r.random()
    if style < 0.35:
        return phone
    if style < 0.55:
        return f"{phone[:4]} {phone[4:7]} {phone[7:]}"
    if style < 0.7:
        return "+84 " + phone[1:]
    if style < 0.85:
        return f"{phone[:4]}.{phone[4:7]}.{phone[7:]}"
    return int(phone)  # Excel làm mất số 0 đầu


def years_text(r: random.Random, years: float) -> str:
    if years == 0:
        return r.choice(["Chưa có kinh nghiệm", "Fresher", "0"])
    if years < 1:
        return "Dưới 1 năm"
    if years > 5 and r.random() < 0.5:
        return "Trên 5 năm"
    return r.choice([f"{years:g} năm", f"{years:g}".replace(".", ","), f"{int(years)}-{int(years) + 1} năm"])


def salary_text(r: random.Random, s: float) -> str:
    style = r.random()
    if style < 0.12:
        return "Thỏa thuận"
    if style < 0.4:
        return f"{s:g} triệu"
    if style < 0.6:
        return f"{s:g}tr"
    if style < 0.8:
        return f"{int(s * 1_000_000):,}".replace(",", ".")
    return f"{s:g}-{s + 3:g} triệu"


def write_cv_files(apps: list[App], out: Path, r: random.Random, gen: Generator) -> None:
    from docx import Document
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    font_dir = Path("/usr/share/fonts/truetype/dejavu")
    pdfmetrics.registerFont(TTFont("DejaVu", str(font_dir / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(font_dir / "DejaVuSans-Bold.ttf")))
    body = ParagraphStyle("b", fontName="DejaVu", fontSize=10, leading=14)
    head = ParagraphStyle("h", fontName="DejaVu-Bold", fontSize=12, leading=16, spaceBefore=6)
    name_style = ParagraphStyle("n", fontName="DejaVu-Bold", fontSize=18, leading=22)
    cv_dir = out / "cvs"
    cv_dir.mkdir(parents=True, exist_ok=True)
    done: set[int] = set()
    for app in apps:
        p = app.person
        if p.cv_file is None or p.pid in done:
            continue
        done.add(p.pid)
        p.cv_text = gen.cv_text(p, app.pos)
        path = cv_dir / p.cv_file
        if path.suffix == ".pdf":
            doc = SimpleDocTemplate(str(path), pagesize=A4, title=f"CV {p.full_name}")
            flow = []
            for i, line in enumerate(p.cv_text.splitlines()):
                if i == 0:
                    flow.append(Paragraph(line, name_style))
                elif line.isupper() and len(line) < 40:
                    flow.append(Paragraph(line, head))
                elif line:
                    flow.append(Paragraph(line.replace("&", "&amp;"), body))
                else:
                    flow.append(Spacer(1, 4))
            doc.build(flow)
        elif path.suffix == ".docx":
            document = Document()
            for i, line in enumerate(p.cv_text.splitlines()):
                if i == 0:
                    document.add_heading(line, level=0)
                elif line.isupper() and len(line) < 40:
                    document.add_heading(line, level=2)
                else:
                    document.add_paragraph(line)
            document.save(path)
        else:
            path.write_text(p.cv_text, encoding="utf-8")


def assign_systems(apps: list[App], r: random.Random, gen: Generator) -> None:
    for app in apps:
        dept = gen.positions[app.pos]["department"]
        primary = "ATS" if r.random() < (0.75 if dept in ("TECH", "DATA") else 0.25) else "EXCEL"
        systems = []
        if app.source in ("CAREER_SITE", "FACEBOOK", "JOB_FAIR", "REFERRAL") and r.random() < 0.85:
            systems.append("GOOGLE_FORM")
        if app.source == "DIRECT_EMAIL":
            systems.append("EMAIL")
        only_new = len(app.events) == 1 and app.applied > END - timedelta(days=10)
        if not (systems and only_new and r.random() < 0.6):
            systems.append(primary)
        if primary == "ATS" and r.random() < 0.05:
            systems.append("EXCEL")  # HR theo dõi trùng ở cả 2 nơi
        app.systems = systems
        needs_cv = "GOOGLE_FORM" in systems or "EMAIL" in systems or ("ATS" in systems and r.random() < 0.55)
        if needs_cv and app.person.cv_file is None:
            ext = r.choices([".pdf", ".docx", ".txt"], weights=[45, 25, 30])[0]
            slug = no_accent(app.person.full_name).replace(" ", "_")
            app.person.cv_file = f"CV_{slug}_{app.person.pid:03d}{ext}"


def ats_stage_name(code: str) -> str:
    return {"APPLIED": "Applied", "SCREENING": "CV Screening", "HR_INTERVIEW": "HR Interview",
            "TECH_INTERVIEW": "Technical Interview", "FINAL_INTERVIEW": "Final Interview", "OFFER": "Offer",
            "HIRED": "Hired"}[code]


def iso(dt: datetime | None) -> str | None:
    return dt.replace(tzinfo=VN).isoformat() if dt else None


def write_ats(apps: list[App], out: Path, r: random.Random, gen: Generator, stale: set[int]) -> int:
    jobs = [{"req_id": p["code"], "title": POSITION_TEXT[p["code"]][0], "department": p["department"],
             "headcount": p["headcount"], "status": "open", "location": p["location"], "description": p["jd"],
             "required_skills": p["required_skills"], "nice_to_have": p["nice_to_have_skills"],
             "opened_at": p["opened"].isoformat()} for p in POSITIONS]
    records = []
    for app in apps:
        if "ATS" not in app.systems:
            continue
        p = app.person
        is_stale = app.aid in stale
        status = "active" if is_stale else app.status
        stages = []
        for ev in app.events:
            exited, outcome = ev.exited, ev.outcome
            if is_stale and ev is app.events[-1]:
                exited, outcome = None, "pending"
            stages.append({"name": ats_stage_name(ev.stage), "entered_at": iso(ev.entered), "exited_at": iso(exited),
                           "result": outcome or "pending", "interviewer": ev.interviewer,
                           "score": f"{ev.score}/5" if ev.score else None, "notes": ev.notes})
        records.append({
            "id": f"ATS-{10000 + app.aid}",
            "candidate": {"first_name": p.given, "last_name": p.full_name.rsplit(" ", 1)[0],
                          "emails": [p.email.upper() if r.random() < 0.08 else p.email],
                          "phones": [str(fmt_phone(r, p.phone))],
                          "gender": {"Nam": "male", "Nữ": "female"}[p.gender] if r.random() < 0.7 else None,
                          "birth_date": p.dob.isoformat() if r.random() < 0.6 else None,
                          "location": {"TP. Hồ Chí Minh": "Ho Chi Minh City", "Hà Nội": "Hanoi"}.get(p.city, p.city),
                          "headline": p.title, "years_of_experience": p.years,
                          "education": {"Đại học": "Bachelor", "Thạc sĩ": "Master", "Cao đẳng": "College"}[p.education],
                          "resume_file": p.cv_file, "tags": p.skills[:4]},
            "job": {"req_id": app.pos, "title": POSITION_TEXT[app.pos][0]},
            "source": r.choice(SOURCE_TEXT[app.source]),
            "applied_at": iso(app.applied), "status": status,
            "current_stage": ats_stage_name(app.events[-1].stage),
            "closed_at": None if is_stale else iso(app.closed),
            "rejection_reason": None if is_stale else app.reason,
            "expected_salary": int(app.salary * 1_000_000),
            "stages": stages,
        })
    data = {"system": "SmartHire ATS (giả lập)", "exported_at": iso(END + timedelta(hours=1)), "jobs": jobs,
            "applications": records}
    (out / "ats_export.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(records)


def write_excel(apps: list[App], out: Path, r: random.Random, gen: Generator, stale: set[int]) -> int:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = "Pipeline Q3-Q4 2026"
    ws["A1"] = "BẢNG THEO DÕI TUYỂN DỤNG – QUÝ 3 & 4/2026"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = "Phòng Nhân sự cập nhật thủ công. Ngày cập nhật cuối: 07/11/2026"
    headers = ["STT", "Họ tên ứng viên", "Số ĐT", "Email", "Vị trí", "Nguồn", "Ngày nộp", "Ngày duyệt CV",
               "Ngày PV HR", "KQ PV HR", "Ngày PV chuyên môn", "KQ PV chuyên môn", "Người PV chuyên môn", "Điểm PV",
               "Ngày PV cuối", "KQ PV cuối", "Ngày gửi offer", "KQ offer", "Ngày nhận việc", "Trạng thái",
               "Lý do loại/rút", "Ngày cập nhật", "Ghi chú"]
    ws.append([])
    ws.append(headers)
    for cell in ws[4]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E79")
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    result_text = {"passed": "Đạt", "failed": "Không đạt", "no_show": "Vắng", "withdrawn": "Rút", "pending": None}
    status_text = {"active": "Đang xử lý", "rejected": "Loại", "withdrawn": "Rút hồ sơ", "hired": "Đã nhận việc"}

    def date_cell(dt: datetime | None):
        if dt is None:
            return None
        style = r.random()
        if style < 0.7:
            return dt.replace(second=0, microsecond=0)
        if style < 0.85:
            return dt.strftime("%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")

    rows = [a for a in apps if "EXCEL" in a.systems]
    dup = r.sample(rows, k=max(2, len(rows) // 35))  # dòng nhập trùng
    stt = 0
    for app in rows + dup:
        p = app.person
        ev = {e.stage: e for e in app.events}
        is_stale = app.aid in stale
        name = p.full_name
        if r.random() < 0.1:
            name = no_accent(name).upper()
        elif r.random() < 0.08:
            name = name.lower()
        stt += 1
        tech = ev.get("TECH_INTERVIEW")
        offer = ev.get("OFFER")
        last = app.events[-1]

        def res(stage):
            e = ev.get(stage)
            if not e:
                return None
            if is_stale and e is last:
                return None
            return result_text.get(e.outcome or "pending")

        ws.append([
            stt, name, fmt_phone(r, p.phone),
            (p.email.upper() if r.random() < 0.1 else p.email) if r.random() > 0.04 else None,
            r.choice(POSITION_TEXT[app.pos]), r.choice(SOURCE_TEXT[app.source]),
            date_cell(app.applied), date_cell(ev["SCREENING"].entered) if "SCREENING" in ev else None,
            date_cell(ev["HR_INTERVIEW"].entered) if "HR_INTERVIEW" in ev else None, res("HR_INTERVIEW"),
            date_cell(tech.entered) if tech else None, res("TECH_INTERVIEW"), tech.interviewer if tech else None,
            (f"{tech.score:g}/5" if r.random() < 0.5 else tech.score) if tech and tech.score else None,
            date_cell(ev["FINAL_INTERVIEW"].entered) if "FINAL_INTERVIEW" in ev else None, res("FINAL_INTERVIEW"),
            date_cell(offer.entered) if offer else None,
            ({"passed": "Chấp nhận", "withdrawn": "Từ chối"}.get(offer.outcome) if offer and not (is_stale and offer is last)
             else None),
            date_cell(ev["HIRED"].entered) if "HIRED" in ev else None,
            "Đang xử lý" if is_stale else status_text[app.status],
            None if is_stale else app.reason,
            date_cell(app.closed or last.entered) if not is_stale else date_cell(last.entered),
            tech.notes if tech else None,
        ])
    # Bản ghi lỗi để kiểm tra khâu làm sạch
    ws.append([stt + 1, "Trương Văn Bảo", "0903 111 222", "bao.truong91@gmail.com", "Bảo vệ tòa nhà", "Facebook",
               datetime(2026, 10, 20, 9, 0), None, None, None, None, None, None, None, None, None, None, None, None,
               "Đang xử lý", None, None, "Ứng tuyển sai kênh"])
    ws.append([stt + 2, None, "0987 654 321", None, "Data Analyst", "TopCV", "15/10/2026", None, None, None, None,
               None, None, None, None, None, None, None, None, "Đang xử lý", None, None, "Thiếu tên"])
    for col, width in zip("ABCDEFGHIJKLMNOPQRSTUVW", [5, 24, 15, 28, 24, 18] + [14] * 14 + [30, 14, 34]):
        ws.column_dimensions[col].width = width
    guide = wb.create_sheet("Hướng dẫn")
    guide["A1"] = "Quy ước nhập liệu"
    guide["A2"] = "KQ: Đạt / Không đạt / Vắng / Rút; Trạng thái: Đang xử lý / Loại / Rút hồ sơ / Đã nhận việc"
    wb.save(out / "hr_tracking.xlsx")
    return stt + 2


def write_form(apps: list[App], out: Path, r: random.Random, gen: Generator) -> int:
    headers = ["Dấu thời gian", "Họ và tên", "Địa chỉ email", "Số điện thoại", "Giới tính", "Ngày sinh",
               "Tỉnh/Thành phố đang sống", "Vị trí ứng tuyển", "Bạn biết đến tin tuyển dụng qua kênh nào?",
               "Số năm kinh nghiệm", "Trình độ học vấn", "Chức danh hiện tại", "Kỹ năng nổi bật",
               "Mức lương mong muốn", "Tải lên CV"]
    rows = []
    for app in apps:
        if "GOOGLE_FORM" not in app.systems:
            continue
        p = app.person
        submitted = app.applied - timedelta(minutes=r.randint(0, 50))
        rows.append([
            submitted.strftime("%d/%m/%Y %H:%M:%S"), p.full_name if r.random() > 0.1 else p.full_name.lower(),
            (" " + p.email.upper() + " ") if r.random() < 0.1 else p.email, str(fmt_phone(r, p.phone)), p.gender,
            p.dob.strftime("%d/%m/%Y"), p.city_raw, r.choice(POSITION_TEXT[app.pos]),
            FORM_SOURCE_OPTIONS[app.source], years_text(r, p.years),
            r.choice({"Đại học": ["Đại học", "Cử nhân", "Kỹ sư"], "Thạc sĩ": ["Thạc sĩ"], "Cao đẳng": ["Cao đẳng"]}
                     [p.education]),
            p.title, ", ".join(SKILL_TEXT.get(s, s) for s in p.skills), salary_text(r, app.salary),
            p.cv_file or "",
        ])
    rows.append(["21/10/2026 20:11:05", "Lê Hoàng Phúc", "khong co", "123", "Nam", "02/02/2001", "HCM",
                 "Data Analyst", "Facebook", "1 năm", "Đại học", "", "Excel", "10 triệu", ""])
    rows.append(["25/10/2026 10:02:44", "Nguyễn Thị Thu Hà", "thuha.nguyen02@gmail.com", "0938 222 444", "Nữ",
                 "11/11/2002", "Hà Nội", "Thực tập sinh Thiết kế đồ họa", "Website công ty", "Chưa có kinh nghiệm",
                 "Đại học", "Sinh viên", "Photoshop, Illustrator", "Thỏa thuận", ""])
    with open(out / "google_form_responses.csv", "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(headers)
        writer.writerows(rows)
    return len(rows)


def write_emails(apps: list[App], out: Path, r: random.Random, gen: Generator, stale: set[int]) -> int:
    mail_dir = out / "emails"
    mail_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for app in apps:
        p = app.person
        pos_text = r.choice(POSITION_TEXT[app.pos])
        if "EMAIL" in app.systems:
            msg = EmailMessage()
            msg["From"] = f"{p.full_name} <{p.email}>"
            msg["To"] = "tuyendung@talentlens.vn"
            msg["Subject"] = r.choice([f"[Ứng tuyển] {pos_text} - {p.full_name}", f"[Ung tuyen] {pos_text} - {p.full_name}"])
            msg["Date"] = format_datetime(app.applied.replace(tzinfo=VN))
            msg["Message-ID"] = f"<apply-{app.aid}@mail.talentlens.vn>"
            msg.set_content(
                f"Kính gửi Phòng Nhân sự,\n\nEm tên là {p.full_name}, em biết tin tuyển dụng vị trí {pos_text} qua "
                f"{r.choice(['website công ty', 'email giới thiệu', 'TopCV'])}. Em có {p.years:g} năm kinh nghiệm ở vị trí "
                f"{p.title}.\nSĐT: {fmt_phone(r, p.phone)}\nEm gửi kèm CV, mong anh/chị xem xét.\n\nTrân trọng,\n{p.full_name}\n")
            if p.cv_file and (out / "cvs" / p.cv_file).exists():
                data = (out / "cvs" / p.cv_file).read_bytes()
                mime = {".pdf": ("application", "pdf"), ".txt": ("text", "plain"),
                        ".docx": ("application", "vnd.openxmlformats-officedocument.wordprocessingml.document")}
                maintype, subtype = mime[Path(p.cv_file).suffix]
                if maintype == "text":
                    msg.add_attachment(data.decode("utf-8"), subtype=subtype, filename=p.cv_file)
                else:
                    msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=p.cv_file)
            count += 1
            (mail_dir / f"{count:03d}_ung_tuyen_{no_accent(p.given).lower()}.eml").write_bytes(bytes(msg))
        if app.aid in stale:
            msg = EmailMessage()
            msg["From"] = f"{p.full_name} <{p.email}>"
            msg["To"] = "tuyendung@talentlens.vn"
            msg["Subject"] = f"Xin rút hồ sơ ứng tuyển vị trí {pos_text}"
            msg["Date"] = format_datetime(app.closed.replace(tzinfo=VN))
            msg["Message-ID"] = f"<withdraw-{app.aid}@mail.talentlens.vn>"
            msg.set_content(f"Chào anh/chị,\n\nEm là {p.full_name}. Em xin phép rút hồ sơ ứng tuyển vị trí {pos_text} "
                            f"vì {app.reason[0].lower() + app.reason[1:]}.\nCảm ơn anh/chị đã dành thời gian.\n\n{p.full_name}\n")
            count += 1
            (mail_dir / f"{count:03d}_rut_ho_so_{no_accent(p.given).lower()}.eml").write_bytes(bytes(msg))
    # email rút hồ sơ không khớp ai (kiểm tra khâu đối soát)
    msg = EmailMessage()
    msg["From"] = "Pham Gia Bao <giabao.pham@gmail.com>"
    msg["To"] = "tuyendung@talentlens.vn"
    msg["Subject"] = "Xin rút hồ sơ ứng tuyển vị trí Data Engineer"
    msg["Date"] = format_datetime(datetime(2026, 10, 30, 9, 12, tzinfo=VN))
    msg.set_content("Em xin rút hồ sơ vị trí Data Engineer vì lý do cá nhân. Cảm ơn anh/chị.")
    count += 1
    (mail_dir / f"{count:03d}_rut_ho_so_khong_khop.eml").write_bytes(bytes(msg))
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    out: Path = args.out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    gen = Generator(args.seed)
    r = gen.r
    apps = gen.build()
    assign_systems(apps, r, gen)
    # Ứng viên rút hồ sơ chỉ báo qua email: hệ thống theo dõi (ATS/Excel) chưa được cập nhật
    stale = {a.aid for a in apps if a.status == "withdrawn" and a.reason and r.random() < 0.45
             and ("ATS" in a.systems or "EXCEL" in a.systems)}
    write_cv_files(apps, out, r, gen)
    n_ats = write_ats(apps, out, r, gen, stale)
    n_xls = write_excel(apps, out, r, gen, stale)
    n_form = write_form(apps, out, r, gen)
    n_mail = write_emails(apps, out, r, gen, stale)
    n_cv = len(list((out / "cvs").iterdir()))
    persons = {a.person.pid for a in apps}
    status = {}
    for a in apps:
        status[a.status] = status.get(a.status, 0) + 1
    print(f"Ứng viên thực: {len(persons)} | Hồ sơ ứng tuyển thực: {len(apps)} | Trạng thái: {status}")
    print(f"ATS: {n_ats} hồ sơ | Excel: {n_xls} dòng | Google Form: {n_form} dòng | Email: {n_mail} | CV: {n_cv}")
    print(f"Đã ghi dữ liệu mẫu vào {out}")


if __name__ == "__main__":
    main()
