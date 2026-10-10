# VnNews — Website tin tức có AI phân loại chủ đề (Đồ án Học máy)

Website tin tức tiếng Việt gồm **5.500 bài báo**, mỗi bài được mô hình **TF-IDF + Linear SVM** tự động xếp vào **11 chuyên mục**.
Chạy hoàn toàn trên CPU, không cần GPU hay mô hình ngôn ngữ lớn.

## Chức năng
**Bài toán chính — phân loại**: TF-IDF + Linear SVM xếp bài vào 11 chuyên mục (Accuracy ≈ 89,3%).

**Các chức năng khác (không phải phân loại):**
| Chức năng | Kỹ thuật | Trang |
|---|---|---|
| **Thử thách: người vs AI** (ghi kết quả thật, bảng xếp hạng, cả lớp chơi qua WiFi) | Đánh giá với con người (human baseline) | `/thu-thach`, `/bang-xep-hang` |
| Phân loại ngay khi gõ | Dự đoán thời gian thực | `/phan-loai` |
| Tóm tắt tự động (kèm từ khóa, đo ROUGE) | TextRank / PageRank trên đồ thị câu | `/tom-tat` |
| Gom sự kiện & chủ đề con | KMeans + TruncatedSVD (học không giám sát) | `/su-kien` |
| Bản tin nhanh 60 giây | Tóm tắt hàng loạt | `/ban-tin` |
| Gợi ý "Dành cho bạn" theo lịch sử đọc | Content-based, cosine TF-IDF | trang chủ |
| Tìm kiếm | TF-IDF + cosine | `/tim-kiem` |
| AI Lab — giải thích dự đoán | Phân rã mô hình tuyến tính (Explainable AI) | `/giai-thich` |

Ngoài ra: trang chủ kiểu báo điện tử, 11 chuyên mục có phân trang, đọc bài kèm bài liên quan, thống kê (ma trận nhầm lẫn, F1, phân tích lỗi),
giao diện trắng đen kiểu báo giấy, chế độ sáng/tối, tốt trên điện thoại. Ảnh minh họa đen-trắng tự tạo theo chuyên mục;
muốn dùng ảnh thật chỉ cần chép `static/img/<id>.jpg` (id = số bài, xem trên URL `/bai/<id>`).

## Chạy
```bash
pip install -r requirements.txt
python app.py          # mở http://127.0.0.1:5000
python app.py --lan    # CHẾ ĐỘ LỚP HỌC: điện thoại cùng WiFi vào địa chỉ hiện trên màn hình để chơi Thử thách
```
Khi trình bày: mở `/trinh-bay` (kịch bản demo ~7 phút, có nút mở sẵn từng màn hình) và `/bang-xep-hang` (màn hình chiếu, tự cập nhật).
Mọi chức năng chạy cục bộ, **không cần Internet hay micro**. (Phông chữ lấy từ Google Fonts nếu có mạng, nếu không tự dùng phông dự phòng.)

## Huấn luyện lại / báo cáo
```bash
python train.py          # huấn luyện, sinh outputs/ và model.joblib
python build_cache.py    # dự đoán sẵn cho toàn bộ bài -> data/predictions.json
python predict.py "Bộ Giáo dục công bố điểm chuẩn đại học"
python eval_summary.py   # đo ROUGE của tóm tắt -> outputs/summary_eval.json
python make_report.py    # sinh BAO_CAO_DO_AN.docx
```

## Kết quả (tập kiểm thử 825 bài chưa dùng khi huấn luyện)
Accuracy ≈ 89,3% · Macro-F1 ≈ 89,3%

Báo cáo đầy đủ: `BAO_CAO_DO_AN.docx` (điền tên/MSSV ở trang đầu).
