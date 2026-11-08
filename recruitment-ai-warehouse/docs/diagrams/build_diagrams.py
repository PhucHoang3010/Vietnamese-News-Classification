"""Vẽ các sơ đồ (SVG) cho báo cáo rồi xuất PNG bằng Playwright.

Chạy: python docs/diagrams/build_diagrams.py  → docs/images/*.svg, *.png
"""
from __future__ import annotations

import html
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "images"
OUT.mkdir(parents=True, exist_ok=True)

INK, INK2, MUTED, LINE = "#0b0b0b", "#3d3c39", "#6b6a66", "#8a8984"
BLUE, BLUE_BG, BLUE_D = "#2a78d6", "#eaf2fc", "#184f95"
ORANGE, ORANGE_BG = "#d95926", "#fdf0ea"
GREEN, GREEN_BG = "#0e7a4f", "#e8f6ef"
VIOLET, VIOLET_BG = "#5544c4", "#efedfb"
GRAY_BG = "#f4f4f1"
FONT = "Inter, 'Noto Sans', 'DejaVu Sans', sans-serif"


class Svg:
    def __init__(self, w: int, h: int):
        self.w, self.h, self.parts = w, h, []

    def add(self, s: str):
        self.parts.append(s)

    def text(self, x, y, s, size=14, weight=400, color=INK, anchor="start", italic=False):
        style = "font-style:italic;" if italic else ""
        self.add(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" '
                 f'text-anchor="{anchor}" style="{style}">{html.escape(s)}</text>')

    def box(self, x, y, w, h, title=None, lines=(), fill="#fff", stroke=LINE, title_color=INK, size=13,
            radius=10, title_size=14, center=False, dash=False):
        d = ' stroke-dasharray="6 5"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="1.5"{d}/>')
        cy = y + 24
        if title:
            if center:
                self.text(x + w / 2, cy, title, title_size, 700, title_color, "middle")
            else:
                self.text(x + 12, cy, title, title_size, 700, title_color)
            cy += 21
        for line in lines:
            if center:
                self.text(x + w / 2, cy, line, size, 400, INK2, "middle")
            else:
                self.text(x + 12, cy, line, size, 400, INK2)
            cy += size + 6

    def group(self, x, y, w, h, label, fill=GRAY_BG, stroke="#d9d8d2", color=MUTED):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="1.2"/>')
        self.text(x + 14, y + 22, label.upper(), 12, 700, color)

    def arrow(self, pts, label=None, color=LINE, dash=False, lx=None, ly=None, width=1.8):
        d = "M " + " L ".join(f"{a},{b}" for a, b in pts)
        dash_attr = ' stroke-dasharray="6 5"' if dash else ""
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash_attr} '
                 f'marker-end="url(#arrow)"/>')
        if label:
            (x1, y1), (x2, y2) = pts[-2], pts[-1]
            self.text(lx if lx is not None else (x1 + x2) / 2, ly if ly is not None else (y1 + y2) / 2 - 6, label,
                      12, 500, MUTED, "middle")

    def line(self, pts, color=LINE, width=1.5, dash=False):
        d = "M " + " L ".join(f"{a},{b}" for a, b in pts)
        dash_attr = ' stroke-dasharray="5 4"' if dash else ""
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash_attr}/>')

    def render(self) -> str:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">'
                f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
                f'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{LINE}"/></marker></defs>'
                f'<rect width="100%" height="100%" fill="#ffffff"/>' + "".join(self.parts) + "</svg>")


