# Đồ án: Phân loại tin tức tiếng Việt (Học máy)

Pipeline nhẹ, chạy CPU, **không cần DeepSeek / GPU / mô hình lớn**.

- Dữ liệu: `data/external/viet_online_news_test.csv` (5.500 bài, 11 chủ đề)
- Mô hình: TF-IDF (1–2 gram) + Linear SVM (so sánh với NB, LR, RF)
- Kết quả test: Accuracy ≈ 89,3%, Macro-F1 ≈ 89,3%

```bash
pip install -r requirements.txt
python train.py          # huấn luyện, sinh outputs/ và model.joblib
python predict.py "Bộ Giáo dục công bố điểm chuẩn đại học"
python make_report.py    # sinh BAO_CAO_DO_AN.docx
```
Báo cáo: `BAO_CAO_DO_AN.docx`. Điền tên/MSSV ở trang đầu.

## Web demo
```bash
pip install -r requirements.txt
python app.py        # mở http://127.0.0.1:5000
```
