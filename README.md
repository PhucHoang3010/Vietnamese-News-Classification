# VnNews — Website tin tức có AI phân loại chủ đề (Đồ án Học máy)

Website tin tức tiếng Việt gồm **5.500 bài báo**, mỗi bài được mô hình **TF-IDF + Linear SVM** tự động xếp vào **11 chuyên mục**.
Chạy hoàn toàn trên CPU, không cần GPU hay mô hình ngôn ngữ lớn, không cần Internet.

## Chức năng
**Bài toán chính — phân loại**: TF-IDF + Linear SVM xếp bài vào 11 chuyên mục (Accuracy ≈ 89,3% trên 825 bài kiểm thử).
Trang chủ có ô **phân loại trực tiếp** (dán đoạn văn bất kỳ → AI xếp chuyên mục ngay), mỗi bài báo có bảng **“AI xếp bài này vào…”** kèm mức nghiêng, top 3 chuyên mục và các từ khóa quyết định.

**Các chức năng khác (không phải phân loại):**
| Chức năng | Kỹ thuật | Trang |
|---|---|---|
| **Hỏi AI về tin tức** — gõ câu hỏi, AI trích đúng câu trả lời từ các bài liên quan, luôn dẫn nguồn, biết từ chối khi không có căn cứ | Truy hồi thông tin (TF-IDF, cosine) + xếp hạng câu, chỉ trích không tự sinh | `/hoi-ai` và ô “Hỏi AI về bài này” ở mỗi bài |
| Phân loại ngay khi gõ | Dự đoán thời gian thực | `/phan-loai` |
| Tóm tắt tự động (kèm từ khóa, đo ROUGE) | TextRank / PageRank trên đồ thị câu | `/tom-tat` |
| Gom sự kiện & chủ đề con | KMeans + TruncatedSVD (học không giám sát) | `/su-kien` |
| Bản tin nhanh 60 giây | Tóm tắt hàng loạt | `/ban-tin` |
| Gợi ý "Dành cho bạn" theo lịch sử đọc | Content-based, cosine TF-IDF | trang chủ |
| Tìm kiếm | TF-IDF + cosine | `/tim-kiem` |
| AI Lab — giải thích dự đoán | Phân rã mô hình tuyến tính (Explainable AI) | `/giai-thich` |

Ngoài ra: trang chủ kiểu báo điện tử, 11 chuyên mục có phân trang (lọc “chỉ bài kiểm thử” / “chỉ bài AI xếp khác báo gốc”), đọc bài kèm bài liên quan,
thống kê (ma trận nhầm lẫn, F1, phân tích lỗi), giao diện trắng đen kiểu báo giấy, chế độ sáng/tối, tốt trên điện thoại.
Ảnh minh họa đen-trắng tự tạo theo chuyên mục; muốn dùng ảnh thật chỉ cần chép `static/img/<id>.jpg` (id = số bài, xem trên URL `/bai/<id>`).

## Chạy
**Windows (dễ nhất):** bấm đúp `CHAY.bat` (tự tạo môi trường `.venv`, cài thư viện, chạy website).

**Hoặc gõ tay:**
```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py                   # mở http://127.0.0.1:5000
```
- Lần chạy đầu mất **1–3 phút** để nạp mô hình và dựng chỉ mục tìm kiếm. **Đừng bấm Ctrl+C** khi chưa thấy dòng “Mở trình duyệt tại http://127.0.0.1:5000”.
- Câu hỏi đầu tiên ở trang Hỏi AI có thể chờ thêm vài giây (chỉ mục nội dung dựng ở luồng nền).
- `python app.py --lan` cho máy khác cùng WiFi mở được website (không bắt buộc).
- Gặp lỗi phiên bản scikit-learn khi nạp mô hình: chạy `python train.py` rồi `python build_cache.py` để tạo lại `model.joblib` và dự đoán sẵn.
- Không biết lỗi ở đâu: `python kiem_tra_moi_truong.py` (in phiên bản Python, thời gian nạp từng thư viện, thử nạp mô hình).

Mọi chức năng chạy cục bộ, **không cần Internet hay micro**. (Phông chữ lấy từ Google Fonts nếu có mạng, nếu không tự dùng phông dự phòng.)

## Huấn luyện lại / báo cáo
```bash
python train.py          # huấn luyện, sinh outputs/ và model.joblib
python build_cache.py    # dự đoán sẵn cho toàn bộ bài -> data/predictions.json
python predict.py "Bộ Giáo dục công bố điểm chuẩn đại học"
python eval_summary.py   # đo ROUGE của tóm tắt -> outputs/summary_eval.json
python make_report.py    # sinh BAO_CAO_DO_AN.docx
```

## Thí nghiệm (thư mục `experiments/`, kết quả trong `outputs/experiments/`)
Các thí nghiệm dùng chung một cách chia dữ liệu (70/15/15, `random_state=42`); **tập kiểm thử chỉ dùng để báo cáo cuối**, mọi lựa chọn đều làm trên tập huấn luyện (cross-validation).
| Script | Nội dung |
|---|---|
| `exp1_tuning.py`, `exp1b_extend_edges.py`, `finalize_exp1.py`, `exp1c_final_table.py` | Chỉnh tham số **công bằng** cho cả 4 mô hình (GridSearchCV 5-fold; mở rộng lưới khi tham số tốt nhất nằm ở biên) → bảng so sánh cuối |
| `exp2_ablation.py` | Ablation: n-gram, sublinear TF, IDF, kích thước từ vựng, min_df/max_df, trường văn bản đầu vào, tiền xử lý, tách từ pyvi (5-fold CV, kiểm định ghép cặp) |
| `exp3_stability.py` | Độ ổn định: nhiều lần chia lại dữ liệu, bootstrap, kiểm định McNemar giữa các mô hình, kiểm tra bài trùng gần giống |
| `exp4_learning_curve.py` | Đường cong học (thêm dữ liệu có giúp không?) |
| `exp5_calibration.py` | Hiệu chỉnh độ tin cậy, biểu đồ rủi ro–độ phủ (từ chối bài kém chắc chắn) |
| `exp6_errors.py` | Phân tích lỗi: cặp chuyên mục hay nhầm, từ gây nhầm, nghi vấn nhãn |
| `exp8_qa.py` | Đánh giá “Hỏi AI”: tìm lại đúng bài (R@1/5/10, MRR), chọn trọng số, ngưỡng tin cậy và ngưỡng từ chối |

Chạy lại: `python experiments/exp2_ablation.py` (mỗi script độc lập; `bash experiments/run_rest.sh exp2_ablation exp3_stability ...` chạy lần lượt). Cần thêm `pip install pyvi` để chạy phần tách từ.

## Kết quả (tập kiểm thử 825 bài chưa dùng khi huấn luyện)
Accuracy ≈ 89,3% · Macro-F1 ≈ 89,3%

Báo cáo đầy đủ: `BAO_CAO_DO_AN.docx` (điền tên/MSSV ở trang đầu).