# --------------------------------------------------------------------------- #
def architecture() -> Svg:
    s = Svg(1560, 760)
    s.text(780, 36, "Kiến trúc tổng thể hệ thống TalentLens", 22, 700, INK, "middle")
    # Nguồn
    s.group(20, 60, 250, 600, "1. Nguồn dữ liệu rời rạc")
    srcs = [("Google Form", [".csv – form ứng tuyển"]), ("Email tuyển dụng", [".eml – ứng tuyển / rút hồ sơ"]),
            ("ATS", [".json – vị trí, hồ sơ, vòng"]), ("Excel HR", [".xlsx – bảng theo dõi"]),
            ("File CV", ["PDF / DOCX / TXT"])]
    for i, (t, l) in enumerate(srcs):
        s.box(38, 100 + i * 108, 214, 82, t, l, fill="#fff", stroke="#c9c8c1")
    # ETL
    s.group(310, 60, 270, 600, "2. ETL bằng Python")
    etl = [("Extract", ["pandas, openpyxl, email,", "pypdf, python-docx"]),
           ("Staging & lineage", ["stg_raw_record + vân tay SHA-256", "→ nạp lại không trùng"]),
           ("Transform", ["Chuẩn hoá tên, SĐT, email, ngày,", "vị trí, nguồn, vòng, trạng thái"]),
           ("Định danh & khử trùng", ["email → SĐT → họ tên + ngày sinh"]),
           ("Load + hậu xử lý", ["dim/fact, thời lượng vòng,", "kỹ năng, lý do rớt (NLP)"])]
    for i, (t, l) in enumerate(etl):
        s.box(328, 100 + i * 108, 234, 82, t, l, fill=ORANGE_BG, stroke=ORANGE, title_color="#8a3a17")
        if i < 4:
            s.arrow([(445, 182 + i * 108), (445, 206 + i * 108)])
    for i in range(5):
        s.arrow([(252, 141 + i * 108), (326, 141 + i * 108)] if i == 0 else [(252, 141 + i * 108), (300, 141 + i * 108),
                                                                            (300, 141), (326, 141)])
    # DWH
    s.group(620, 60, 300, 600, "3. Kho dữ liệu PostgreSQL")
    s.box(638, 100, 264, 74, "Staging", ["stg_raw_record (bản ghi thô)", "etl_run (log ETL)"], fill="#fff")
    s.box(638, 186, 264, 140, "Bảng chiều (Dimension)", ["dim_candidate · dim_position", "dim_source · dim_stage",
                                                         "dim_date · dim_department"], fill=BLUE_BG, stroke=BLUE,
          title_color=BLUE_D)
    s.box(638, 338, 264, 100, "Bảng sự kiện (Fact)", ["fact_application", "fact_stage_event"], fill=BLUE_BG,
          stroke=BLUE, title_color=BLUE_D)
    s.box(638, 450, 264, 120, "Bảng vận hành", ["app_user (RBAC) · audit_log", "ai_insight (kiểm duyệt)",
                                                "weekly_report"], fill="#fff")
    s.arrow([(562, 549), (600, 549), (600, 260), (636, 260)], "Load", lx=588, ly=410)
    s.arrow([(562, 249), (636, 137)])
    # API
    s.group(960, 60, 280, 600, "4. Backend FastAPI (REST)")
    api = [("Xác thực JWT + RBAC", ["admin · hr · hiring_manager", "che dữ liệu cá nhân (masking)"]),
           ("Analytics (pandas)", ["phễu, chuyển đổi, thời gian,", "điểm nghẽn, nguồn, công bằng"]),
           ("AI Service", ["ẩn danh → Claude / NLP nội bộ", "→ bias guard → chờ duyệt"]),
           ("Báo cáo tuần", ["số liệu + nhận định AI", "Markdown / HTML"]),
           ("ETL API", ["tải tệp, chạy ETL, xem log"])]
    for i, (t, l) in enumerate(api):
        s.box(978, 100 + i * 108, 244, 82, t, l, fill=GREEN_BG, stroke=GREEN, title_color=GREEN)
    s.arrow([(902, 390), (976, 390)], "SQLAlchemy", ly=380)
    s.arrow([(976, 300), (902, 300)])
    # AI
    s.box(980, 680, 240, 62, "Claude API (Anthropic)", ["structured outputs · fallback"], fill=VIOLET_BG,
          stroke=VIOLET, title_color=VIOLET, center=True)
    s.arrow([(1100, 682), (1100, 666)])
    s.line([(1100, 666), (1100, 662)])
    # UI
    s.group(1280, 60, 260, 600, "5. Giao diện Streamlit")
    ui = [("Dashboard pipeline", ["Plotly: phễu, SLA, nguồn"]), ("Ứng viên & hồ sơ", ["hành trình, CV, nhận xét"]),
          ("AI phân tích CV", ["tóm tắt, kỹ năng, câu hỏi"]), ("Kiểm duyệt AI · Báo cáo", ["duyệt / sửa / từ chối"]),
          ("ETL · Người dùng · Nhật ký", ["quản trị hệ thống"])]
    for i, (t, l) in enumerate(ui):
        s.box(1298, 100 + i * 108, 224, 82, t, l, fill="#fff", stroke="#c9c8c1")
    s.arrow([(1222, 360), (1296, 360)])
    s.text(1259, 312, "HTTPS", 12, 500, MUTED, "middle")
    s.text(1259, 326, "JSON", 12, 500, MUTED, "middle")
    s.arrow([(1296, 330), (1222, 330)])
    s.text(1410, 700, "Người dùng: HR · Hiring manager · Admin", 13, 600, INK2, "middle")
    s.text(1410, 722, "(trình duyệt, URL công khai)", 12, 400, MUTED, "middle")
    return s


