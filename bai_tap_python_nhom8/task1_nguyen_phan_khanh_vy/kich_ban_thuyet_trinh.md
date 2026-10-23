# Kịch bản thuyết trình – Task 1 (Nguyễn Phan Khánh Vy)

File slide: `2431540032_NguyenPhanKhanhVy.pptx` · Thời lượng: khoảng 10 phút + 1 phút chạy demo

## 5 bí quyết để thầy hiểu toàn bộ bài

1. **Nói "bản đồ" ngay từ đầu.** Ở slide 1, chỉ vào 4 bước bên phải: dữ liệu rời rạc → Python gom và làm sạch → lưu vào PostgreSQL → báo cáo và AI. Cả bài đi đúng theo 4 bước này.
2. **Đi theo một ví dụ xuyên suốt: anh Nguyễn Minh Huy.** Huy nộp hồ sơ, mỗi nơi ghi thông tin của Huy một kiểu, rồi ETL làm sạch thành một dòng duy nhất trong kho.
3. **Mỗi slide làm đúng 3 việc:** nói câu chốt → chỉ tay vào hình và giải thích → nói câu chuyển sang slide sau.
4. **Gặp từ khó thì giải thích ngay bằng lời thường.** Ví dụ: "ETL, tức là Lấy – Làm sạch – Lưu".
5. **Chạy demo thật ở slide 9.** Thầy thấy số trên màn hình khớp với số trên slide là tin bài làm thật.

> Nếu thầy cho ít thời gian (khoảng 5 phút): chỉ nói **câu chốt** của mỗi slide và bỏ demo.

---

## Kịch bản từng slide

### Slide 1 – Bìa (30 giây)
**Lời nói:** "Em chào thầy và các bạn. Em là Nguyễn Phan Khánh Vy, nhóm trưởng nhóm 8. Đề tài của nhóm em là Kho dữ liệu tuyển dụng có AI phân tích pipeline ứng viên. Em trình bày Task 1: phân tích bài toán, quy trình ETL và kiến trúc công nghệ."
**Chỉ vào:** 4 bước bên phải. "Bài của em đi đúng 4 bước này: dữ liệu tuyển dụng đang rời rạc, Python gom và làm sạch, lưu vào PostgreSQL, rồi dùng để báo cáo và cho AI phân tích."
**Nói thêm:** "Trong bài có đủ 3 sơ đồ: sơ đồ luồng ETL ở slide 5, sơ đồ ERD ở slide 7 và sơ đồ kiến trúc ở slide 8."

### Slide 2 – Đặt vấn đề và mục tiêu (1 phút)
**Câu chốt:** Hồ sơ nằm rải rác nên không thống kê được. Task 1 gom tất cả về một chỗ.
**Lời nói:** "Bên trái là 4 vấn đề. Ví dụ anh Nguyễn Minh Huy nộp hồ sơ qua web tuyển dụng, HR lại nhập thêm Huy vào file Excel. Thế là một người thành hai dòng, đếm số ứng viên sẽ bị sai. Bên phải là 4 mục tiêu của em, em sẽ đi lần lượt."
**Chuyển:** "Để làm được, trước tiên em phân tích quy trình tuyển dụng."

### Slide 3 – Phân tích bài toán (1 phút)
**Câu chốt:** Tuyển dụng là một cái phễu 5 vòng, có 3 loại người dùng và 3 con số cần theo dõi.
**Lời nói:** "Bên trái là 5 vòng tuyển dụng, từ nộp hồ sơ đến nhận việc. Càng về sau càng ít người nên giống cái phễu. Chữ 'pipeline ứng viên' trong tên đề tài chính là cái phễu này."
**Chỉ vào:** phần bên phải. "Hệ thống có 3 loại người dùng: Admin, HR và Quản lý, mỗi người được làm việc khác nhau. Vì vậy hệ thống cần đăng nhập và phân quyền. Dưới cùng là 3 con số HR cần: tỷ lệ qua từng vòng, số ngày để tuyển được một người, và nguồn nào hiệu quả nhất."
**Chuyển:** "Muốn tính được 3 con số này thì phải có dữ liệu. Vậy dữ liệu đến từ đâu?"

### Slide 4 – Dữ liệu đến từ đâu (1 phút)
**Câu chốt:** Dữ liệu đến từ 4 nguồn, mỗi nguồn ghi một kiểu.
**Lời nói:** Đọc lướt cột "Nguồn dữ liệu", nhấn vào cột "Lỗi hay gặp". "Ví dụ với anh Huy: file Excel của HR ghi tên viết hoa NGUYỄN MINH HUY. Web tuyển dụng ghi số điện thoại dạng +84 và ghi trạng thái bằng tiếng Anh 'interview'."
**Chỉ vào:** 3 ô dưới cùng. "Nên việc phải làm là đưa tất cả về một mẫu chung."
**Chuyển:** "Việc đưa về một mẫu chung được làm bằng quy trình ETL."

