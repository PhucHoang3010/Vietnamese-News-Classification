# VnNews — Website tin tức có AI phân loại chủ đề (Đồ án Học máy)

Website tin tức tiếng Việt gồm **5.500 bài báo**, mỗi bài được mô hình **TF-IDF + Linear SVM** tự động xếp vào **11 chuyên mục**.
Chạy hoàn toàn trên CPU, không cần GPU hay mô hình ngôn ngữ lớn, không cần Internet.

## Chức năng
**Bài toán chính — phân loại**: TF-IDF + Linear SVM xếp bài vào 11 chuyên mục (Accuracy ≈ 89,3% trên 825 bài kiểm thử).
Trang chủ có ô **phân loại trực tiếp** (dán đoạn văn bất kỳ → AI xếp chuyên mục ngay), mỗi bài báo có bảng **“AI xếp bài này vào…”** kèm độ tự tin (website gọi phần trăm này là “độ tự tin”), top 3 chuyên mục và các từ khóa quyết định.

**Điểm nhấn — AI gắn nhiều chuyên mục, có bảo đảm** (*conformal prediction*): thay vì ép mỗi bài vào đúng một chuyên mục, AI đưa ra một **tập** chuyên mục sao cho
với bài mới, chuyên mục đúng nằm trong tập với xác suất ≥ 95% (chọn được 90 / 95 / 99%). Bài rõ ràng → 1 chuyên mục; bài mơ hồ → 2–3 chuyên mục (nhãn “↔ cũng: …”).
Trên 825 bài kiểm thử, mức 95%: chuyên mục đúng nằm trong tập ở 94,5% bài, trung bình 1,37 chuyên mục/bài, 76% bài chỉ cần 1 chuyên mục (và 1 chuyên mục đó đúng 95,8%);
lặp 300 lần chia ngẫu nhiên thì độ phủ trung bình 95,6%. Hiện ở trang chủ, trang bài báo, `/phan-loai`, `/giai-thich`, `/thong-ke` và tab **“Bài có thể thuộc nhiều mục”** của mỗi chuyên mục.
Lưu ý: bảo đảm là *trung bình* trên các bài cùng phân bố với dữ liệu hiệu chỉnh (4.675 điểm “chưa thấy”), không phải cam kết cho từng bài.

**Các chức năng khác (không phải phân loại):**
| Chức năng | Kỹ thuật | Trang |
|---|---|---|
| **Hỏi AI về tin tức** — gõ câu hỏi, AI trích đúng câu trả lời từ các bài liên quan, luôn dẫn nguồn, biết từ chối khi không có căn cứ | Truy hồi thông tin (TF-IDF, cosine) + xếp hạng câu, chỉ trích không tự sinh | `/hoi-ai` và ô “Hỏi AI về bài này” ở mỗi bài |
| **Tìm kiếm nâng cao** — `AND / OR / NOT`, `"cụm từ"`, `bóng*`, `-từ`, ngoặc đơn, tìm theo trường `tieude: sapo: noidung: chuyenmuc:`; không phân biệt dấu; hiển thị “Hiểu truy vấn là…” | Chỉ mục ngược nhị phân theo từng trường + bộ phân tích cú pháp; kết quả xếp theo TF-IDF | `/tim-kiem` |
| **Tìm theo nghĩa** — kết quả cùng chủ đề hơn tìm từ khóa thuần | LSA (TF-IDF → TruncatedSVD 300 chiều) trộn 70% TF-IDF + 30% LSA | `/tim-kiem` (chọn “Theo nghĩa”) |
| **Bình luận của bạn đọc** — đăng, trả lời, thích, sắp xếp mới nhất / nhiều thích, xóa bình luận của mình; số bình luận hiện trên thẻ bài; khối “Ý kiến bạn đọc” ở thanh bên | SQLite (`data/comments.db`), không cần tài khoản; giới hạn độ dài/tốc độ, chống trùng, thoát HTML (xem `comments.py`) | cuối mỗi trang bài |
| **Bộ sưu tập cá nhân** — lưu bài (☆), gắn thẻ, lọc theo thẻ, xuất JSON/CSV, hỏi AI trong các bài đã lưu, gợi ý thêm | Lưu trong trình duyệt (localStorage); chỉ số thứ tự bài được gửi lên khi hỏi/gợi ý | `/bo-suu-tap` |
| Phân loại ngay khi gõ | Dự đoán thời gian thực | `/phan-loai` |
| Tóm tắt tự động (kèm từ khóa, đo ROUGE) | TextRank / PageRank trên đồ thị câu | `/tom-tat` |
| Gom sự kiện & chủ đề con | KMeans + TruncatedSVD (học không giám sát) | `/su-kien` |
| Bản tin nhanh 60 giây | Tóm tắt hàng loạt | `/ban-tin` |
| Gợi ý "Dành cho bạn" theo lịch sử đọc | Content-based, cosine TF-IDF | trang chủ |
| AI Lab — giải thích dự đoán | Phân rã mô hình tuyến tính (Explainable AI) | `/giai-thich` |