def etl_flow() -> Svg:
    s = Svg(1560, 470)
    s.text(780, 36, "Quy trình ETL đa nguồn và khử trùng ứng viên", 22, 700, INK, "middle")
    steps = [("1. Extract", ["Đọc CSV, JSON, XLSX", "(tự dò dòng tiêu đề),", ".eml + CV đính kèm"]),
             ("2. Staging", ["Lưu bản ghi thô +", "vân tay SHA-256;", "bỏ qua bản ghi đã nạp"]),
             ("3. Transform", ["Chuẩn hoá tên, email,", "SĐT (0xxxxxxxxx), ngày,", "vị trí/nguồn/vòng/trạng thái"]),
             ("4. Validate", ["Bắt buộc: họ tên,", "email hoặc SĐT, vị trí,", "ngày nộp hợp lệ"]),
             ("5. Định danh", ["Khớp email → SĐT →", "họ tên + ngày sinh;", "gộp thông tin thiếu"]),
             ("6. Load", ["Upsert dim_*, gộp hồ sơ", "(ứng viên, vị trí) duy nhất,", "gộp sự kiện từng vòng"]),
             ("7. Hậu xử lý", ["Thời lượng vòng, vòng", "hiện tại, kỹ năng (NLP),", "lý do rớt, cờ thiên vị"])]
    w, gap, x0, y = 196, 22, 22, 90
    for i, (t, l) in enumerate(steps):
        x = x0 + i * (w + gap)
        s.box(x, y, w, 132, t, l, fill=ORANGE_BG if i in (2, 3, 4) else BLUE_BG,
              stroke=ORANGE if i in (2, 3, 4) else BLUE, title_color="#8a3a17" if i in (2, 3, 4) else BLUE_D)
        if i < len(steps) - 1:
            s.arrow([(x + w, y + 66), (x + w + gap - 2, y + 66)])
    xv = x0 + 3 * (w + gap) + w / 2
    s.arrow([(xv, y + 132), (xv, 300)], "không hợp lệ", lx=xv + 52, ly=272)
    s.box(xv - 150, 302, 300, 74, "Bản ghi bị loại", ["stg_raw_record.status = 'rejected'", "+ lý do, hiển thị trên web"],
          fill="#fff6f1", stroke=ORANGE, title_color="#8a3a17")
    s.box(1100, 302, 438, 136, "etl_run – nhật ký mỗi lần chạy", [
        "START / EXTRACT / TRANSFORM / LOAD / NLP / DONE",
        "Số bản ghi: thô, hợp lệ, bị loại, bỏ qua (đã nạp)",
        "Ứng viên mới, bản ghi trùng đã gộp (theo email/SĐT/…)",
        "Trạng thái: success · partial · failed"], fill=GRAY_BG)
    s.arrow([(x0 + 6 * (w + gap) + w / 2, y + 132), (x0 + 6 * (w + gap) + w / 2, 300)])
    s.box(22, 302, 420, 136, "Ví dụ dữ liệu bẩn được làm sạch", [
        "'+84 912 345 678', '912345678' → 0912345678",
        "'NGUYEN VAN AN' ↔ 'Nguyễn Văn An' (cùng email)",
        "'DA', 'Data analyst (Junior)' → DA-2026",
        "'topcv.vn', 'Top CV' → TOPCV"], fill="#fff")
    return s


