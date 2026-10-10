"""Sinh báo cáo Word từ kết quả trong outputs/: python make_report.py"""
import json
from pathlib import Path
import pandas as pd
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

O = Path(__file__).parent / "outputs"
m = json.load(open(O / "metrics.json", encoding="utf-8")); bench = pd.read_csv(O / "so_sanh_mo_hinh.csv", encoding="utf-8")
rep = pd.read_csv(O / "bao_cao_phan_loai.csv", index_col=0, encoding="utf-8-sig"); kw = json.load(open(O / "tu_khoa_dac_trung.json", encoding="utf-8"))
err = pd.read_csv(O / "mau_du_doan_sai.csv", encoding="utf-8-sig")

d = Document(); d.styles["Normal"].font.name = "Times New Roman"; d.styles["Normal"].font.size = Pt(13)
def H(t, l=1): d.add_heading(t, l)
def P(t): d.add_paragraph(t)
def B(items): [d.add_paragraph(i, style="List Bullet") for i in items]
def IMG(f, cap, w=14):
    d.add_picture(str(O / f), width=Cm(w)); d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = d.add_paragraph(cap); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
def TABLE(df, fmt="{:.3f}"):
    t = d.add_table(rows=1, cols=len(df.columns)); t.style = "Light Grid Accent 1"
    for i, c in enumerate(df.columns): t.rows[0].cells[i].text = str(c)
    for _, r in df.iterrows():
        cells = t.add_row().cells
        for i, v in enumerate(r): cells[i].text = fmt.format(v) if isinstance(v, float) else str(v)

t = d.add_heading("ĐỒ ÁN MÔN HỌC MÁY\nPHÂN LOẠI TIN TỨC TIẾNG VIỆT", 0); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
P("Sinh viên thực hiện: ........................   MSSV: ..............\nLớp: ..............   Giảng viên: ........................")

H("1. Giới thiệu")
P("Mỗi ngày các trang báo điện tử đăng hàng nghìn bài viết. Việc gán chủ đề (giáo dục, sức khỏe, thể thao, pháp luật...) thủ công tốn nhiều thời gian. "
  "Đề tài xây dựng hệ thống học máy tự động phân loại bài báo tiếng Việt vào 11 chủ đề dựa trên nội dung văn bản.")
P("Mục tiêu: (1) xây dựng pipeline tiền xử lý – trích xuất đặc trưng – huấn luyện; (2) so sánh một số thuật toán học máy cổ điển; "
  "(3) đánh giá bằng Accuracy, Precision, Recall, F1; (4) cung cấp chương trình dự đoán chạy được trên máy cấu hình thấp (CPU, không cần GPU hay mô hình ngôn ngữ lớn).")

H("2. Dữ liệu")
P(f"Bộ dữ liệu gồm {m['n_samples']} bài báo tiếng Việt, {m['n_classes']} chủ đề, mỗi chủ đề 500 bài (cân bằng). "
  "Mỗi mẫu có tiêu đề, mô tả, nội dung và nhãn. Văn bản đầu vào = tiêu đề + mô tả + nội dung. Dữ liệu chia phân tầng (stratified) theo tỉ lệ 70% huấn luyện / 15% kiểm định / 15% kiểm thử (random_state=42).")
IMG("phan_bo_nhan.png", "Hình 1. Phân bố số bài theo chủ đề", 12)
IMG("do_dai_bai.png", "Hình 2. Phân bố độ dài bài báo", 12)

H("3. Phương pháp")
H("3.1 Tiền xử lý", 2)
B(["Chuẩn hóa Unicode NFC, chuyển chữ thường.", "Loại bỏ URL, email, chữ số và dấu câu.", "Gộp khoảng trắng; loại mẫu quá ngắn và mẫu trùng lặp."])
H("3.2 Trích xuất đặc trưng TF-IDF", 2)
P("Văn bản được biểu diễn bằng vector TF-IDF với unigram + bigram (bigram giúp bắt cụm từ tiếng Việt như “học sinh”, “ngân hàng”, “diễn viên”), "
  "min_df=2, max_df=0.9, sublinear_tf=True. TF-IDF cho trọng số cao với từ đặc trưng của một chủ đề và thấp với từ xuất hiện ở mọi chủ đề.")
H("3.3 Các mô hình so sánh", 2)
B(["Complement Naive Bayes – nhanh, phù hợp văn bản.", "Logistic Regression.", "Linear SVM (LinearSVC) – thường mạnh nhất với TF-IDF thưa, nhiều chiều.", "Random Forest."])
P("Mô hình tốt nhất trên tập kiểm định (Linear SVM) được tinh chỉnh siêu tham số bằng GridSearchCV (3-fold, độ đo Macro-F1) trên tập huấn luyện.")