Ngoài ra: trang chủ kiểu báo điện tử, 11 chuyên mục có phân trang (lọc “bài AI chưa từng thấy” / “AI xếp khác báo gốc” / “bài có thể thuộc nhiều mục”), đọc bài kèm bài liên quan,
thống kê (ma trận nhầm lẫn, F1, phân tích lỗi, bảng so sánh công bằng 6 mô hình, độ phủ của tập chuyên mục), giao diện kiểu báo điện tử hiện đại, **đã làm gọn cho dễ hiểu**: trang chủ chỉ có ba việc (thử phân loại theo 3 bước ①②③, giải thích “AI làm thế nào” trong 3 dòng, tin theo chuyên mục); thanh menu chỉ có 5 mục (Trang chủ · Chuyên mục · Thử phân loại · Độ chính xác · Công cụ AI); chi tiết nâng cao nằm trong mục “Xem AI phân tích chi tiết” hoặc trang riêng; phần màu nằm trong `static/theme.css`, chế độ sáng/tối, tốt trên điện thoại.
Ảnh minh họa tự vẽ bằng SVG, mỗi chuyên mục một bảng màu; muốn dùng ảnh thật chỉ cần chép `static/img/<id>.jpg` (id = số bài, xem trên URL `/bai/<id>`).

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
- Câu hỏi đầu tiên ở trang Hỏi AI và lần tìm “Theo nghĩa” đầu tiên có thể chờ thêm khoảng nửa phút (chỉ mục nội dung và chỉ mục LSA dựng ở luồng nền; tìm Boolean sẵn sàng sớm hơn).
- `python app.py --lan` cho máy khác cùng WiFi mở được website (không bắt buộc).
- Gặp lỗi phiên bản scikit-learn khi nạp mô hình: chạy `python train.py` rồi `python build_cache.py` để tạo lại `model.joblib`, dự đoán sẵn và ngưỡng của tập chuyên mục.
- Không biết lỗi ở đâu: `python kiem_tra_moi_truong.py` (in phiên bản Python, thời gian nạp từng thư viện, thử nạp mô hình).
- Kiểm thử tự động (40 bài: độ phủ conformal, cú pháp tìm kiếm AND/OR/NOT, cụm từ, ký tự đại diện, trường, bỏ dấu, báo lỗi cú pháp, bình luận: đăng/trả lời/thích/xóa, giới hạn tốc độ, API): `python -m unittest discover -s tests -v`. Kiểm thử giao diện bằng trình duyệt (cần Node.js + Playwright): xem đầu các tệp trong `tests/e2e/`.
- **Bình luận** nằm trong `data/comments.db` (SQLite, không đưa lên git; mỗi máy có bộ riêng). Muốn xóa hết bình luận: xóa tệp này (tắt website trước cho chắc). Muốn dùng tệp khác: đặt biến môi trường `VNNEWS_COMMENTS_DB=<đường dẫn>` trước khi chạy `python app.py`. Website không có tài khoản và không kiểm duyệt nội dung bình luận.

Hướng dẫn chi tiết từng bước và cách xử lý lỗi: `HUONG-DAN-CHAY.txt`. Slide và kịch bản thuyết trình (không demo, chia 5 người): thư mục `trinh-bay/`.
Mọi chức năng chạy cục bộ, **không cần Internet hay micro**. (Phông chữ lấy từ Google Fonts nếu có mạng, nếu không tự dùng phông dự phòng.)

