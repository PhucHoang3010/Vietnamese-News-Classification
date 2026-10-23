# Kịch bản thuyết trình – Task 2 (Trần Phúc Hoàng)

File slide: `2431540018_TranPhucHoang.pptx` · Thời lượng: khoảng 10 phút + 1 phút chạy demo

## 5 bí quyết để thầy hiểu toàn bộ bài

1. **Nói "bản đồ" ngay từ đầu.** Ở slide 1, chỉ vào 4 bước bên phải: dữ liệu ghi nhiều kiểu → chuẩn hóa → thiết kế 6 bảng → kho dữ liệu. Thầy biết trước bài đi đâu thì sẽ theo kịp.
2. **Đi theo một ví dụ xuyên suốt: anh Trần Văn An.** An nộp hồ sơ Data Analyst qua TopCV, rồi trượt vòng phỏng vấn. Slide nào cũng quay lại hỏi "dữ liệu của An đang ra sao?".
3. **Mỗi slide làm đúng 3 việc:** nói câu chốt → chỉ tay vào hình và giải thích → nói câu chuyển sang slide sau.
4. **Gặp từ khó thì giải thích ngay bằng lời thường.** Ví dụ: "khóa ngoại, tức là cột lưu mã để nối sang bảng khác".
5. **Chạy demo thật ở slide 9.** Thầy thấy số trên màn hình khớp với số trên slide là tin bài làm thật.

> Nếu thầy cho ít thời gian (khoảng 5 phút): chỉ nói **câu chốt** của mỗi slide và bỏ demo.

---

## Kịch bản từng slide

### Slide 1 – Bìa (30 giây)
**Lời nói:** "Em chào thầy và các bạn. Em là Trần Phúc Hoàng, thành viên nhóm 8, đề tài Kho dữ liệu tuyển dụng có AI phân tích pipeline ứng viên. Em trình bày Task 2: chuẩn hóa dữ liệu ứng viên và mô hình kho dữ liệu. Bạn Vy ở Task 1 đã nói quy trình tổng quát. Phần của em đi sâu vào hai việc: đặt quy tắc ghi dữ liệu thống nhất, và thiết kế chi tiết các bảng để lưu."
**Chỉ vào:** 4 bước bên phải. "Bài của em đi đúng 4 bước này, từ trên xuống."

### Slide 2 – Đặt vấn đề và mục tiêu (1 phút)
**Câu chốt:** Mỗi người ghi một kiểu thì máy tính đếm sai, nên cần quy tắc chung và cấu trúc bảng chung.
**Lời nói:** "Bên trái là 4 vấn đề. Ví dụ người này ghi 'DA', người kia ghi 'Data Analyst'. Máy tính sẽ hiểu đó là hai vị trí khác nhau, nên báo cáo số ứng viên Data Analyst bị sai. Kết quả cũng vậy: người ghi 'Trượt', người ghi 'Rớt', người ghi 'fail'. Bên phải là 4 mục tiêu của em, em sẽ đi lần lượt từng mục."
**Chuyển:** "Việc đầu tiên là xác định cần quản lý những thông tin gì."

### Slide 3 – 5 nhóm thông tin chính (1 phút)
**Câu chốt:** Dữ liệu tuyển dụng gồm 5 nhóm thông tin, và cả 5 gặp nhau ở hồ sơ ứng tuyển.
**Lời nói:** "Đây là đúng 5 thông tin đề bài gợi ý: ứng viên, vị trí, nguồn, vòng phỏng vấn và trạng thái." Đọc lướt dòng mô tả dưới mỗi ô. "Năm nhóm này gặp nhau ở **hồ sơ ứng tuyển**. Ví dụ hồ sơ của anh An: An là ứng viên, nộp vào vị trí Data Analyst, qua nguồn TopCV, đang ở vòng Phỏng vấn, trạng thái Không đạt."
**Chỉ vào:** dải màu xanh đậm phía dưới khi nói câu "1 hồ sơ nối cả 5 nhóm". Nói thêm: "Năm nhóm này sẽ thành các bảng trong sơ đồ ERD ở slide 7."
**Chuyển:** "Mỗi nhóm thông tin cần một quy tắc ghi chung."

### Slide 4 – Quy tắc chuẩn hóa (1 phút 30 giây)
**Câu chốt:** Mỗi thông tin chỉ có một cách ghi đúng.
**Lời nói:** Đi từng dòng của bảng với ví dụ anh An:
- "Tên của An bị ghi '  trần  văn AN', thừa khoảng trắng, chữ hoa lẫn thường. Theo quy tắc thì thành 'Trần Văn An'."
- "Email viết thường hết, nên 'An.Tran@Example.COM' thành 'an.tran@example.com'."
- "Số điện thoại chỉ giữ chữ số, đủ 10 số, bắt đầu bằng 0, nên '+84 906 609 544' thành '0906609544'."
- "Ngày ghi năm-tháng-ngày theo chuẩn quốc tế ISO 8601. Cách này không bị nhầm 05/06 là ngày 5 hay ngày 6, và sắp xếp đúng thứ tự."
- "Vị trí và nguồn chỉ được dùng tên có sẵn trong danh mục, nên 'DA' thành 'Data Analyst', 'topcv.vn' thành 'TopCV'."