### Slide 5 – ETL: Lấy – Làm sạch – Lưu (1 phút)
**Câu chốt:** ETL gồm 3 bước: lấy dữ liệu, làm sạch, lưu vào kho.
**Lời nói:** "E là Extract, lấy dữ liệu. T là Transform, làm sạch. L là Load, lưu vào kho. Hiểu đơn giản giống đi chợ: mua rau về, nhặt và rửa sạch, rồi mới cất vào tủ lạnh."
**Chỉ vào:** 3 ô dưới. "Quy trình được thiết kế để tự chạy mỗi đêm, có ghi nhật ký mỗi lần chạy, và chạy lại bao nhiêu lần cũng không bị nhân đôi dữ liệu."
**Chuyển:** "Trong 3 bước, làm sạch là bước quan trọng nhất, em xin nói kỹ hơn."

### Slide 6 – Làm sạch dữ liệu (1 phút 30 giây)
**Câu chốt:** Làm sạch nghĩa là đưa mỗi thông tin về một cách ghi.
**Lời nói:** Chỉ vào bảng "Trước / Sau", đi từng dòng: "Tên NGUYỄN MINH HUY thành Nguyễn Minh Huy. Số +84906609544 thành 0906609544. Ngày 15/06/2026 thành 2026-06-15. Trạng thái 'interview' thành 'Phỏng vấn'."
**Chỉ vào code bên phải:** "Mỗi bước là một dòng code Python dùng thư viện pandas. Ví dụ dòng đầu, str.strip() bỏ khoảng trắng thừa, str.title() viết hoa chữ cái đầu. Dòng cuối, drop_duplicates xóa hồ sơ trùng email và vị trí, nên Huy chỉ còn một dòng."
**Chuyển:** "Dữ liệu sạch rồi thì lưu vào đâu? Em thiết kế cơ sở dữ liệu PostgreSQL."

### Slide 7 – Sơ đồ ERD mức khái niệm (1 phút 30 giây)
**Câu chốt:** Đây là ERD mức khái niệm của hệ thống: 5 thực thể và quan hệ một – nhiều giữa chúng. ERD chi tiết nằm ở Task 2 của bạn Hoàng.
**Lời nói:** "Slide này là sơ đồ ERD ở mức khái niệm, tức là vẽ các thực thể và mối liên kết giữa chúng, chưa đi vào từng cột. Thầy xem ô ký hiệu dưới cùng: hình chữ nhật là thực thể, hình thoi là mối liên kết, PK là khóa chính. Hệ thống có 5 thực thể: ở giữa là Hồ sơ ứng tuyển, mỗi lần nộp hồ sơ là một dòng, hồ sơ của anh Huy là một dòng ở đây. Xung quanh là Ứng viên, Vị trí tuyển, Nguồn hồ sơ và Vòng tuyển."
**Chỉ vào từng hình thoi, đọc to mối liên kết:** "Ứng viên **nộp** hồ sơ, Vị trí tuyển **nhận** hồ sơ, Nguồn **mang về** hồ sơ, Vòng tuyển **có** hồ sơ. Số 1 và chữ n trên đường nối là quan hệ một – nhiều: một ứng viên nộp được nhiều hồ sơ vì một người nộp được nhiều vị trí. Hồ sơ nằm ở giữa theo hình ngôi sao, nên đếm số người qua từng vòng hay theo từng nguồn chỉ cần một câu truy vấn."
**Nối sang Task 2:** "Vì các task trong nhóm không trùng nhau, ERD chi tiết với từng cột, khóa chính, khóa ngoại và ký hiệu 1 – n thuộc phần 'mô hình kho dữ liệu' của bạn Hoàng, ở slide 7 trong file Task 2. Ở đó bạn Hoàng tách thêm thực thể Trạng thái."
**Chuyển:** "Cơ sở dữ liệu là một phần trong kiến trúc chung của cả hệ thống."

> **Nếu thầy chấm trên file bản cũ** (slide 7 ghi "Thiết kế cơ sở dữ liệu PostgreSQL", không có hình thoi và số 1, n): mở đầu bằng câu "Đây là sơ đồ ERD mức khái niệm", rồi chỉ vào từng đường nối và nói ra quan hệ một – nhiều như trên.

