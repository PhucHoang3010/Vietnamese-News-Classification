# Hướng dẫn triển khai online

Yêu cầu đề bài: sản phẩm web có **URL truy cập công khai**. Dưới đây là 2 cách miễn phí.

## Cách 1 – Render (khuyến nghị): PostgreSQL + API + Web

1. Đăng nhập https://render.com bằng tài khoản GitHub.
2. **New → Blueprint**, chọn repo này. Vì dự án nằm trong thư mục con, ở mục *Blueprint Path* nhập
   `recruitment-ai-warehouse/render.yaml` (nếu bạn tách dự án ra repo riêng thì để mặc định `render.yaml`).
3. Render đọc `render.yaml` và tạo:
   * `talentlens-db` – PostgreSQL (free),
   * `talentlens-api` – FastAPI (`SERVICE=api`), tự tạo bảng, tài khoản demo và nạp dữ liệu mẫu ở lần khởi động đầu,
   * `talentlens-web` – Streamlit (`SERVICE=web`).
4. Khi được hỏi biến môi trường:
   * `API_BASE_URL` (của web) = URL của API, ví dụ `https://talentlens-api.onrender.com`
   * `ADMIN_PASSWORD` = mật khẩu admin mong muốn
   * `ANTHROPIC_API_KEY` = (tuỳ chọn) API key Claude; để trống thì dùng engine NLP nội bộ.
5. Chờ build xong → mở URL của `talentlens-web` (ví dụ `https://talentlens-web.onrender.com`).

Kiểm tra: `https://<api>/api/health` trả `{"status":"ok"}`; Swagger tại `https://<api>/docs`.

> Gói free của Render cho dịch vụ “ngủ” sau ~15 phút không dùng; lần truy cập đầu có thể mất ~1 phút. CSDL free có
> thời hạn – có thể thay bằng Neon (bên dưới) bằng cách đặt `DATABASE_URL` của API.

### Tạo thủ công (không dùng Blueprint)

* **New → PostgreSQL** → lấy *Internal Database URL*.
* **New → Web Service** → repo này → *Root Directory* `recruitment-ai-warehouse` → *Runtime* Docker →
  biến `SERVICE=api`, `DATABASE_URL=<url>`, `JWT_SECRET=<chuỗi ngẫu nhiên>` → Health check `/api/health`.
* **New → Web Service** lần nữa → cùng repo/thư mục → `SERVICE=web`, `API_BASE_URL=<URL API>`.

## Cách 2 – Hugging Face Spaces (1 container) + Neon PostgreSQL

1. Tạo CSDL miễn phí tại https://neon.tech → copy connection string (`postgresql://...`).
2. Tạo Space mới, SDK **Docker**, đưa nội dung thư mục `recruitment-ai-warehouse/` vào repo của Space.
3. Thêm vào đầu `README.md` của Space:

   ```yaml
   ---
   title: TalentLens
   sdk: docker
   app_port: 7860
   ---
   ```
4. Trong *Settings → Variables and secrets*: `SERVICE=all`, `PORT=7860`, `DATABASE_URL=<Neon>`,
   `JWT_SECRET=<chuỗi ngẫu nhiên>`, (tuỳ chọn) `ANTHROPIC_API_KEY`.
5. Space build xong sẽ có URL `https://<user>-talentlens.hf.space`.

## Cách 3 – VPS / máy chủ riêng

```bash
git clone <repo> && cd <repo>/recruitment-ai-warehouse
export JWT_SECRET=$(openssl rand -hex 32)
docker compose up -d --build
```

Mở cổng 8501 (web) hoặc đặt sau Nginx/Caddy để có HTTPS.

## Biến môi trường

| Biến | Ý nghĩa | Mặc định |
|---|---|---|
| `SERVICE` | `api`, `web` hoặc `all` | `all` |
| `DATABASE_URL` | Chuỗi kết nối PostgreSQL (`postgres://` cũng được) | localhost |
| `JWT_SECRET` | Khoá ký JWT – **bắt buộc đổi** | giá trị dev |
| `API_BASE_URL` | Địa chỉ API mà giao diện gọi tới | `http://localhost:8000` |
| `AI_PROVIDER` | `auto` / `claude` / `local` | `auto` |
| `ANTHROPIC_API_KEY` | Key Claude (tuỳ chọn) | trống |
| `LLM_MODEL`, `LLM_EFFORT` | Model & mức effort của Claude | `claude-opus-5-5`, `medium` |
| `SEED_DEMO` | Tự nạp dữ liệu mẫu khi CSDL trống | `true` |
| `ADMIN_PASSWORD`, `DEMO_PASSWORD` | Mật khẩu tài khoản demo | `Admin@123`, `Demo@123` |