H("4. Kết quả thực nghiệm")
H("4.1 So sánh mô hình (tập kiểm định)", 2)
b = bench.copy(); b.columns = ["Mô hình", "Accuracy", "Macro-F1", "Thời gian huấn luyện (s)"]; TABLE(b)
IMG("so_sanh_mo_hinh.png", "Hình 3. So sánh Macro-F1 các mô hình", 12)
H("4.2 Tinh chỉnh siêu tham số", 2)
P(f"Cấu hình tốt nhất: {m['best_params']} với Macro-F1 CV = {m['cv_macro_f1']:.4f}.")
H("4.3 Kết quả cuối trên tập kiểm thử", 2)
P(f"Trên {m['test_size']} mẫu kiểm thử (chưa từng dùng khi huấn luyện/chọn mô hình): Accuracy = {m['test_accuracy']:.4f}, Macro-F1 = {m['test_macro_f1']:.4f}.")
r = rep.loc[[i for i in rep.index if i not in ("accuracy", "macro avg", "weighted avg")], ["precision", "recall", "f1-score", "support"]].reset_index()
r.columns = ["Chủ đề", "Precision", "Recall", "F1", "Số mẫu"]; r["Số mẫu"] = r["Số mẫu"].astype(int).astype(str); TABLE(r, "{:.3f}")
IMG("ma_tran_nham_lan.png", "Hình 4. Ma trận nhầm lẫn trên tập kiểm thử", 15)

H("5. Phân tích")
P("Các chủ đề có đặc trưng từ vựng rõ như Thể thao, Sức khỏe, Xe, Giải trí, Pháp luật đạt F1 > 0,92. Các chủ đề “Thời sự”, “Đời sống”, “Kinh doanh”, “Thế giới” thấp hơn "
  "do nội dung giao thoa (một bài về chính sách kinh tế có thể thuộc Thời sự hoặc Kinh doanh). Đây là hạn chế do ranh giới nhãn mờ chứ không hoàn toàn do mô hình.")
P("Từ khóa đặc trưng nhất của từng chủ đề (trọng số lớn nhất của Linear SVM), giúp giải thích mô hình:")
TABLE(pd.DataFrame({"Chủ đề": list(kw), "Top từ khóa": [", ".join(v[:6]) for v in kw.values()]}))
P(f"Số mẫu dự đoán sai trên tập kiểm thử: {len(err)} / {m['test_size']} (xem file outputs/mau_du_doan_sai.csv).")

H("6. Hệ thống web và chức năng nổi bật")
P("Mô hình được đóng gói thành website tin tức VnNews (Flask) gồm: trang chủ, 11 chuyên mục, trang đọc bài, tìm kiếm TF-IDF, công cụ phân loại (văn bản/đường link), trang thống kê và giới thiệu. "
  "Toàn bộ 5.500 bài được mô hình tự động gán chuyên mục; các chỉ số độ chính xác chỉ tính trên tập kiểm thử.")
H("6.1 AI Lab – giải thích dự đoán (Explainable AI)", 2)
P("Điểm khác biệt của đồ án là chức năng giải thích vì sao mô hình chọn một chủ đề. Vì Linear SVM là mô hình tuyến tính, điểm của mỗi chủ đề bằng tổng (trọng số × giá trị TF-IDF) nên có thể tách chính xác "
  "phần đóng góp của từng từ và cụm hai từ mà không cần xấp xỉ như LIME/SHAP. Đóng góp của một từ = (trọng số chủ đề dự đoán − trọng số trung bình các chủ đề còn lại) × TF-IDF.")
B(["Bản đồ nhiệt từ ngữ: mỗi từ trong bài được tô đậm theo mức ủng hộ chủ đề dự đoán; từ đi ngược được gạch chấm.",
   "What-if: người dùng bấm bỏ một từ, hệ thống dự đoán lại ngay và cho biết xác suất thay đổi bao nhiêu hoặc chủ đề có bị đổi không (ví dụ bỏ các từ thể thao thì bài chuyển sang Kinh doanh).",
   "Dải chủ đề theo đoạn: bài được cắt thành các đoạn, mỗi đoạn phân loại riêng; nếu dưới 75% nội dung cùng một chủ đề thì cảnh báo bài đa chủ đề/mơ hồ.",
   "Phân tích lỗi: trang thống kê liệt kê các bài AI đoán sai nhưng có độ tin cậy cao, kèm liên kết sang AI Lab để xem nguyên nhân."])
H("7. Hạn chế và hướng phát triển")
B(["Chưa tách từ tiếng Việt (word segmentation); có thể thêm underthesea/VnCoreNLP để cải thiện.",
   "Có thể thử mô hình học sâu (PhoBERT) khi có GPU – đã cố ý không dùng để chương trình chạy được trên máy yếu.",
   "Dữ liệu chỉ 5.500 bài; thêm dữ liệu và gộp/chuẩn hóa nhãn mờ sẽ tăng độ chính xác.",
   "Triển khai thành web/API để người dùng dán bài báo và nhận chủ đề."])

H("8. Hướng dẫn chạy")
P("pip install -r requirements.txt\npython train.py        # huấn luyện + sinh biểu đồ\npython app.py          # chạy website tại http://127.0.0.1:5000\npython predict.py \"nội dung bài báo\"\npython make_report.py  # sinh lại báo cáo")
H("9. Kết luận")
P(f"Hệ thống TF-IDF + Linear SVM đạt Accuracy {m['test_accuracy']:.1%} và Macro-F1 {m['test_macro_f1']:.1%} trên 11 chủ đề, huấn luyện chỉ vài giây trên CPU, "
  "đáp ứng mục tiêu phân loại tin tức tự động mà không cần tài nguyên tính toán lớn.")
H("Tài liệu tham khảo")
B(["Pedregosa et al., Scikit-learn: Machine Learning in Python, JMLR 12, 2011.", "Manning, Raghavan, Schütze. Introduction to Information Retrieval, Cambridge UP, 2008.",
   "Joachims, T. Text categorization with Support Vector Machines, ECML 1998."])
d.save(Path(__file__).parent / "BAO_CAO_DO_AN.docx")