### Slide 8 – Kiến trúc công nghệ (1 phút 30 giây)
**Câu chốt:** Hệ thống gồm backend là phần chạy phía sau, và frontend là phần giao diện người dùng nhìn thấy.
**Lời nói:** Đi theo mũi tên từ trái sang phải: "Dữ liệu nguồn đi vào Python để gom và làm sạch, lưu vào PostgreSQL. FastAPI lấy dữ liệu ra và kiểm tra đăng nhập. Cuối cùng Streamlit hiển thị lên web. Python, PostgreSQL, FastAPI và phần AI là **backend**. Streamlit là **frontend**."
**Ví dụ dễ hiểu:** "Hệ thống giống một nhà hàng. Streamlit là phòng ăn và tờ menu, khách thấy và gọi món ở đó. Backend là nhà bếp và kho. FastAPI là người phục vụ chạy giữa bàn ăn và nhà bếp."
**Chỉ vào ô "Vì sao chọn":** "Em chọn bộ công nghệ này vì tất cả đều dùng Python, miễn phí và dễ học, cả nhóm dễ phối hợp."
**Chuyển:** "Để kiểm tra thiết kế, em đã viết code chạy thử."

### Slide 9 – Kết quả chạy thử (1 phút + 1 phút demo)
**Câu chốt:** Chạy thật với dữ liệu mẫu từ 3 nguồn, ra 293 hồ sơ sạch.
**Demo:** chuyển sang cửa sổ lệnh và chạy `python etl_demo.py` (cách chuẩn bị xem phần dưới). Vừa chỉ vào kết quả vừa nói: "Đọc vào 315 dòng từ 3 nguồn. Bỏ 4 dòng trống, 5 email sai và 13 hồ sơ trùng. Còn lại 293 hồ sơ sạch."
**Chỉ vào biểu đồ:** "Đây là cái phễu ở slide 3, giờ có số thật: 293 người nộp hồ sơ, càng về sau càng ít, cuối cùng 15 người nhận việc."
**Chỉ vào ô dưới phải:** "Dữ liệu sạch này là đầu vào cho phần AI và dashboard của các bạn trong nhóm." Nói rõ: "Đây là dữ liệu mẫu em tự tạo để chạy thử."
**Chuyển:** "Cuối cùng là khó khăn và hướng cải thiện."

### Slide 10 – Khó khăn, cải thiện, tham khảo (1 phút)
**Lời nói:** "Khó nhất là mỗi nguồn ghi dữ liệu một kiểu, và nhận ra hồ sơ trùng khi thông tin ghi khác nhau. Hướng cải thiện: nhận diện trùng thông minh hơn, tự đọc kỹ năng từ CV, và bảo vệ thông tin cá nhân theo Luật Bảo vệ dữ liệu cá nhân 2025." Chỉ tay vào cột tham khảo, không cần đọc hết.
**Câu tóm tắt cuối (quan trọng nhất):** "Tóm lại, Task 1 biến dữ liệu tuyển dụng rời rạc thành dữ liệu sạch trong một kho chung, và chọn công nghệ để cả nhóm cùng xây dựng sản phẩm. Em xin cảm ơn thầy và các bạn đã lắng nghe."

---

## Chuẩn bị demo (làm trước buổi thuyết trình)

```bash
pip install pandas
cd bai_tap_python_nhom8/task1_nguyen_phan_khanh_vy
python etl_demo.py
```

- Chạy thử một lần trên đúng máy sẽ dùng để thuyết trình.
- Mở sẵn cửa sổ lệnh ở thư mục trên, chỉ cần bấm lại lệnh khi tới slide 9.
- **Phòng khi máy lỗi:** chụp màn hình kết quả trước, nếu demo hỏng thì đưa ảnh ra.

## Nếu thầy hỏi

Xem 12 câu hỏi kèm gợi ý trả lời trong `README.md`. Các câu dễ bị hỏi nhất:
- **ERD của em đâu?** Slide 7 là ERD mức khái niệm: các thực thể và quan hệ một – nhiều. ERD chi tiết với cột, khóa chính, khóa ngoại nằm ở slide 7 trong file Task 2 của bạn Hoàng, vì đó là phần "mô hình kho dữ liệu".
- **Star schema khác ERD thế nào?** ERD là cách vẽ sơ đồ thực thể – quan hệ. Star schema là một kiểu thiết kế kho dữ liệu: vẽ bằng ERD thì có hình ngôi sao, một bảng chính ở giữa và các bảng thông tin xung quanh.
- **Frontend và backend của nhóm là gì?** Frontend là Streamlit, phần giao diện người dùng nhìn thấy. Backend là Python ETL, PostgreSQL, FastAPI và phần AI, chạy phía sau để xử lý và lưu dữ liệu.
- **Streamlit viết bằng Python, sao gọi là frontend?** Vì việc của nó trong hệ thống là làm giao diện, nên nó đóng vai frontend.

## Checklist trước khi lên

- [ ] Đọc kịch bản 2–3 lần, rồi tập nói bằng lời của mình, không đọc nguyên văn
- [ ] Bấm giờ một lần tập: khoảng 10 phút
- [ ] Chạy demo thử và chụp màn hình dự phòng
- [ ] Nhìn thầy khi nói, dùng tay hoặc chuột chỉ vào phần đang nói trên slide
