"""Kiểm thử NLP/AI: kỹ năng, ẩn danh, bộ lọc thiên vị, phân loại lý do, engine Claude (giả lập client)."""
import json
from types import SimpleNamespace

from app.ai.anonymizer import anonymize_text
from app.ai.bias_guard import scan_object, scan_text
from app.ai.claude_engine import ClaudeEngine
from app.ai.local_engine import LocalEngine
from app.ai.rejection import classify_reason
from app.ai.skills import extract_skills, group_skills, match_jd

CV = """NGUYỄN VĂN AN
Data Analyst
Ngày sinh: 15/03/1998 | Giới tính: Nam
Điện thoại: 0912 345 678 | Email: an.nguyen98@gmail.com
Địa chỉ: Quận 7, TP. Hồ Chí Minh
Tình trạng hôn nhân: Độc thân

KINH NGHIỆM LÀM VIỆC
Tổng kinh nghiệm: 3 năm
Công ty TNHH Minh Phát (03/2023 – nay) – Data Analyst
- Xây dựng 12 dashboard Power BI theo dõi doanh thu cho ban giám đốc
- Viết truy vấn SQL tổng hợp dữ liệu bán hàng, giảm 40% thời gian lập báo cáo tuần

HỌC VẤN
ĐH Kinh tế TP.HCM – Đại học Hệ thống thông tin quản lý

KỸ NĂNG
- SQL, Python (Pandas), Excel nâng cao
- Giao tiếp, Làm việc nhóm
"""
POSITION = {"title": "Data Analyst", "department_code": "DATA", "required_skills": ["SQL", "Python", "Power BI",
            "Excel", "Thống kê"], "nice_to_have_skills": ["Tableau", "Pandas"], "jd_text": "Phân tích dữ liệu SQL"}


def test_extract_and_group_skills():
    skills = extract_skills(CV)
    for s in ["SQL", "Python", "Power BI", "Excel", "Pandas", "Giao tiếp", "Làm việc nhóm"]:
        assert s in skills
    assert "Bán hàng B2B" not in skills  # "dữ liệu bán hàng" không phải kỹ năng bán hàng
    assert "Java" not in extract_skills("JavaScript, TypeScript")
    groups = group_skills(skills)
    assert "SQL" in groups["Dữ liệu & BI"] and "Python" in groups["Ngôn ngữ lập trình"]
    jd = match_jd(skills, POSITION["required_skills"])
    assert jd["required_coverage_pct"] == 80 and jd["missing_required"] == ["Thống kê"]


def test_anonymizer_removes_protected_attributes():
    text, removed = anonymize_text(CV, names=["Nguyễn Văn An"])
    for leaked in ["0912", "an.nguyen98", "15/03/1998", "Nam", "Độc thân", "Quận 7", "NGUYỄN VĂN AN"]:
        assert leaked not in text, leaked
    assert {"ho_ten", "ngay_sinh", "lien_he", "dia_chi", "hon_nhan"} <= set(removed)
    assert "Power BI" in text  # nội dung nghề nghiệp được giữ nguyên


def test_bias_guard():
    flags = scan_text("Ứng viên nữ, đã lập gia đình và có con nhỏ nên khó tăng ca")
    cats = {f["category"] for f in flags}
    assert {"Giới tính", "Hôn nhân / Thai sản"} <= cats
    assert scan_text("Giọng miền Trung hơi khó nghe")[0]["category"] == "Vùng miền / Quê quán"
    assert scan_text("Ứng viên giải tốt bài SQL, tư duy logic rõ ràng") == []
    assert scan_text("Báo giá dịch vụ năm 2026") == []  # 'giá', 'năm' không bị nhầm
    assert scan_object({"a": ["ok", {"b": "ngoại hình ưa nhìn"}]})


def test_rejection_classifier():
    assert classify_reason("Kỳ vọng mức lương cao hơn ngân sách") == "SALARY"
    assert classify_reason("Ứng viên nhận offer công ty khác") == "OTHER_OFFER"
    assert classify_reason("Kỹ năng giao tiếp chưa tốt") == "COMMUNICATION"
    assert classify_reason("Không đạt bài test chuyên môn") == "SKILL_GAP"
    assert classify_reason("Chất lượng bài test chưa tốt") == "SKILL_GAP"  # 'chất lượng' ≠ lương
    assert classify_reason("Chờ lâu không có phản hồi nên không tiếp tục") == "SLOW_PROCESS"
    assert classify_reason("Không thể đi làm onsite tại văn phòng") == "LOCATION_SCHEDULE"
    assert classify_reason("abc") == "OTHER"
    assert classify_reason(None) is None


def test_local_engine_outputs():
    engine = LocalEngine()
    anon, _ = anonymize_text(CV, names=["Nguyễn Văn An"])
    result = engine.analyze_cv(anon, POSITION)
    assert result["experience_years"] == 3.0
    assert result["jd_match"]["required_coverage_pct"] == 80
    assert any("Power BI" in h for h in result["highlights"])
    assert scan_object({k: result[k] for k in ["headline", "summary", "highlights", "gaps"]}) == []
    questions = engine.interview_questions(POSITION, result)
    cats = {q["category"] for q in questions["questions"]}
    assert {"Chuyên môn", "Làm rõ yêu cầu JD", "Tình huống", "Hành vi (STAR)"} <= cats
    assert questions["avoid_topics"]


class FakeMessages:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(stop_reason="end_turn",
                               content=[SimpleNamespace(type="text", text=json.dumps(self.payload, ensure_ascii=False))])


def test_claude_engine_request_shape_and_merge():
    payload = {"headline": "DA 3 năm", "summary": "Tóm tắt", "highlights": ["12 dashboard"],
               "skills": ["SQL", "Tableau"], "gaps": ["Cần làm rõ thống kê"]}
    fake = FakeMessages(payload)
    client = SimpleNamespace(beta=SimpleNamespace(messages=fake), messages=fake)
    engine = ClaudeEngine("test-key", "claude-opus-5-5", "medium", client=client)
    anon, _ = anonymize_text(CV, names=["Nguyễn Văn An"])
    result = engine.analyze_cv(anon, POSITION)
    call = fake.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["fallbacks"] == "default" and "server-side-fallback-2026-07-01" in call["betas"]
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert "0912" not in call["messages"][0]["content"]  # dữ liệu gửi đi đã ẩn danh
    assert result["headline"] == "DA 3 năm"
    assert "Tableau" in result["skills"]  # hợp nhất kỹ năng AI nêu + từ điển
    assert result["jd_match"]["required_coverage_pct"] == 80
