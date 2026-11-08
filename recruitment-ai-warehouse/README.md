# TalentLens – Kho dữ liệu tuyển dụng có AI phân tích pipeline ứng viên

Đồ án môn **Lập trình Python** – Nhóm 8, đề tài AI 9 (Data + AI – HR Analytics).

TalentLens gom dữ liệu tuyển dụng nằm rải rác ở **Google Form, email, ATS và file Excel** vào một kho dữ liệu
PostgreSQL, chuẩn hoá & khử trùng ứng viên, rồi cung cấp **dashboard pipeline** (tỷ lệ chuyển đổi, thời gian xử lý,
điểm nghẽn từng vòng) và **AI** hỗ trợ tóm tắt CV, phân nhóm kỹ năng, phát hiện lý do rớt phổ biến, gợi ý câu hỏi
phỏng vấn theo JD, viết báo cáo tuần. Hệ thống có **phân quyền HR / hiring manager / admin**, **che dữ liệu cá nhân**,
**bộ lọc thiên vị** và **luồng kiểm duyệt nhận xét AI** bởi con người.

![Kiến trúc](docs/images/kien_truc.png)

## Báo cáo

* Báo cáo Word theo mẫu của Học viện: [docs/BaoCao_Nhom8_AI9_KhoDuLieuTuyenDung.docx](docs/BaoCao_Nhom8_AI9_KhoDuLieuTuyenDung.docx)
  (bản PDF cùng tên để xem nhanh). Sinh lại bằng `python docs/report/build_report.py` (cần LibreOffice để tính số trang).

## Chức năng chính

| Task | Nội dung | Thành phần |
|---|---|---|
| 1. ETL & kiến trúc | ETL đa nguồn (CSV, JSON, XLSX, EML + CV PDF/DOCX/TXT) vào PostgreSQL, log ETL chi tiết, chạy lại không trùng | `app/etl/`, trang **Nhập dữ liệu (ETL)** |
| 2. Chuẩn hoá & mô hình kho | Lược đồ hình sao `dim_*`/`fact_*`, chuẩn hoá tên/SĐT/email/ngày/vị trí/nguồn/vòng/trạng thái, khử trùng email → SĐT → họ tên + ngày sinh | `app/models.py`, `app/etl/normalize.py`, `sql/` |
| 3. Dashboard pipeline | Phễu tuyển dụng, tỷ lệ qua vòng, thời gian chuyển vòng so với SLA, điểm nghẽn tự động, hiệu quả nguồn, xu hướng tuần | `app/services/analytics.py`, trang **Tổng quan pipeline** |
| 4. NLP/AI xử lý CV | Trích văn bản CV, tóm tắt, phân nhóm kỹ năng, độ phủ kỹ năng JD, câu hỏi phỏng vấn, lý do rớt phổ biến | `app/ai/`, trang **AI phân tích CV** |
| 5. Phân quyền, chống thiên vị, báo cáo, deploy | RBAC, che PII, ẩn danh trước khi gửi AI, bias guard, kiểm duyệt AI, giám sát công bằng (quy tắc 4/5), báo cáo tuần, audit log, Docker/Render | `app/rbac.py`, `app/ai/bias_guard.py`, `app/services/reports.py`, `render.yaml` |

## Công nghệ

Python 3.13 · FastAPI · SQLAlchemy 2 · PostgreSQL 16 · pandas · scikit-learn (TF-IDF) · pypdf · python-docx ·
Streamlit · Plotly · Anthropic SDK (Claude) · PyJWT · pytest · Docker.

AI: nếu đặt `ANTHROPIC_API_KEY`, hệ thống gọi **Claude** (`LLM_MODEL`, mặc định `claude-opus-5-5`) với structured outputs
(JSON Schema) và server-side fallback; nếu không có key hoặc Claude lỗi, hệ thống tự dùng **engine NLP nội bộ**
(từ điển kỹ năng, TF-IDF, luật từ khoá) nên luôn hoạt động.

## Chạy trên máy (không dùng Docker)

```bash
cd recruitment-ai-warehouse
pip install -r requirements.txt
cp .env.example .env            # sửa DATABASE_URL nếu cần
# Tạo CSDL PostgreSQL: recruitment_dw (user hr_admin / hr_admin_pw)
uvicorn app.main:app --port 8000          # lần đầu tự tạo bảng, tài khoản demo, nạp dữ liệu mẫu
streamlit run frontend/app.py             # mở http://localhost:8501
```

## Chạy bằng Docker Compose

```bash
docker compose up --build
```

Web: http://localhost:8501 · API docs (Swagger): http://localhost:8000/docs

## Triển khai online

Xem [docs/DEPLOY.md](docs/DEPLOY.md) – Render (Blueprint `render.yaml`: PostgreSQL + API + web) hoặc
Hugging Face Spaces (1 container `SERVICE=all`) + Neon PostgreSQL.

## Tài khoản demo

| Tài khoản | Mật khẩu | Vai trò | Thấy gì |
|---|---|---|---|
| `admin` | `Admin@123` | Quản trị | Toàn bộ + quản lý người dùng, nhật ký |
| `hr.lan` | `Demo@123` | HR | Toàn bộ ứng viên, thông tin cá nhân, chạy ETL/AI, kiểm duyệt |
| `manager.data` | `Demo@123` | Hiring manager khối Dữ liệu & AI | Chỉ hồ sơ khối mình, dữ liệu cá nhân bị che, chỉ nhận xét AI đã duyệt |
| `manager.tech` | `Demo@123` | Hiring manager khối Công nghệ | Tương tự, khối Công nghệ |

> Đổi `ADMIN_PASSWORD`, `DEMO_PASSWORD`, `JWT_SECRET` khi triển khai thật.

## Dữ liệu mẫu

`scripts/generate_sample_data.py` sinh bộ dữ liệu **giả lập** (314 ứng viên, 329 hồ sơ, 10 vị trí, 08/2026–11/2026)
rải trên 4 nguồn với lỗi thường gặp: trùng ứng viên giữa các nguồn, SĐT/ngày nhiều định dạng, tên không dấu,
vị trí/nguồn viết khác nhau, bản ghi thiếu thông tin, email rút hồ sơ. ETL khôi phục đúng 314 ứng viên / 329 hồ sơ.

```bash
python scripts/generate_sample_data.py     # tạo lại data/raw
python scripts/export_ddl.py               # xuất sql/schema.sql
```

## Kiểm thử

```bash
TEST_DATABASE_URL=postgresql+psycopg://hr_admin:hr_admin_pw@localhost:5432/recruitment_test pytest -q
```

45 kiểm thử: chuẩn hoá dữ liệu, ETL (khử trùng, idempotent), NLP/AI (kỹ năng, ẩn danh, thiên vị, Claude client giả
lập), API (RBAC, che dữ liệu, kiểm duyệt AI, báo cáo, quản lý người dùng).

## Cấu trúc thư mục

```
app/            FastAPI backend
  etl/          extract · normalize · transform · load · pipeline
  ai/           skills · anonymizer · bias_guard · cv_parser · rejection · local_engine · claude_engine · service
  services/     analytics · reports · audit
  routers/      auth · candidates · analytics · ai · etl · reports
frontend/       Streamlit (app.py + views/)
data/raw/       dữ liệu mẫu 4 nguồn + CV
sql/            schema.sql (DDL) · sample_queries.sql
scripts/        sinh dữ liệu mẫu, xuất DDL
docs/           sơ đồ, hướng dẫn triển khai
tests/          pytest
```
