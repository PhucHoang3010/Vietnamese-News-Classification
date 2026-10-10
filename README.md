# VnNews — Website tin tức có AI phân loại chủ đề (Đồ án Học máy)

Website tin tức tiếng Việt gồm **5.500 bài báo**, mỗi bài được mô hình **TF-IDF + Linear SVM** tự động xếp vào **11 chuyên mục**.
Chạy hoàn toàn trên CPU, không cần GPU hay mô hình ngôn ngữ lớn.

## Chức năng
- **Trang chủ** kiểu báo điện tử: tin nổi bật, tin mới, từng chuyên mục
- **11 chuyên mục** có phân trang (Thời sự, Thế giới, Kinh doanh, Pháp luật, Giáo dục, Sức khỏe, Khoa học, Đời sống, Giải trí, Thể thao, Xe)
- **Đọc bài** kèm phân tích AI (xác suất, từ khóa quyết định) và bài liên quan
- **Tìm kiếm** theo nội dung, lọc theo chuyên mục
- **Công cụ phân loại**: nhập văn bản / link báo, gợi ý mẫu, bài ngẫu nhiên, lịch sử
- **Thống kê**: Accuracy, F1 từng lớp, ma trận nhầm lẫn, so sánh thuật toán, từ khóa đặc trưng
- **AI Lab — chức năng nổi bật**: giải thích AI bằng bản đồ nhiệt từ ngữ, bấm bỏ từ để xem dự đoán đổi (what-if), phát hiện bài đa chủ đề, phân tích lỗi
- Giao diện trắng đen kiểu báo giấy, chế độ sáng/tối, tốt trên điện thoại
- Ảnh minh họa đen-trắng tự tạo theo chuyên mục; muốn dùng ảnh thật chỉ cần chép `static/img/<id>.jpg` (id = số bài, xem trên URL `/bai/<id>`)

## Chạy
```bash
pip install -r requirements.txt
python app.py          # mở http://127.0.0.1:5000
```

## Huấn luyện lại / báo cáo
```bash
python train.py          # huấn luyện, sinh outputs/ và model.joblib
python build_cache.py    # dự đoán sẵn cho toàn bộ bài -> data/predictions.json
python predict.py "Bộ Giáo dục công bố điểm chuẩn đại học"
python make_report.py    # sinh BAO_CAO_DO_AN.docx
```

## Kết quả (tập kiểm thử 825 bài chưa dùng khi huấn luyện)
Accuracy ≈ 89,3% · Macro-F1 ≈ 89,3%

Báo cáo đầy đủ: `BAO_CAO_DO_AN.docx` (điền tên/MSSV ở trang đầu).