def erd() -> Svg:
    s = Svg(1560, 900)
    s.text(780, 36, "Mô hình kho dữ liệu tuyển dụng – lược đồ hình sao (Star Schema)", 22, 700, INK, "middle")

    def table(x, y, name, cols, kind="dim", w=260):
        fill, stroke, tc = {"dim": (BLUE_BG, BLUE, BLUE_D), "fact": (ORANGE_BG, ORANGE, "#8a3a17"),
                            "app": (GREEN_BG, GREEN, GREEN), "stg": (GRAY_BG, "#a9a8a2", INK2)}[kind]
        h = 36 + 21 * len(cols) + 8
        s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#ffffff" stroke="{stroke}" stroke-width="1.6"/>')
        s.add(f'<path d="M {x} {y + 8} a 8 8 0 0 1 8 -8 h {w - 16} a 8 8 0 0 1 8 8 v 26 h {-w} z" fill="{fill}"/>')
        s.text(x + 12, y + 23, name, 14, 700, tc)
        for i, c in enumerate(cols):
            key = c.split(" ")[0] if c.split(" ")[0] in ("PK", "FK", "UK") else ""
            label = c[len(key):].strip() if key else c
            if key:
                s.text(x + 12, y + 54 + i * 21, key, 11, 700, ORANGE if key == "FK" else BLUE_D)
            s.text(x + 44, y + 54 + i * 21, label, 12.5, 400, INK2)
        return (x, y, w, h)

    fa = table(560, 300, "fact_application", ["PK id", "UK application_code", "FK candidate_id", "FK position_id",
               "FK source_id", "FK applied_date_key", "FK current_stage_id", "applied_at, closed_at",
               "status (active/hired/…)", "rejection_reason, rejection_category", "expected_salary",
               "source_systems, external_ids"], "fact", 300)
    fe = table(980, 330, "fact_stage_event", ["PK id", "FK application_id", "FK stage_id", "entered_at, exited_at",
               "outcome (passed/failed/…)", "duration_hours", "interviewer, score", "feedback, bias_flags"], "fact")
    dc = table(140, 120, "dim_candidate", ["PK id", "UK candidate_code", "full_name, email, phone",
               "gender, date_of_birth, city  (nhạy cảm)", "years_experience, education", "skills, skill_groups",
               "cv_text, merged_identities"], "dim", 300)
    dp = table(560, 70, "dim_position", ["PK id", "UK code", "title, level, location", "FK department_id",
               "FK hiring_manager_id", "jd_text, required_skills", "headcount, status"], "dim", 300)
    dd = table(980, 80, "dim_department", ["PK id", "UK code", "name"], "dim")
    ds = table(140, 470, "dim_source", ["PK id", "UK code", "name, channel"], "dim", 300)
    dt = table(140, 640, "dim_date", ["PK date_key (YYYYMMDD)", "full_date, day, month", "quarter, year, iso_week",
               "week_start, is_weekend"], "dim", 300)
    st_ = table(1290, 360, "dim_stage", ["PK id", "UK code", "name, stage_order", "sla_days, is_terminal"], "dim", 250)
    us = table(1290, 100, "app_user", ["PK id", "UK username", "hashed_password", "role (RBAC)", "FK department_id"],
               "app", 250)
    ai = table(560, 650, "ai_insight", ["PK id", "FK candidate_id / application_id", "insight_type, content (JSON)",
               "provider, model_name", "status (pending/approved)", "bias_flags, removed_fields",
               "FK created_by, reviewed_by"], "app", 300)
    table(980, 640, "stg_raw_record / etl_run", ["stg: source, file, fingerprint", "payload (JSON), status, error",
          "etl_run: stats, log"], "stg", 300)
    table(1290, 560, "weekly_report · audit_log", ["metrics, narrative, status", "action, entity, detail"], "app", 250)

    def link(p1, p2, n1="n", n2="1"):
        s.line([p1, p2], color="#9d9c96", width=1.6)
        s.text(p1[0] + (6 if p2[0] > p1[0] else -14), p1[1] - 6, n1, 12, 700, MUTED)
        s.text(p2[0] + (-14 if p2[0] > p1[0] else 6), p2[1] - 6, n2, 12, 700, MUTED)

    link((560, 380), (440, 230))            # candidate
    link((710, 300), (710, 262))            # position
    link((560, 430), (440, 510))            # source
    link((560, 470), (440, 690))            # date
    link((980, 400), (860, 400), "n", "1")  # event -> application
    link((1240, 420), (1290, 420))          # event -> stage
    link((860, 140), (980, 120), "n", "1")  # position -> department
    link((860, 170), (1290, 160))           # position -> hiring manager
    link((710, 650), (710, 597), "n", "1")  # ai -> application
    s.text(780, 880, "Màu cam: bảng sự kiện (fact) · xanh dương: bảng chiều (dimension) · xanh lá: bảng vận hành · "
                     "xám: staging", 13, 400, MUTED, "middle")
    return s