**Chỉ vào:** cột "Trước" (chữ đỏ) rồi cột "Sau" (chữ xanh). Kết bằng 3 ô dưới cùng: "ghi giống nhau thì máy so sánh được, tìm được, đếm đúng".
**Chuyển:** "Có hai thông tin bị ghi lộn xộn nhất là vòng phỏng vấn và trạng thái, em xin nói riêng."

### Slide 5 – Chuẩn hóa vòng và trạng thái (1 phút 30 giây)
**Câu chốt:** Mọi cách ghi đều được đổi về 5 vòng và 4 trạng thái cố định. Tách riêng hai thông tin này thì biết ứng viên bị loại ở vòng nào.
**Lời nói:** "Bên trái, chữ nghiêng màu xám là các cách ghi thực tế, ví dụ 'interview', 'PV', 'Vòng PV'. Mũi tên chỉ ra chúng đều được đổi về '3. Phỏng vấn'. Các vòng có số thứ tự từ 1 đến 5. Bên phải là 4 trạng thái, mỗi trạng thái một màu, ví dụ 'Trượt', 'Rớt', 'fail' đều thành 'Không đạt'."
**Chỉ vào:** ô bóng đèn dưới cùng. "Điểm quan trọng nhất của slide: anh An đang ở vòng **Phỏng vấn**, trạng thái **Không đạt**, tức là trượt phỏng vấn. Nếu chỉ ghi chung một chữ 'Bị loại' thì không biết An trượt ở vòng nào."
**Chuyển:** "Ghi đúng rồi, câu hỏi tiếp theo là lưu thế nào cho gọn."

### Slide 6 – Tách bảng để không lưu lặp (1 phút)
**Câu chốt:** Thông tin nào lặp lại thì tách ra bảng riêng, chỗ khác chỉ lưu mã.
**Lời nói:** "Bên trái là cách lưu chung một bảng. Thầy thấy 'Data Analyst – Phòng Dữ liệu' bị lặp lại ở cả 3 dòng, chữ đỏ là phần bị lặp. Nếu công ty đổi tên phòng thì phải sửa từng dòng, sót một dòng là dữ liệu mâu thuẫn. Bên phải là cách của em: hồ sơ chỉ lưu mã số 1, 2. Tên thật nằm một lần duy nhất ở bảng vi_tri và bảng nguon. Đổi tên thì chỉ sửa một chỗ. Cách làm này trong môn cơ sở dữ liệu gọi là chuẩn hóa bảng."
**Chuyển:** "Áp dụng cách tách này cho cả 5 nhóm thông tin, em được mô hình 6 bảng."

### Slide 7 – Sơ đồ ERD 6 bảng (1 phút 30 giây)
**Câu chốt:** Đây là sơ đồ ERD (sơ đồ thực thể – quan hệ): một bảng chính ở giữa lưu các lần nộp hồ sơ, nối với 5 bảng thông tin xung quanh bằng quan hệ 1 – n.
**Lời nói:** "Đây là sơ đồ ERD của kho dữ liệu. Ở giữa là bảng chính ho_so_ung_tuyen, mỗi dòng là một lần nộp hồ sơ. Xung quanh là 5 bảng thông tin. Thầy xem ô chú thích: PK là khóa chính, mã riêng của mỗi dòng, không bao giờ trùng. FK là khóa ngoại, cột lưu mã để nối sang bảng khác."
**Chỉ vào:** lần theo từng đường nối. "Hồ sơ của An là một dòng trong bảng chính. Cột ma_ung_vien trỏ sang dòng của An trong bảng ung_vien. Cột ma_vi_tri trỏ sang Data Analyst. ma_vong trỏ sang Phỏng vấn, ma_trang_thai trỏ sang Không đạt. Mỗi đường nối đi từ cột FK của bảng chính sang cột PK của bảng kia. Đầu ghi số 1 là phía bảng xung quanh, đầu ghi chữ n là phía bảng chính. Nghĩa là một ứng viên có thể nộp nhiều vị trí, nên một ứng viên nối với nhiều hồ sơ. Đó là quan hệ một – nhiều."
**Thêm:** "Cột diem_ai là chỗ để phần AI của nhóm ghi điểm. Đây cũng là bản chi tiết của sơ đồ hình ngôi sao mà bạn Vy đã giới thiệu, em thêm bảng trang_thai."
**Chuyển:** "Thiết kế xong, em viết lệnh SQL tạo bảng và đặt luật để chặn dữ liệu sai."

