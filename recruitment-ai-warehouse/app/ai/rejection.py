"""Phân loại lý do loại / rút hồ sơ (NLP dựa trên luật từ khoá tiếng Việt + Anh)."""
from __future__ import annotations

from app.utils import normalize_key

# Thứ tự quan trọng: nhóm cụ thể đứng trước nhóm chung
REJECTION_CATEGORIES: list[tuple[str, str, list[str]]] = [
    ("OTHER_OFFER", "Nhận offer nơi khác",
     ["offer khac", "offer noi khac", "cong ty khac", "nhan viec noi khac", "other offer", "counter offer",
      "da nhan viec", "nhan loi moi khac", "ben khac"]),
    ("SALARY", "Kỳ vọng lương/phúc lợi chưa phù hợp",
     ["muc luong", "ky vong luong", "luong mong muon", "luong thap", "luong cao", "luong chua", "luong khong",
      "ve luong", "deal luong", "luong offer", "salary", "thu nhap", "dai ngo", "phuc loi", "budget", "ngan sach",
      "muc offer thap", "compensation"]),
    ("SLOW_PROCESS", "Quy trình tuyển dụng kéo dài",
     ["cho lau", "qua lau", "keo dai", "cham phan hoi", "khong co phan hoi", "doi lau", "cho doi"]),
    ("NO_RESPONSE", "Không phản hồi / vắng mặt phỏng vấn",
     ["khong phan hoi", "khong lien lac", "khong nghe may", "no show", "vang mat", "khong den", "ghost",
      "mat lien lac", "khong tra loi"]),
    ("POSITION_CLOSED", "Vị trí đã đóng / đủ người",
     ["da du nguoi", "dong tuyen", "huy tuyen", "position closed", "headcount", "tam dung tuyen", "da tuyen du"]),
    ("LANGUAGE", "Ngoại ngữ chưa đạt yêu cầu",
     ["tieng anh", "english", "ngoai ngu", "ielts", "toeic", "tieng nhat"]),
    ("COMMUNICATION", "Kỹ năng giao tiếp / trình bày",
     ["giao tiep", "trinh bay", "communication", "thuyet trinh", "dien dat"]),
    ("SKILL_GAP", "Thiếu kỹ năng chuyên môn",
     ["ky nang", "chuyen mon", "kien thuc", "technical", "skill", "bai test", "coding", "khong dat test",
      "chua nam vung", "yeu ve", "thieu kien thuc", "sql", "python", "logic"]),
    ("EXPERIENCE", "Kinh nghiệm chưa phù hợp",
     ["kinh nghiem", "experience", "chua du", "junior", "overqualified", "qua cao so voi vi tri", "senior"]),
    ("CULTURE_FIT", "Phù hợp văn hoá / thái độ",
     ["van hoa", "culture", "thai do", "attitude", "dinh huong", "khong gan bo", "dong luc"]),
    ("LOCATION_SCHEDULE", "Địa điểm / thời gian làm việc",
     ["dia diem", "location", "xa nha", "di chuyen", "chuyen noi", "ca lam", "thoi gian lam viec", "onsite",
      "remote", "lam tu xa", "khong the di lam"]),
    ("PERSONAL", "Lý do cá nhân",
     ["ca nhan", "personal", "gia dinh", "suc khoe", "du hoc", "hoc tiep"]),
]

CATEGORY_LABELS = {code: label for code, label, _ in REJECTION_CATEGORIES} | {"OTHER": "Lý do khác"}

RECOMMENDATIONS = {
    "OTHER_OFFER": "Rút ngắn thời gian giữa các vòng và gửi offer sớm hơn; duy trì liên lạc chủ động với ứng viên tốt.",
    "SALARY": "Rà soát khung lương so với thị trường; công bố dải lương trong JD để sàng lọc kỳ vọng từ đầu.",
    "SLOW_PROCESS": "Đặt SLA cho từng vòng, cảnh báo hồ sơ quá hạn và cập nhật tiến độ cho ứng viên mỗi tuần.",
    "NO_RESPONSE": "Nhắc lịch tự động qua email/Zalo trước 24h; xác nhận lịch phỏng vấn bằng 1 click.",
    "POSITION_CLOSED": "Đồng bộ trạng thái vị trí với các kênh đăng tuyển; thông báo kịp thời cho ứng viên.",
    "LANGUAGE": "Ghi rõ yêu cầu ngoại ngữ trong JD và thêm câu hỏi sàng lọc ở form ứng tuyển.",
    "SKILL_GAP": "Bổ sung câu hỏi sàng lọc kỹ thuật ở form/ATS; cân nhắc bài test ngắn trước vòng chuyên môn.",
    "EXPERIENCE": "Làm rõ cấp độ (level) trong JD; phân luồng ứng viên junior sang vị trí phù hợp.",
    "COMMUNICATION": "Chuẩn hoá tiêu chí chấm giao tiếp trong scorecard để giảm cảm tính.",
    "CULTURE_FIT": "Tiêu chí 'phù hợp văn hoá' dễ gây thiên vị – cần mô tả hành vi cụ thể và kiểm duyệt nhận xét.",
    "LOCATION_SCHEDULE": "Nêu rõ địa điểm, chế độ hybrid/remote ngay trong tin tuyển dụng.",
    "PERSONAL": "Không can thiệp lý do cá nhân; giữ liên hệ để mời lại khi phù hợp (talent pool).",
    "OTHER": "Yêu cầu người phỏng vấn ghi lý do cụ thể hơn để phân tích chính xác.",
}


def classify_reason(text: str | None) -> str | None:
    """Trả về mã nhóm lý do; None nếu không có lý do."""
    key = normalize_key(text)
    if not key:
        return None
    padded = f" {key} "
    for code, _label, keywords in REJECTION_CATEGORIES:
        if any(f" {kw} " in padded for kw in keywords):
            return code
    return "OTHER"