def ai_flow() -> Svg:
    s = Svg(1560, 430)
    s.text(780, 36, "Quy trình AI có kiểm duyệt và chống thiên vị (human-in-the-loop)", 22, 700, INK, "middle")
    steps = [("CV / hồ sơ", ["PDF, DOCX, TXT", "hoặc dữ liệu kho"], "#fff", LINE, INK),
             ("Trích văn bản", ["pypdf, python-docx,", "tách mục CV"], BLUE_BG, BLUE, BLUE_D),
             ("Ẩn danh hoá", ["bỏ tên, email, SĐT, ngày", "sinh, giới tính, hôn nhân,", "địa chỉ, tôn giáo…"],
              ORANGE_BG, ORANGE, "#8a3a17"),
             ("AI engine", ["Claude (JSON Schema)", "hoặc NLP nội bộ", "– không chấm điểm người"], VIOLET_BG, VIOLET,
              VIOLET),
             ("Bias guard", ["quét nội dung theo 7", "nhóm thuộc tính", "được bảo vệ → gắn cờ"], ORANGE_BG, ORANGE,
              "#8a3a17"),
             ("Chờ duyệt", ["ai_insight.status =", "pending_review"], GRAY_BG, "#a9a8a2", INK2),
             ("HR kiểm duyệt", ["duyệt / sửa / từ chối;", "cờ thiên vị bắt buộc", "ghi chú"], GREEN_BG, GREEN, GREEN)]
    w, gap, x0, y = 196, 22, 22, 80
    for i, (t, l, f, st_, tc) in enumerate(steps):
        x = x0 + i * (w + gap)
        s.box(x, y, w, 120, t, l, fill=f, stroke=st_, title_color=tc)
        if i < len(steps) - 1:
            s.arrow([(x + w, y + 60), (x + w + gap - 2, y + 60)])
    xg = x0 + 6 * (w + gap) + w / 2
    s.arrow([(xg, 200), (xg, 262)], "đã duyệt", lx=xg + 40, ly=236)
    s.box(xg - 210, 264, 300, 92, "Hiring manager", ["chỉ xem nhận xét đã duyệt,", "thông tin ứng viên đã che"],
          fill="#fff", stroke=GREEN, title_color=GREEN)
    s.box(22, 264, 640, 140, "Kiểm soát đi kèm", [
        "• Độ phủ kỹ năng JD tính bằng từ điển (nhất quán, giải thích được) – chỉ tham khảo",
        "• Nhận xét phỏng vấn của con người cũng được quét thiên vị trước khi lưu",
        "• Giám sát tỷ lệ qua vòng theo giới tính – quy tắc 4/5 (impact ratio ≥ 0,8)",
        "• Nhật ký audit: ai chạy AI, ai duyệt, ai xem thông tin cá nhân"], fill=GRAY_BG)
    s.box(700, 264, 420, 140, "Dự phòng", ["• Không có API key / Claude lỗi → engine NLP nội bộ",
                                          "• Claude từ chối → server-side fallback",
                                          "• Mọi kết quả đều lưu provider, model, phiên bản prompt"], fill="#fff")
    return s


