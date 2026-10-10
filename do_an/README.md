# Đồ án: Phân loại tin tức tiếng Việt (Học máy)

Pipeline nhẹ, chạy CPU, **không cần DeepSeek / GPU / mô hình lớn**.

- Dữ liệu: `data/external/viet_online_news_test.csv` (5.500 bài, 11 chủ đề)
- Mô hình: TF-IDF (1–2 gram) + Linear SVM (so sánh với NB, LR, RF)
- Kết quả test: Accuracy ≈ 89,3%, Macro-F1 ≈ 89,3%

```bash
pip install -r do_an/requirements.txt
python do_an/train.py          # huấn luyện, sinh outputs/ và model.joblib
python do_an/predict.py "Bộ Giáo dục công bố điểm chuẩn đại học"
python do_an/make_report.py    # sinh BAO_CAO_DO_AN.docx
```
Báo cáo: `BAO_CAO_DO_AN.docx`. Điền tên/MSSV ở trang đầu.
