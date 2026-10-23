# Task 1 – Phân tích bài toán, ETL và kiến trúc công nghệ

Nhóm 8 · Đề tài AI 9: Kho dữ liệu tuyển dụng có AI phân tích pipeline ứng viên
Nguyễn Phan Khánh Vy · MSSV 2431540032 · Lớp 24ĐHTT01

## Có gì trong thư mục này

| File | Dùng để làm gì |
|---|---|
| `2431540032_NguyenPhanKhanhVy.pptx` | 10 slide để nộp. Lời thuyết trình cho từng slide nằm trong phần **Notes** dưới mỗi slide |
| `kich_ban_thuyet_trinh.md` | Kịch bản nói chi tiết từng slide: câu chốt, lời nói mẫu, chỗ cần chỉ tay, cách chạy demo |
| `etl_demo.py` | Code Python chạy thử ETL (số liệu ở slide 9 lấy từ đây) |
| `du_lieu_mau/` | Dữ liệu mẫu tự tạo cho 3 nguồn: file HR, web tuyển dụng, Google Form |

## Chạy thử

```bash
pip install pandas
python etl_demo.py
```

Kết quả: đọc 315 dòng → bỏ 4 dòng trống, 5 email sai, 13 hồ sơ trùng → còn 293 hồ sơ sạch.

## Giải thích nhanh các từ khó

| Từ | Nói đơn giản |
|---|---|
| ETL | 3 bước: **E**xtract lấy dữ liệu → **T**ransform làm sạch → **L**oad lưu vào kho |
| Pipeline ứng viên | Các vòng ứng viên đi qua: Nộp hồ sơ → Sàng lọc → Phỏng vấn → Đề nghị → Nhận việc |
| Kho dữ liệu | Một cơ sở dữ liệu chung chứa dữ liệu đã làm sạch, dùng để báo cáo và phân tích |
| PostgreSQL | Phần mềm cơ sở dữ liệu miễn phí, lưu dữ liệu dạng bảng |
| pandas | Thư viện Python xử lý bảng dữ liệu, giống Excel nhưng bằng code |
| FastAPI | Thư viện Python làm "cầu nối" (API): giao diện web hỏi, API lấy dữ liệu trả về |
| Streamlit | Thư viện Python làm giao diện web và vẽ biểu đồ |
| Star schema | 1 bảng chính ở giữa, các bảng thông tin xung quanh, nhìn giống ngôi sao |
| JSON | Kiểu dữ liệu các trang web hay trả về, dạng `{"ten": "giá trị"}` |
| Phân quyền | Mỗi loại tài khoản (Admin, HR, Quản lý) được làm những việc khác nhau |

## Câu hỏi có thể bị hỏi

1. **ETL là gì, sao phải làm?** – Lấy dữ liệu từ nhiều nơi, làm sạch, rồi lưu vào một chỗ. Nếu không làm sạch thì một người có thể bị đếm 2 lần và báo cáo bị sai.
2. **Làm sao biết hồ sơ bị trùng?** – So email và vị trí ứng tuyển. Trước khi so, email đã được đổi hết về chữ thường nên `AN@EXAMPLE.COM` và `an@example.com` được coi là một.
3. **Sao không dùng luôn Excel?** – Excel khó cho nhiều người cùng sửa, không phân quyền được và dễ sai khi dữ liệu nhiều. PostgreSQL lưu được nhiều dữ liệu, tìm nhanh và nhiều người dùng cùng lúc được.
4. **Sao demo lưu vào SQLite chứ không phải PostgreSQL?** – SQLite có sẵn trong Python, không cần cài nên chạy thử nhanh. Khi triển khai thật chỉ đổi phần kết nối sang PostgreSQL, phần làm sạch giữ nguyên.
5. **Số liệu slide 9 lấy ở đâu?** – Từ việc chạy `etl_demo.py` với dữ liệu mẫu tự tạo trong `du_lieu_mau/`, không phải dữ liệu thật của công ty.
6. **Chạy lại nhiều lần có bị nhân đôi không?** – Không. Mỗi lần chạy bảng được ghi đè (`if_exists="replace"`), và hồ sơ trùng đã bị xóa ở bước làm sạch.
7. **"Tự chạy mỗi đêm" làm thế nào?** – Dùng lịch hẹn giờ (thư viện APScheduler của Python hoặc cron trên server). Bản demo hiện tại chạy bằng lệnh `python etl_demo.py`.
8. **Người bị loại tính thế nào trong biểu đồ?** – Chỉ tính là đã nộp hồ sơ, vì dữ liệu không ghi họ bị loại ở vòng nào.
9. **"Trang thử API" của FastAPI là gì?** – FastAPI tự tạo trang `/docs`, ở đó có thể bấm thử từng API mà không cần viết thêm code.
10. **Phần của em liên quan gì tới các bạn khác?** – Dữ liệu sạch trong kho là đầu vào cho phần AI chấm điểm hồ sơ và cho dashboard của nhóm.
11. **ERD của em đâu?** – Slide 7 là ERD mức khái niệm: hình chữ nhật là 5 thực thể (Hồ sơ ứng tuyển, Ứng viên, Vị trí tuyển, Nguồn hồ sơ, Vòng tuyển), hình thoi là mối liên kết (nộp, nhận, mang về, có), số 1 và chữ n là quan hệ một – nhiều, ví dụ một ứng viên nộp nhiều hồ sơ. ERD chi tiết với từng cột, khóa chính, khóa ngoại nằm ở slide 7 trong file Task 2 của bạn Hoàng, vì đó là phần "mô hình kho dữ liệu".
12. **Star schema khác ERD thế nào?** – ERD là cách vẽ sơ đồ thực thể – quan hệ. Star schema là một kiểu thiết kế kho dữ liệu: khi vẽ bằng ERD thì có hình ngôi sao, một bảng chính ở giữa và các bảng thông tin xung quanh.