## Huấn luyện lại / báo cáo
```bash
python train.py          # huấn luyện, sinh outputs/ và model.joblib
python build_cache.py    # dự đoán sẵn cho toàn bộ bài + hiệu chỉnh conformal -> data/predictions.json, data/conformal.json
python predict.py "Bộ Giáo dục công bố điểm chuẩn đại học"
python eval_summary.py   # đo ROUGE của tóm tắt -> outputs/summary_eval.json
python make_report.py    # sinh BAO_CAO_DO_AN.docx (A4, có bìa, tóm tắt, mục lục, cơ sở lý thuyết, ảnh website, phân công, phụ lục)
```
Báo cáo dùng thêm hai loại ảnh tạo sẵn: sơ đồ hệ thống (`python experiments/ve_so_do_he_thong.py` → `outputs/he_thong.png`) và ảnh màn hình website
(`node tests/e2e/chup_man_hinh.js outputs/man_hinh`, cần Node.js + Playwright, chạy khi website đang chạy với kho bình luận tạm). Số trang trong mục lục lấy từ
`outputs/toc_pages.json` (tạo bằng `python experiments/tinh_so_trang_muc_luc.py BAO_CAO_DO_AN.pdf` sau khi xuất báo cáo ra PDF); trong Word có thể bấm chuột phải vào mục lục → Cập nhật trường.
`build_cache.py` chấm điểm các bài huấn luyện bằng *cross-fitting* 5 lần (mỗi bài được chấm bởi mô hình chưa thấy nó) để có đủ điểm “chưa thấy” cho hiệu chỉnh;
kết quả lưu ở `data/oof_train.npz` nên các lần chạy sau nhanh. Mã của phương pháp: `conformal.py`; công cụ tìm kiếm: `search_tools.py`.

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
| `exp7_explain.py` | Độ trung thực của AI Lab: giữ / xóa các từ AI cho là quan trọng thì dự đoán đổi thế nào |
| `exp8_qa.py` | Đánh giá “Hỏi AI”: tìm lại đúng bài (R@1/5/10, MRR), chọn trọng số, ngưỡng tin cậy và ngưỡng từ chối |
| `exp9_conformal.py` | **AI gắn nhiều chuyên mục có bảo đảm**: so top-k cố định, LAC, APS ngẫu nhiên, khoảng cách điểm SVM (chung / theo chuyên mục) ở mức 90/95/99%; lặp 300 lần chia ngẫu nhiên; kiểm tra điểm cross-fitting có thay được điểm “chưa thấy” không |
| `exp10_search.py` | **Tìm kiếm**: bộ tìm Boolean có đúng không (100/100 truy vấn ngẫu nhiên khớp cách duyệt tuần tự; trung bình ≈ 5 ms/truy vấn); LSA có hơn TF-IDF không (tìm lại đúng bài, độ thuần chủ đề P@10) |

Chạy lại: `python experiments/exp2_ablation.py` (mỗi script độc lập; `bash experiments/run_rest.sh exp2_ablation exp3_stability ...` chạy lần lượt). Cần thêm `pip install pyvi` để chạy phần tách từ.

## Kết quả (tập kiểm thử 825 bài chưa dùng khi huấn luyện)
Accuracy ≈ 89,3% · Macro-F1 ≈ 89,3%

Tập chuyên mục có bảo đảm (mức 95%): độ phủ 94,5% · trung bình 1,37 chuyên mục/bài · 76% bài chỉ 1 chuyên mục. Mức 90%: 92,1% / 1,16; mức 99%: 99,3% / 2,53.
(Mức 90% gần bằng độ chính xác của việc chọn 1 chuyên mục nên trang web mặc định hiển thị mức 95%.)

Tìm theo nghĩa (LSA trộn 70/30) so với TF-IDF thuần, nửa dữ liệu dùng để đánh giá: độ thuần chủ đề P@10 64,3% so với 60,7% (+3,7 điểm); tìm lại đúng một bài gần như không đổi (R@1 tiêu đề → bài 78,3% so với 77,4%).
Vì vậy “Theo nghĩa” là lựa chọn để *khám phá cùng chủ đề*, không phải để tìm đúng một bài cụ thể.

Báo cáo đầy đủ: `BAO_CAO_DO_AN.docx`. **Nhóm cần điền** (các chỗ tô vàng và ô trống): trường/khoa, giảng viên, lớp, họ tên + MSSV ở trang bìa; nguồn dữ liệu ở mục 2.1; kiểm tra bảng phân công ở mục 10.