### Slide 8 – Tạo bảng và ràng buộc (1 phút 30 giây)
**Câu chốt:** Cơ sở dữ liệu tự từ chối dữ liệu sai nhờ 5 loại ràng buộc.
**Lời nói:** "Bên phải là lệnh SQL tạo bảng. Chữ màu cam trong code chính là 5 ràng buộc ở bên trái." Đi từng ô, kèm ví dụ:
- "**PRIMARY KEY**: mỗi dòng có mã riêng."
- "**UNIQUE**: nếu ai đó nhập email của An cho một người khác thì bị chặn."
- "**NOT NULL**: không được bỏ trống họ tên, email, ngày nộp."
- "**REFERENCES**: không thể ghi một vòng số 9 không có trong danh mục."
- "**CHECK**: điểm AI gõ nhầm thành 150 cũng bị chặn."

"File SQL này viết theo SQL chuẩn nên chạy được trên cả PostgreSQL và SQLite."
**Chuyển:** "Để chắc chắn mọi thứ chạy đúng, em đã chạy thử toàn bộ với dữ liệu mẫu."

### Slide 9 – Kết quả chạy thử (1 phút + 1 phút demo)
**Câu chốt:** Chạy thật với 221 dòng dữ liệu lộn xộn, kết quả là dữ liệu sạch trong 6 bảng và cả 3 dữ liệu sai đều bị chặn.
**Demo:** chuyển sang cửa sổ lệnh và chạy `python tao_kho_du_lieu.py` (cách chuẩn bị xem phần dưới). Vừa chỉ vào kết quả vừa nói:
- "221 dòng đọc vào. 17 cách ghi vòng khác nhau được gom về 5 vòng."
- "5 dòng lỗi được tách ra file can_kiem_tra.csv để HR xem lại." Mở file đó cho thầy xem nếu còn thời gian.
- "9 hồ sơ trùng bị bỏ, còn 207 hồ sơ."
- "Cuối cùng là 3 lần thử lưu dữ liệu sai, cả 3 đều bị chặn."

**Chỉ vào biểu đồ:** "Nhờ tách vòng và trạng thái, em đếm được người trượt ở từng vòng: nhiều nhất là sàng lọc 34 người, phỏng vấn 27, đề nghị 5. Những trường hợp như anh An nằm ở cột Phỏng vấn."
**Chỉ vào ô dưới phải:** "Phần AI của nhóm sẽ ghi điểm vào cột diem_ai, dashboard đọc 6 bảng này để vẽ biểu đồ." Nói rõ: "Đây là dữ liệu mẫu em tự tạo để chạy thử."
**Chuyển:** "Cuối cùng là khó khăn và hướng cải thiện."

### Slide 10 – Khó khăn, cải thiện, tham khảo (1 phút)
**Lời nói:** "Khó nhất là một giá trị có rất nhiều cách ghi, và phải thống nhất danh mục với cả nhóm. Hướng cải thiện: thêm bảng lịch sử để biết ngày qua từng vòng, thêm bảng kỹ năng cho phần AI." Chỉ tay vào cột tham khảo, không cần đọc hết.
**Câu tóm tắt cuối (quan trọng nhất):** "Tóm lại, Task 2 giúp dữ liệu ứng viên được ghi thống nhất, lưu gọn trong 6 bảng, có luật tự chặn dữ liệu sai, sẵn sàng cho AI và dashboard của nhóm. Em xin cảm ơn thầy và các bạn đã lắng nghe."

---

## Chuẩn bị demo (làm trước buổi thuyết trình)

```bash
pip install pandas
cd bai_tap_python_nhom8/task2_tran_phuc_hoang
python tao_kho_du_lieu.py
```

- Chạy thử một lần trên đúng máy sẽ dùng để thuyết trình.
- Mở sẵn cửa sổ lệnh ở thư mục trên, chỉ cần bấm lại lệnh khi tới slide 9.
- **Phòng khi máy lỗi:** chụp màn hình kết quả trước, nếu demo hỏng thì đưa ảnh ra.

## Nếu thầy hỏi

Xem 14 câu hỏi kèm gợi ý trả lời trong `README.md`. Bốn câu dễ bị hỏi nhất:
- **ERD là gì, nằm ở đâu?** Là sơ đồ thực thể – quan hệ, vẽ các bảng, cột và đường nối quan hệ giữa các bảng. ERD của em ở slide 7.
- **PK và FK khác nhau thế nào?** PK là mã riêng của dòng trong chính bảng đó. FK là cột lưu mã của bảng khác để nối hai bảng.
- **Sao không để chung một bảng?** Vì thông tin bị lặp, sửa dễ sót, dữ liệu mâu thuẫn.
- **Sao phải tách vòng và trạng thái?** Để biết ứng viên bị loại ở vòng nào.

## Checklist trước khi lên

- [ ] Đọc kịch bản 2–3 lần, rồi tập nói bằng lời của mình, không đọc nguyên văn
- [ ] Bấm giờ một lần tập: khoảng 10 phút
- [ ] Chạy demo thử và chụp màn hình dự phòng
- [ ] Nhìn thầy khi nói, dùng tay hoặc chuột chỉ vào phần đang nói trên slide