def use_case() -> Svg:
    s = Svg(1560, 760)
    s.text(780, 36, "Sơ đồ use case theo tác nhân", 22, 700, INK, "middle")
    s.add(f'<rect x="300" y="60" width="960" height="680" rx="16" fill="{GRAY_BG}" stroke="#d1d0c9"/>')
    s.text(320, 86, "Hệ thống TalentLens", 14, 700, MUTED)

    def actor(x, y, name, sub):
        s.add(f'<circle cx="{x}" cy="{y}" r="16" fill="#fff" stroke="{INK2}" stroke-width="2"/>')
        s.line([(x, y + 16), (x, y + 60)], INK2, 2)
        s.line([(x - 24, y + 32), (x + 24, y + 32)], INK2, 2)
        s.line([(x, y + 60), (x - 18, y + 92)], INK2, 2)
        s.line([(x, y + 60), (x + 18, y + 92)], INK2, 2)
        s.text(x, y + 116, name, 15, 700, INK, "middle")
        s.text(x, y + 136, sub, 12, 400, MUTED, "middle")

    def uc(x, y, label, color=BLUE, fill=BLUE_BG, w=270):
        s.add(f'<ellipse cx="{x}" cy="{y}" rx="{w / 2}" ry="24" fill="{fill}" stroke="{color}" stroke-width="1.5"/>')
        s.text(x, y + 5, label, 13, 500, INK, "middle")
        return (x, y, w)

    actor(140, 140, "Hiring manager", "quản lý phòng ban")
    actor(140, 470, "HR", "chuyên viên tuyển dụng")
    actor(1420, 300, "Admin", "quản trị hệ thống")
    common = [uc(500, 130, "Đăng nhập / đổi mật khẩu"), uc(500, 190, "Xem dashboard pipeline"),
              uc(500, 250, "Xem hồ sơ (đã che thông tin)"), uc(500, 310, "Ghi nhận kết quả phỏng vấn"),
              uc(500, 370, "Xem nhận xét AI & báo cáo đã duyệt")]
    hr = [uc(800, 430, "Nhập dữ liệu đa nguồn (ETL)", ORANGE, ORANGE_BG),
          uc(800, 490, "Phân tích CV, phân nhóm kỹ năng", VIOLET, VIOLET_BG),
          uc(800, 550, "Gợi ý câu hỏi PV, lý do rớt", VIOLET, VIOLET_BG),
          uc(800, 610, "Kiểm duyệt nhận xét AI", GREEN, GREEN_BG),
          uc(800, 670, "Tạo & duyệt báo cáo tuần · giám sát công bằng", GREEN, GREEN_BG, 360)]
    admin = [uc(1080, 190, "Quản lý người dùng & phân quyền", GREEN, GREEN_BG),
             uc(1080, 250, "Xem nhật ký hệ thống (audit)", GREEN, GREEN_BG)]
    for (x, y, w) in common:
        s.line([(170, 190), (x - w / 2, y)], "#9d9c96", 1.2)
    for (x, y, w) in common[:2] + hr:
        s.line([(170, 520), (x - w / 2, y)], "#9d9c96", 1.2)
    for (x, y, w) in admin + hr:
        s.line([(1392, 350), (x + w / 2, y)], "#9d9c96", 1.2, dash=True)
    s.text(780, 734, "Admin kế thừa toàn bộ quyền của HR (nét đứt).", 12, 400, MUTED, "middle")
    return s


