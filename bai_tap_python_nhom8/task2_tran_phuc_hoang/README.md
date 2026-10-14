# Task 2 – Chuẩn hóa dữ liệu ứng viên và mô hình kho dữ liệu

Nhóm 8 · Đề tài AI 9: Kho dữ liệu tuyển dụng có AI phân tích pipeline ứng viên
Trần Phúc Hoàng · MSSV 2431540018 · Lớp 24ĐHTT01

## Có gì trong thư mục này

| File | Dùng để làm gì |
|---|---|
| `2431540018_TranPhucHoang.pptx` | 10 slide để nộp. Lời thuyết trình cho từng slide nằm trong phần **Notes** dưới mỗi slide |
| `kho_du_lieu.sql` | Lệnh tạo 6 bảng của kho dữ liệu (chạy được trên PostgreSQL và SQLite) |
| `tao_kho_du_lieu.py` | Code Python chuẩn hóa dữ liệu rồi lưu vào 6 bảng (số liệu ở slide 9 lấy từ đây) |
| `du_lieu_mau/ho_so_tong_hop.csv` | Dữ liệu mẫu tự tạo, cố tình ghi lộn xộn như khi nhiều người cùng nhập |

## Chạy thử

```bash
pip install pandas
python tao_kho_du_lieu.py
```

Kết quả: đọc 221 dòng → 17 cách ghi vòng gom về 5 vòng chuẩn → tách 5 dòng lỗi ra file
`can_kiem_tra.csv` cho HR xem lại → bỏ 9 hồ sơ trùng → còn 207 hồ sơ trong 6 bảng.
Cuối cùng script thử lưu 3 dữ liệu sai và cả 3 đều bị cơ sở dữ liệu chặn lại.

## Giải thích nhanh các từ khó

| Từ | Nói đơn giản |
|---|---|
| Chuẩn hóa dữ liệu | Đưa mọi cách ghi khác nhau về **một** cách ghi chung (`DA`, `data analyst` → `Data Analyst`) |
| Danh mục | Danh sách giá trị được phép dùng, ví dụ 5 vòng tuyển, 4 trạng thái |
| Kho dữ liệu | Cơ sở dữ liệu chung chứa dữ liệu đã chuẩn hóa, dùng để báo cáo và phân tích |
| Khóa chính (PK) | Mã riêng của mỗi dòng trong bảng, không bao giờ trùng |
| Khóa ngoại (FK) | Cột lưu mã của bảng khác, dùng để nối hai bảng với nhau |
| Ràng buộc | Luật đặt trong cơ sở dữ liệu, dữ liệu sai luật sẽ bị từ chối (UNIQUE, NOT NULL, CHECK…) |
| Chuẩn hóa bảng (normalization) | Thông tin nào lặp lại thì tách ra bảng riêng, chỗ khác chỉ lưu mã |
| Quan hệ 1 – nhiều | Một dòng bảng này nối với nhiều dòng bảng kia (1 ứng viên – nhiều hồ sơ) |
| ISO 8601 | Chuẩn quốc tế ghi ngày dạng năm-tháng-ngày, ví dụ `2026-06-15` |

## Câu hỏi có thể bị hỏi

1. **Chuẩn hóa dữ liệu là gì, sao phải làm?** – Là đưa mọi cách ghi về một cách ghi chung. Nếu không, máy tính hiểu `DA` và `Data Analyst` là hai vị trí khác nhau và báo cáo bị sai.
2. **Sao phải tách vòng và trạng thái?** – Để biết ứng viên bị loại ở vòng nào. Nếu chỉ ghi "Bị loại" thì không biết họ trượt sàng lọc hay trượt phỏng vấn.
3. **Khóa chính và khóa ngoại khác nhau thế nào?** – Khóa chính là mã riêng của mỗi dòng trong chính bảng đó. Khóa ngoại là cột lưu mã của bảng khác, ví dụ `ma_vi_tri` trong bảng hồ sơ trỏ sang bảng `vi_tri`.
4. **Sao không để chung một bảng cho dễ?** – Vì tên vị trí, phòng ban, nguồn bị lặp lại ở rất nhiều dòng. Muốn đổi tên phải sửa từng dòng, dễ sót và dữ liệu bị mâu thuẫn.
5. **Gặp cách ghi mới chưa có trong danh mục thì sao?** – Dòng đó không được lưu mà tách ra file `can_kiem_tra.csv` để HR xem lại. Nếu đó là cách ghi hợp lệ thì thêm vào danh mục trong code.
6. **Hồ sơ trùng xử lý thế nào?** – Cùng email và cùng vị trí là trùng, giữ bản cập nhật mới nhất. Trong cơ sở dữ liệu còn có ràng buộc `UNIQUE (ma_ung_vien, ma_vi_tri)` nên không thể lưu trùng.
7. **Sao ngày phải ghi năm-tháng-ngày?** – Theo chuẩn ISO 8601: sắp xếp theo chữ cũng đúng thứ tự thời gian, và không bị nhầm `05/06` là 5 tháng 6 hay 6 tháng 5.
8. **Sao demo dùng SQLite chứ không phải PostgreSQL?** – SQLite có sẵn trong Python nên chạy thử nhanh. File `kho_du_lieu.sql` viết theo SQL chuẩn, đã chạy thử được trên PostgreSQL 16, các ràng buộc cũng chặn đúng.
9. **Cột `diem_ai` để trống là sao?** – Đó là chỗ dành cho phần AI của nhóm ghi điểm vào. Cột được phép trống, nhưng nếu có điểm thì phải từ 0 đến 100 (ràng buộc `CHECK`).
10. **"25 ngày tuyển trung bình" tính thế nào?** – Lấy ngày cập nhật trừ ngày nộp của những người đã nhận việc, rồi tính trung bình.
11. **Số liệu ở slide 9 lấy từ đâu?** – Từ việc chạy `tao_kho_du_lieu.py` với dữ liệu mẫu tự tạo, không phải dữ liệu thật của công ty.
12. **Phần của em khác gì Task 1?** – Task 1 thiết kế quy trình ETL và kiến trúc tổng thể. Task 2 đặt quy tắc chuẩn hóa cho từng thông tin và thiết kế chi tiết 6 bảng mà ETL sẽ đổ dữ liệu vào.