def deployment() -> Svg:
    s = Svg(1560, 420)
    s.text(780, 36, "Sơ đồ triển khai online (Render + PostgreSQL + Claude API)", 22, 700, INK, "middle")
    s.box(30, 150, 210, 100, "Người dùng", ["trình duyệt web", "(HR, quản lý, admin)"], center=True)
    s.box(330, 70, 260, 100, "GitHub repo", ["mã nguồn + Dockerfile", "+ render.yaml"], center=True, fill=GRAY_BG)
    s.group(660, 60, 560, 320, "Render (Docker, HTTPS)")
    s.box(690, 110, 230, 100, "talentlens-web", ["Streamlit + Plotly", "SERVICE=web"], fill=BLUE_BG, stroke=BLUE,
          title_color=BLUE_D, center=True)
    s.box(960, 110, 230, 100, "talentlens-api", ["FastAPI + ETL + AI", "SERVICE=api"], fill=GREEN_BG, stroke=GREEN,
          title_color=GREEN, center=True)
    s.box(960, 250, 230, 100, "talentlens-db", ["PostgreSQL 16", "kho dữ liệu"], fill=ORANGE_BG, stroke=ORANGE,
          title_color="#8a3a17", center=True)
    s.box(1290, 110, 240, 100, "Anthropic API", ["Claude – tuỳ chọn", "ANTHROPIC_API_KEY"], fill=VIOLET_BG,
          stroke=VIOLET, title_color=VIOLET, center=True)
    s.arrow([(240, 200), (688, 175)], "HTTPS (URL công khai)", lx=470, ly=205)
    s.arrow([(590, 120), (688, 130)], "auto deploy", lx=640, ly=112)
    s.arrow([(920, 160), (958, 160)])
    s.arrow([(1075, 210), (1075, 248)])
    s.arrow([(1190, 160), (1288, 160)], "HTTPS", ly=150)
    s.text(780, 405, "Phương án khác: docker compose (VPS) · Hugging Face Spaces (SERVICE=all) + Neon PostgreSQL",
           13, 400, MUTED, "middle")
    return s


def main() -> None:
    diagrams = {"kien_truc": architecture(), "quy_trinh_etl": etl_flow(), "erd": erd(), "quy_trinh_ai": ai_flow(),
                "use_case": use_case(), "trien_khai": deployment()}
    for name, svg in diagrams.items():
        (OUT / f"{name}.svg").write_text(svg.render(), encoding="utf-8")
    js = """
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
(async () => {
  const dir = process.argv[2]; const names = process.argv.slice(3);
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 2 });
  for (const n of names) {
    const svg = fs.readFileSync(path.join(dir, n + '.svg'), 'utf8');
    await page.setContent('<html><body style="margin:0">' + svg + '</body></html>');
    await page.locator('svg').screenshot({ path: path.join(dir, n + '.png') });
  }
  await browser.close();
})();
"""
    script = OUT / "_render.js"
    script.write_text(js)
    subprocess.run(["node", str(script), str(OUT), *diagrams], check=True)
    script.unlink()
    print("Đã xuất:", ", ".join(f"{n}.png" for n in diagrams))


if __name__ == "__main__":
    sys.exit(main())
