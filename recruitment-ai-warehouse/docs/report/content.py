"""Nội dung báo cáo (tiếng Việt, bản rút gọn ~40 trang). Mỗi khối gọi các hàm của ReportBuilder."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "docs" / "images"
SHOT = ROOT / "docs" / "report_images"

MEMBERS = [
    ("Nguyễn Phan Khánh Vy", "2431540032", "24ĐHTT01", "Nhóm trưởng"),
    ("Trần Phúc Hoàng", "2431540018", "24ĐHTT01", "Thành viên"),
    ("Đoàn Cường Thịnh", "2431540060", "24ĐHTT01", "Thành viên"),
    ("Đoàn Thiên Thiên Khánh", "2431540014", "24ĐHTT01", "Thành viên"),
]

ABBREVIATIONS = [
    ("AI", "Artificial Intelligence – Trí tuệ nhân tạo"),
    ("API", "Application Programming Interface – Giao diện lập trình ứng dụng"),
    ("ATS", "Applicant Tracking System – Hệ thống quản lý ứng viên"),
    ("BI", "Business Intelligence – Phân tích kinh doanh"),
    ("CSDL", "Cơ sở dữ liệu"),
    ("CV", "Curriculum Vitae – Hồ sơ năng lực"),
    ("ERD", "Entity Relationship Diagram – Sơ đồ thực thể liên kết"),
    ("ETL", "Extract – Transform – Load (Trích xuất – Biến đổi – Nạp)"),
    ("HR", "Human Resources – Bộ phận nhân sự"),
    ("JD", "Job Description – Bản mô tả công việc"),
    ("JWT", "JSON Web Token – Mã thông báo xác thực"),
    ("LLM", "Large Language Model – Mô hình ngôn ngữ lớn"),
    ("NLP", "Natural Language Processing – Xử lý ngôn ngữ tự nhiên"),
    ("PII", "Personally Identifiable Information – Thông tin định danh cá nhân"),
    ("PV", "Phỏng vấn"),
    ("RBAC", "Role-Based Access Control – Phân quyền theo vai trò"),
    ("SLA", "Service Level Agreement – Thời hạn xử lý cam kết của mỗi vòng"),
    ("TF-IDF", "Term Frequency – Inverse Document Frequency"),
]


def write(b) -> None:  # noqa: PLR0915
    F = lambda k: b.fig_no.get(k, "3.x")  # noqa: E731  số hình (lấy từ lượt dựng thử)
    T = lambda k: b.tab_no.get(k, "3.x")  # noqa: E731  số bảng

    # =================================================================== MỞ ĐẦU
    b.page_break()
    b.heading(1, "MỞ ĐẦU")
    b.para("Ở nhiều doanh nghiệp, dữ liệu tuyển dụng nằm rải rác trong câu trả lời Google Form, hộp thư tuyển dụng, hệ "
           "thống quản lý ứng viên (ATS) và các file Excel do từng chuyên viên nhân sự tự theo dõi. Vì không có một nguồn "
           "dữ liệu chung, bộ phận nhân sự khó biết nguồn tuyển nào hiệu quả, một hồ sơ mất bao lâu để đi hết quy trình, "
           "vòng nào đang tắc nghẽn hay vì sao ứng viên rớt hoặc tự rút hồ sơ.")
    b.para("Đề tài **“Kho dữ liệu tuyển dụng có AI phân tích pipeline ứng viên”** (Nhóm 8 – Đề tài AI 9) xây dựng sản "
           "phẩm web **TalentLens** bằng Python: ETL đa nguồn vào kho dữ liệu PostgreSQL, dashboard phân tích pipeline, AI "
           "(Claude và NLP) hỗ trợ tóm tắt CV, phân nhóm kỹ năng, tìm lý do rớt phổ biến, gợi ý câu hỏi phỏng vấn và viết "
           "báo cáo tuần. Hệ thống có phân quyền HR / hiring manager / admin, che thông tin cá nhân, chống thiên vị và luôn "
           "để con người kiểm duyệt nhận xét của AI. Báo cáo gồm Mở đầu, ba chương, Kết luận, tài liệu tham khảo và phụ lục.")

    # ============================================================ CHƯƠNG 1
    b.heading(1, "CHƯƠNG 1. GIỚI THIỆU", page_break=True)
    b.heading(2, "1.1. Lý do chọn đề tài")
    b.para("Doanh nghiệp ngày càng tuyển dụng qua nhiều kênh song song: TopCV, VietnamWorks, ITviec, LinkedIn, nhóm "
           "Facebook, website công ty, giới thiệu nội bộ, ngày hội việc làm và email. Mỗi kênh để lại dữ liệu ở một định "
           "dạng khác nhau. Cùng một ứng viên có thể xuất hiện ở nhiều nguồn với tên, số điện thoại, email viết khác nhau "
           "nên số liệu bị đếm trùng; các chỉ số như tỷ lệ chuyển đổi, thời gian xử lý, điểm nghẽn phải tổng hợp thủ công, "
           "tốn thời gian và dễ sai. Việc đọc hàng trăm CV và soạn câu hỏi phỏng vấn theo từng mô tả công việc cũng chiếm "
           "nhiều công sức của bộ phận nhân sự.")
    b.para("AI có thể hỗ trợ đọc hiểu văn bản rất tốt nhưng cũng tiềm ẩn rủi ro thiên vị – công cụ tuyển dụng thử nghiệm "
           "của Amazon từng bị ngừng vì đánh giá thấp hồ sơ của ứng viên nữ [9]. Pháp luật Việt Nam cấm phân biệt đối xử "
           "trong lao động [11] và yêu cầu bảo vệ dữ liệu cá nhân [12]. Vì vậy bài toán không chỉ là “dùng AI” mà là dùng "
           "AI có kiểm soát. Giải quyết được bài toán sẽ giúp HR có dữ liệu sạch để ra quyết định, quản lý phòng ban nắm "
           "được pipeline của mình, ban lãnh đạo có báo cáo định kỳ và ứng viên được đánh giá công bằng hơn; cách tiếp cận "
           "này cũng áp dụng được cho các quy trình nhiều bước khác như tuyển sinh hay xét duyệt hồ sơ.")
    b.heading(2, "1.2. Mục tiêu đề tài")
    b.para("TalentLens giúp **HR** gom dữ liệu tuyển dụng về một kho thống nhất, phân tích pipeline và dùng AI hỗ trợ xử "
           "lý CV; giúp **hiring manager** xem pipeline và ghi nhận kết quả phỏng vấn của phòng ban mình trên dữ liệu đã ẩn "
           "danh; giúp **admin** quản lý người dùng và nhật ký hệ thống. Kết quả cần đạt:")
    b.bullets([
        "ETL đọc 4 nguồn (CSV, JSON, XLSX, EML kèm CV), chuẩn hoá ứng viên, vị trí, nguồn, vòng, trạng thái và khử trùng.",
        "Kho dữ liệu PostgreSQL theo lược đồ hình sao, có DDL, ERD và truy vấn mẫu.",
        "Dashboard: phễu tuyển dụng, tỷ lệ chuyển đổi, thời gian xử lý, điểm nghẽn từng vòng, hiệu quả nguồn.",
        "AI: tóm tắt CV, phân nhóm kỹ năng, lý do rớt phổ biến, câu hỏi phỏng vấn theo JD, báo cáo tuần.",
        "Phân quyền, che dữ liệu nhạy cảm, chống thiên vị, kiểm duyệt AI; sản phẩm web hoàn chỉnh, triển khai online.",
    ])
    b.heading(2, "1.3. Phạm vi và đối tượng nghiên cứu")
    b.para("**Phạm vi:** quy trình tuyển dụng của một doanh nghiệp công nghệ (giả định) có 6 phòng ban, 10 vị trí, dữ liệu "
           "từ 08/2026 đến 11/2026. Do quy định bảo vệ dữ liệu cá nhân, nhóm dùng bộ dữ liệu **giả lập** có chủ đích chứa "
           "lỗi thường gặp; hệ thống vẫn nhận tệp thật cùng định dạng. Đề tài không xử lý CV ảnh scan (OCR) và đọc tệp xuất "
           "thay vì kết nối API trực tiếp với ATS/Gmail.")
    b.para("**Đối tượng nghiên cứu:** dữ liệu và quy trình tuyển dụng nhiều vòng cùng các chỉ số đo lường; kỹ thuật kho dữ "
           "liệu, ETL, định danh và khử trùng bản ghi; NLP và mô hình ngôn ngữ lớn cho CV tiếng Việt; phân quyền theo vai "
           "trò, ẩn danh dữ liệu, phát hiện thiên vị và kiểm duyệt có con người tham gia.")
    b.heading(2, "1.4. Phương pháp nghiên cứu")
    b.bullets([
        "**Thu thập thông tin:** đọc tài liệu về kho dữ liệu [1], [2], phân tích dữ liệu bằng Python [3], NLP [4], [6], "
        "LLM [5], phân quyền [7] và công bằng trong tuyển dụng tự động [8], [10]; tìm hiểu biểu mẫu Google Form, tệp xuất "
        "ATS và bảng theo dõi Excel thực tế.",
        "**Xử lý thông tin:** định lượng (tỷ lệ chuyển đổi, trung vị và P90 thời gian, quy tắc 4/5) và định tính (phân "
        "nhóm lý do rớt, nhận định điểm nghẽn).",
        "**Thực nghiệm:** sinh dữ liệu giả lập có đáp án biết trước (314 ứng viên, 329 hồ sơ) để kiểm tra ETL; 45 kiểm "
        "thử tự động bằng pytest; chạy thử toàn hệ thống trên trình duyệt với hai vai trò.",
    ])
    b.heading(2, "1.5. Phân công thực hiện")
    b.para("Nhóm có 4 thành viên nên hai nhóm công việc NLP/AI và phân quyền – báo cáo – triển khai được gộp cho một thành "
           f"viên (Bảng {T('phancong')}).")
    b.table("phancong", "1|Phân công nhiệm vụ của các thành viên",
            ["Thành viên", "Nhiệm vụ", "Sản phẩm / Demo"],
            [["Nguyễn Phan Khánh Vy (Nhóm trưởng)", "Task 1 – Phân tích bài toán, ETL và kiến trúc công nghệ",
              "Script ETL đa nguồn, API FastAPI, khung Streamlit – log ETL thành công"],
             ["Trần Phúc Hoàng", "Task 2 – Chuẩn hoá dữ liệu ứng viên và mô hình kho dữ liệu",
              "DDL, khử trùng – ERD và truy vấn mẫu"],
             ["Đoàn Cường Thịnh", "Task 3 – Dashboard phân tích pipeline tuyển dụng",
              "Tỷ lệ chuyển đổi, thời gian xử lý, điểm nghẽn – phễu tuyển dụng"],
             ["Đoàn Thiên Thiên Khánh", "Task 4 + 5 – NLP/AI xử lý CV; phân quyền, chống thiên vị, báo cáo, deploy",
              "Xử lý một CV mẫu; hai vai trò thấy dữ liệu khác nhau"]],
            [4.2, 6.0, 5.8])
    b.heading(2, "1.6. Bố cục đề tài")
    b.para("Chương 2 trình bày cơ sở lý thuyết: pipeline tuyển dụng và các chỉ số đo lường, kho dữ liệu và ETL, các công "
           "nghệ Python được sử dụng, xử lý ngôn ngữ tự nhiên và mô hình ngôn ngữ lớn, cùng các nguyên tắc phân quyền và sử "
           "dụng AI có trách nhiệm trong tuyển dụng. Chương 3 trình bày đóng góp chính là nền tảng TalentLens, gồm phân tích "
           "yêu cầu, kiến trúc, thiết kế ETL và kho dữ liệu, mô-đun AI và cơ chế chống thiên vị, các giao diện theo từng tác "
           "nhân, kết quả kiểm thử, thực nghiệm và triển khai. Phần Kết luận tổng kết kết quả, hạn chế và hướng phát triển.")

    # ============================================================ CHƯƠNG 2
    b.heading(1, "CHƯƠNG 2. CƠ SỞ LÝ THUYẾT", page_break=True)
    b.para("Bài toán kết hợp kỹ thuật dữ liệu (ETL, kho dữ liệu), phân tích (BI, dashboard) và AI (NLP, LLM) trong một "
           "ứng dụng web xử lý dữ liệu cá nhân. Chương này trình bày lần lượt các nền tảng đó.")
    b.heading(2, "2.1. Pipeline tuyển dụng và các chỉ số đo lường")
    b.para("Pipeline tuyển dụng là chuỗi các vòng mà hồ sơ đi qua: nộp hồ sơ → sàng lọc CV → phỏng vấn HR → phỏng vấn "
           "chuyên môn → phỏng vấn cuối → offer → nhận việc. Ở mỗi vòng, hồ sơ có thể đạt, bị loại, vắng mặt hoặc ứng viên "
           "tự rút. Số hồ sơ giảm dần qua từng vòng nên pipeline thường biểu diễn bằng **biểu đồ phễu**. Gọi N(i) là số hồ "
           "sơ đã đi tới vòng i, các chỉ số chính được định nghĩa như sau:")
    b.formula("Tỷ lệ chuyển đổi (i → i+1) = N(i+1) / N(i) × 100%")
    b.formula("Tỷ lệ qua vòng i = N(i+1) / [N(i+1) + số bị loại ở vòng i + số rút ở vòng i] × 100%")
    b.formula("Thời gian chuyển vòng i = thời điểm vào vòng i+1 − thời điểm vào vòng i")
    b.para("Thời gian được tóm tắt bằng **trung vị** và **P90** vì phân phối thường lệch phải; mỗi vòng có một **SLA** "
           "(số ngày xử lý cam kết). **Điểm nghẽn** là vòng có tỷ lệ qua thấp nhất (nghẽn chất lượng) hoặc vòng có thời "
           "gian vượt SLA nhiều nhất (nghẽn năng lực xử lý). Ngoài ra hệ thống đo time-to-hire (từ nộp hồ sơ đến nhận "
           "việc), tỷ lệ nhận offer và tỷ lệ tuyển của từng nguồn.")
    b.heading(2, "2.2. Kho dữ liệu, lược đồ hình sao và ETL")
    b.para("Kho dữ liệu được Inmon định nghĩa là tập dữ liệu hướng chủ đề, tích hợp, ổn định theo thời gian, phục vụ ra "
           "quyết định [2]; Kimball đề xuất mô hình hoá chiều với **lược đồ hình sao** [1]: bảng **sự kiện** (fact) ở trung "
           "tâm chứa các sự kiện đo lường được (một hồ sơ, một lần chuyển vòng) cùng khoá ngoại tới các bảng **chiều** "
           "(dimension) như ứng viên, vị trí, nguồn, vòng, ngày. Ưu điểm là truy vấn đơn giản và nhanh; nhược điểm là cần "
           "quy trình nạp chặt chẽ để dữ liệu nhất quán.")
    b.para("**ETL** gồm trích xuất dữ liệu thô, biến đổi (làm sạch, chuẩn hoá, ánh xạ mã, kiểm tra ràng buộc) và nạp vào "
           "kho. Thực tiễn tốt giữ vùng **staging** để truy vết và đảm bảo ETL **idempotent** – chạy lại không sinh trùng. "
           "Khi tích hợp nhiều nguồn cần **định danh thực thể** (entity resolution) [13]: chuẩn hoá các trường định danh "
           "rồi so khớp theo thứ tự khoá tin cậy, khớp thì gộp và bổ sung thông tin còn thiếu.")
    b.heading(2, "2.3. Ngôn ngữ Python và các công nghệ sử dụng")
    b.para("Python (Guido van Rossum, 1991) có cú pháp rõ ràng và hệ sinh thái dữ liệu – AI rất lớn; các thư viện tính toán "
           "lõi viết bằng C nên đáp ứng tốt quy mô đề tài. Bảng 2.1 tóm tắt các công nghệ chính [15]. Xác thực dùng **JSON Web "
           "Token** (RFC 7519): sau khi đăng nhập, máy chủ cấp token có chữ ký HMAC-SHA256 chứa mã người dùng, vai trò, hạn "
           "dùng; mật khẩu được băm PBKDF2-SHA256 có muối.")
    b.table("congnghe", "2|Các công nghệ chính và vai trò trong hệ thống",
            ["Công nghệ", "Đặc điểm", "Vai trò trong đề tài"],
            [["pandas [3], openpyxl, pypdf, python-docx", "Xử lý bảng dữ liệu; đọc Excel, PDF, DOCX",
              "Extract/Transform trong ETL, tính chỉ số pipeline"],
             ["PostgreSQL 16 + SQLAlchemy 2", "CSDL quan hệ mã nguồn mở, JSONB, hàm cửa sổ; ORM Python",
              "Kho dữ liệu lược đồ hình sao, truy vấn phân tích"],
             ["FastAPI (2018)", "Framework ASGI, kiểm tra dữ liệu bằng Pydantic, tự sinh OpenAPI/Swagger",
              "REST API, xác thực JWT, phân quyền bằng dependency"],
             ["Streamlit (2019) + Plotly", "Ứng dụng web dữ liệu thuần Python; biểu đồ tương tác",
              "Dashboard, màn hình nghiệp vụ, menu theo vai trò"],
             ["scikit-learn [4]", "Thư viện học máy: TF-IDF, cosine", "Độ tương đồng nội dung CV – JD"],
             ["Anthropic SDK – Claude", "LLM, structured outputs theo JSON Schema", "Tóm tắt CV, câu hỏi PV, nhận định"],
             ["pytest, Docker, Render", "Kiểm thử tự động; đóng gói; nền tảng đám mây", "Đảm bảo chất lượng, deploy"]],
            [4.4, 6.0, 5.6])
    b.heading(2, "2.4. Xử lý ngôn ngữ tự nhiên và mô hình ngôn ngữ lớn")
    b.para("Văn bản tiếng Việt được **chuẩn hoá** trước khi so khớp: Unicode NFC, chữ thường, bỏ dấu (“Phỏng vấn” → "
           "“phong van”, “đ” → “d”), bỏ ký tự đặc biệt. Kỹ năng được trích bằng **từ điển kỹ năng**: mỗi kỹ năng chuẩn có "
           "danh sách từ đồng nghĩa được tìm theo ranh giới từ – minh bạch và nhất quán, phù hợp với tuyển dụng. **TF-IDF** "
           "[6] biểu diễn văn bản bằng véc-tơ trọng số; độ tương đồng CV – JD đo bằng cosine:")
    b.formula("tfidf(t, d) = tf(t, d) × log( N / df(t) ) ;   cos(a, b) = (a · b) / (‖a‖ × ‖b‖)")
    b.para("**Mô hình ngôn ngữ lớn** dựa trên kiến trúc Transformer [5] hiểu và sinh ngôn ngữ tự nhiên, phù hợp cho tóm "
           "tắt, trích xuất, viết báo cáo. Claude của Anthropic được gọi qua Messages API [14]; tính năng **structured "
           "outputs** ràng buộc câu trả lời theo JSON Schema để chương trình đọc ổn định. Do LLM có thể “ảo giác” và mang "
           "thiên kiến, đề tài chỉ dùng LLM cho phần diễn giải, còn các chỉ số định lượng vẫn tính bằng mã nguồn.")
    b.heading(2, "2.5. Phân quyền, bảo vệ dữ liệu cá nhân và AI có trách nhiệm")
    b.para("Mô hình **RBAC** [7] gán quyền cho vai trò thay vì cho từng người, giúp quản lý nhất quán và tuân thủ nguyên "
           "tắc đặc quyền tối thiểu; kết hợp với **che giấu dữ liệu** (masking) để chỉ hiển thị một phần thông tin cho "
           "người không cần biết. Nghị định 13/2023/NĐ-CP quy định xử lý dữ liệu cá nhân phải có mục đích rõ ràng và hạn "
           "chế ở mức cần thiết [12]; Bộ luật Lao động 2019 cấm phân biệt đối xử theo giới tính, dân tộc, tôn giáo, tình "
           "trạng hôn nhân, mang thai… [11]. Trong khi đó CV ở Việt Nam thường ghi ngày sinh, giới tính, hôn nhân, quê quán.")
    b.para("Nghiên cứu về tuyển dụng bằng thuật toán cho thấy hệ thống có thể tái tạo thiên kiến lịch sử [10]. Công cụ giám "
           "sát phổ biến là **quy tắc 4/5** [8]: nếu tỷ lệ được chọn của một nhóm thấp hơn 80% tỷ lệ của nhóm cao nhất thì "
           "cần xem xét. Đề tài áp dụng nguyên tắc **human-in-the-loop**: AI chỉ tóm tắt và gợi ý, không chấm điểm hay "
           "quyết định; dữ liệu nhạy cảm bị loại trước khi gửi AI; mọi nhận xét AI phải được người phụ trách kiểm duyệt.")
    b.formula("Tỷ lệ tác động = min(tỷ lệ qua các nhóm) / max(tỷ lệ qua các nhóm);  cảnh báo khi < 0,8")

    # ============================================================ CHƯƠNG 3
    b.heading(1, "CHƯƠNG 3. PHÂN TÍCH HỆ THỐNG VÀ XÂY DỰNG SẢN PHẨM", page_break=True)
    b.heading(2, "3.1. Phân tích hệ thống")
    b.heading(3, "3.1.1. Hiện trạng và dữ liệu đầu vào")
    b.para("Doanh nghiệp giả định có 6 phòng ban và 10 vị trí đang tuyển. Khối Công nghệ và Dữ liệu dùng ATS cho phần lớn "
           "hồ sơ, các phòng khác theo dõi bằng Excel; ứng viên từ website, Facebook, ngày hội việc làm, giới thiệu điền "
           f"Google Form; một số gửi email trực tiếp. Bảng {T('nguon')} mô tả các nguồn và lỗi dữ liệu điển hình.")
    b.table("nguon", "3|Các nguồn dữ liệu đầu vào và vấn đề chất lượng",
            ["Nguồn", "Nội dung", "Vấn đề chất lượng điển hình"],
            [["Google Form (.csv)", "Thông tin cá nhân, vị trí, kênh, kinh nghiệm, kỹ năng, lương, tệp CV",
              "Tên viết thường, email viết hoa/thừa khoảng trắng, SĐT +84, “1-2 năm”, “15tr”"],
             ["ATS (.json)", "Danh mục vị trí + JD; hồ sơ; lịch sử từng vòng, người PV, điểm",
              "Tên tách họ/tên, thời gian có múi giờ, điểm “4/5”, trạng thái chưa cập nhật"],
             ["Excel HR (.xlsx)", "Ngày từng vòng, kết quả, trạng thái, lý do loại/rút",
              "Tiêu đề không ở dòng 1, SĐT mất số 0, tên không dấu, dòng nhập trùng"],
             ["Email (.eml + CV)", "Email ứng tuyển kèm CV; email xin rút hồ sơ",
              "Thông tin trong văn bản tự do; email rút hồ sơ cập nhật cho hồ sơ ở nguồn khác"]],
            [3.0, 6.2, 6.8])
    b.heading(3, "3.1.2. Yêu cầu chức năng và phi chức năng")
    b.table("yc", "3|Yêu cầu chức năng của hệ thống",
            ["Chức năng", "Mô tả", "Task"],
            [["Nhập dữ liệu (ETL)", "Tải tệp CSV/JSON/XLSX/EML/CV; chuẩn hoá, khử trùng, nạp kho; xem log, bản ghi bị loại", "1, 2"],
             ["Quản lý hồ sơ", "Tìm kiếm, lọc; chi tiết hồ sơ, hành trình các vòng, CV; ghi nhận kết quả vòng", "2, 3"],
             ["Dashboard pipeline", "KPI, phễu, tỷ lệ qua vòng, thời gian so với SLA, điểm nghẽn, nguồn, xu hướng", "3"],
             ["AI xử lý CV", "Trích văn bản, ẩn danh, tóm tắt, phân nhóm kỹ năng, độ phủ JD, câu hỏi PV, lý do rớt", "4"],
             ["Kiểm duyệt AI, báo cáo tuần", "Duyệt/sửa/từ chối nhận xét AI; tạo, duyệt, tải báo cáo tuần", "5"],
             ["Phân quyền & công bằng", "JWT, 3 vai trò, che PII, bias guard, quy tắc 4/5", "5"],
             ["Quản trị", "Quản lý người dùng, nhật ký hệ thống", "5"]],
            [4.0, 10.4, 1.6])
    b.para("Yêu cầu phi chức năng: **bảo mật** (băm mật khẩu, JWT có hạn, kiểm tra quyền phía máy chủ, ghi nhật ký xem "
           "thông tin cá nhân); **công bằng** (ẩn danh CV trước khi gửi AI, AI không chấm điểm người); **tin cậy** (ETL "
           "idempotent, Claude lỗi thì tự chuyển sang engine NLP nội bộ); **hiệu năng** (ETL 500 bản ghi + 185 CV trong vài "
           "giây); **triển khai** (Docker, cấu hình bằng biến môi trường, URL công khai).")
    b.heading(3, "3.1.3. Tác nhân, use case và phân quyền")
    b.para("**HR** quản lý toàn bộ dữ liệu, chạy ETL và AI, kiểm duyệt nhận xét AI và báo cáo. **Hiring manager** chỉ xem "
           "dữ liệu phòng ban mình ở dạng đã che, ghi nhận kết quả phỏng vấn, xem nhận xét AI và báo cáo đã duyệt. **Admin** "
           f"có quyền của HR và thêm quản lý người dùng, nhật ký (Hình {F('usecase')}, Bảng {T('rbac')}).")
    b.figure("usecase", IMG / "use_case.png", "3|Sơ đồ use case theo tác nhân", max_h_cm=9.5)
    b.table("rbac", "3|Ma trận phân quyền theo vai trò",
            ["Chức năng / dữ liệu", "Admin", "HR", "Hiring manager"],
            [["Phạm vi dữ liệu", "Toàn công ty", "Toàn công ty", "Phòng ban của mình"],
             ["Họ tên, email, SĐT, giới tính, ngày sinh, nơi ở", "Đầy đủ", "Đầy đủ", "Bị che"],
             ["Chạy ETL, chạy AI, giám sát công bằng", "Có", "Có", "Không"],
             ["Xem / kiểm duyệt nhận xét AI", "Tất cả / Có", "Tất cả / Có", "Bản đã duyệt / Không"],
             ["Ghi nhận kết quả phỏng vấn", "Có", "Có", "Có (phòng ban mình)"],
             ["Báo cáo tuần", "Tạo, duyệt", "Tạo, duyệt", "Xem bản đã duyệt"],
             ["Quản lý người dùng, nhật ký", "Có", "Không", "Không"]],
            [6.4, 2.8, 2.8, 4.0])
    b.heading(3, "3.1.4. Kiến trúc tổng thể")
    b.para(f"Hệ thống gồm 5 lớp (Hình {F('kientruc')}): nguồn dữ liệu rời rạc → ETL Python → kho PostgreSQL (staging, "
           "bảng chiều, bảng sự kiện, bảng vận hành) → backend FastAPI (xác thực – RBAC, phân tích, dịch vụ AI, báo cáo, "
           "ETL API) → giao diện Streamlit. Dịch vụ AI gọi Claude khi có API key, ngược lại dùng engine NLP nội bộ.")
    b.figure("kientruc", IMG / "kien_truc.png", "3|Kiến trúc tổng thể hệ thống TalentLens")
    b.heading(3, "3.1.5. Thiết kế quy trình ETL và khử trùng")
    b.para(f"Quy trình gồm 7 bước (Hình {F('etl')}). **Extract:** mỗi định dạng có bộ đọc riêng; Excel được dò tự động "
           "dòng tiêu đề, email được phân tích kèm CV đính kèm. **Staging:** bản ghi thô lưu vào stg_raw_record cùng vân tay "
           "SHA-256; bản ghi đã nạp sẽ được bỏ qua ở lần sau. **Transform:** đưa về một cấu trúc chuẩn theo các quy tắc ở "
           f"Bảng {T('chuanhoa')}; giá trị phân loại được ánh xạ theo 3 tầng: khớp chính xác sau chuẩn hoá → khớp cụm từ dài "
           "nhất → khớp gần đúng (difflib). **Validate:** loại bản ghi thiếu họ tên, thiếu cả email lẫn SĐT, không xác định "
           "được vị trí hoặc thiếu ngày nộp, kèm lý do.")
    b.figure("etl", IMG / "quy_trinh_etl.png", "3|Quy trình ETL đa nguồn và khử trùng ứng viên")
    b.table("chuanhoa", "3|Một số quy tắc chuẩn hoá dữ liệu",
            ["Trường", "Ví dụ dữ liệu nguồn", "Giá trị chuẩn"],
            [["Họ tên / email", "“nguyễn văn AN”; “ AN.NGUYEN@GMAIL.COM ”", "Nguyễn Văn An; an.nguyen@gmail.com"],
             ["Số điện thoại", "+84 912 345 678; 912345678; 0912.345.678", "0912345678"],
             ["Ngày giờ", "15/09/2026 10:22; 2026-09-15T09:00+07:00; serial Excel", "datetime giờ Việt Nam"],
             ["Kinh nghiệm / lương", "“1-2 năm”, “Fresher”; “15tr”, “15.000.000”", "1,5 / 0 năm; 15 triệu"],
             ["Vị trí / nguồn", "“DA”, “QC/Tester”; “topcv.vn”, “Bạn bè giới thiệu”", "DA-2026, QA-2026; TOPCV, REFERRAL"],
             ["Vòng / trạng thái", "“CV Screening”, “PV kỹ thuật”; “Không đạt”, “Rút hồ sơ”",
              "SCREENING, TECH_INTERVIEW; rejected, withdrawn"]],
            [3.4, 7.2, 5.4])
    b.para("**Định danh** (trọng tâm Task 2): mỗi bản ghi được so khớp với ứng viên đã có theo **email → số điện thoại → "
           "họ tên không dấu + ngày sinh**; khớp thì gộp, bổ sung trường thiếu, giữ CV dài hơn, ưu tiên tên có dấu và lưu "
           "danh tính đã gộp để truy vết. Cặp (ứng viên, vị trí) là duy nhất: hồ sơ xuất hiện ở nhiều nguồn được gộp, giữ "
           "ngày nộp sớm nhất và nguồn chạm đầu tiên, hợp nhất sự kiện từng vòng. Email rút hồ sơ được xử lý sau cùng như "
           "bản cập nhật. **Load và hậu xử lý** tính lại vòng hiện tại, thời lượng từng vòng, trích kỹ năng, phân loại lý "
           "do rớt, quét cờ thiên vị và ghi log vào etl_run (trích đoạn log lần chạy đầu):")
    b.code("""[20:22:43] START     ETL run #1 – 26 tệp dữ liệu, 185 tệp CV/khác
[20:22:43] EXTRACT   Tổng bản ghi thô: ATS (vị trí)=10, ATS=191, Email=23, Form=117, Excel=159
[20:22:46] WARN      Loại hr_tracking.xlsx bản ghi 162: không xác định được vị trí
[20:22:48] TRANSFORM Hợp lệ 485 | bị loại 5 | bỏ qua do đã nạp trước đó 0
[20:22:48] LOAD      dim_candidate: +314 ứng viên mới, gộp 160 bản ghi trùng (email=158, SĐT=2)
[20:22:48] LOAD      fact_application: +329 hồ sơ mới, 145 hồ sơ trùng được gộp, 11 cập nhật
[20:22:48] DONE      Hoàn tất sau 5.9s – trạng thái: PARTIAL""")
    b.heading(3, "3.1.6. Thiết kế kho dữ liệu")
    b.para(f"Kho dữ liệu theo lược đồ hình sao (Hình {F('erd')}) với hai bảng sự kiện: **fact_application** (một hồ sơ "
           "của một ứng viên vào một vị trí, ràng buộc UNIQUE(candidate_id, position_id)) và **fact_stage_event** (một lần "
           "hồ sơ đi qua một vòng: vào/ra, kết quả, thời lượng, người PV, điểm, nhận xét, cờ thiên vị). Bảng chiều gồm "
           "dim_candidate (thuộc tính nhạy cảm tách riêng), dim_position (JD, kỹ năng bắt buộc), dim_department, dim_source, "
           "dim_stage (thứ tự, SLA), dim_date; bảng vận hành gồm app_user, ai_insight, weekly_report, audit_log và vùng "
           "staging stg_raw_record, etl_run. DDL đầy đủ ở sql/schema.sql; 10 truy vấn mẫu ở sql/sample_queries.sql, ví dụ "
           "truy vấn tỷ lệ chuyển đổi dùng hàm cửa sổ LEAD:")
    b.figure("erd", IMG / "erd.png", "3|Sơ đồ ERD kho dữ liệu tuyển dụng (lược đồ hình sao)", max_h_cm=11)
    b.code("""WITH reached AS (SELECT s.stage_order, s.name, COUNT(DISTINCT e.application_id) AS n
                 FROM fact_stage_event e JOIN dim_stage s ON s.id = e.stage_id
                 GROUP BY s.stage_order, s.name)
SELECT name, LEAD(name) OVER (ORDER BY stage_order) AS den_vong, n,
       ROUND(100.0 * LEAD(n) OVER (ORDER BY stage_order) / n, 1) AS ty_le_chuyen_doi
FROM reached ORDER BY stage_order;
-- Kết quả: 329 → 321 (97,6%) → 176 (54,8%) → 96 (54,5%) → 44 (45,8%) → 37 (84,1%) → 24 (64,9%)""")
    b.heading(3, "3.1.7. Thiết kế mô-đun AI và cơ chế chống thiên vị")
    b.para("Mô-đun AI có hai engine cùng giao diện: **ClaudeEngine** (Anthropic SDK, mô hình mặc định claude-opus-5-5, "
           "đầu ra theo JSON Schema, fallback phía máy chủ khi bị từ chối) và **LocalEngine** (NLP nội bộ). Nếu Claude lỗi, "
           f"hệ thống tự chuyển sang LocalEngine và ghi chú lại. Luồng xử lý có kiểm duyệt ở Hình {F('aiflow')}:")
    b.figure("aiflow", IMG / "quy_trinh_ai.png", "3|Quy trình AI có kiểm duyệt và chống thiên vị")
    b.bullets([
        "**Trích văn bản & ẩn danh:** pypdf/python-docx; loại dòng có nhãn nhạy cảm (họ tên, ngày sinh, giới tính, hôn "
        "nhân, địa chỉ, quê quán, tôn giáo…) và thay email, SĐT, link, ngày tháng, tên bằng nhãn giữ chỗ.",
        "**Tóm tắt & kỹ năng:** từ điển 14 nhóm, khoảng 100 kỹ năng; độ phủ JD = số kỹ năng bắt buộc có trong CV / tổng "
        "số kỹ năng bắt buộc – chỉ tham khảo, không phải điểm xếp hạng.",
        "**Câu hỏi phỏng vấn:** chuyên môn, làm rõ kỹ năng JD còn thiếu, làm rõ thành tích, tình huống, hành vi (STAR), kèm "
        "mục đích, tín hiệu trả lời tốt và danh sách chủ đề cấm hỏi.",
        "**Lý do rớt:** phân vào 12 nhóm bằng luật từ khoá (kinh nghiệm, kỹ năng, lương, offer nơi khác, quy trình kéo "
        "dài…), tổng hợp theo vòng kèm đề xuất cải tiến. **Báo cáo tuần:** số liệu tuần này so với tuần trước + nhận định.",
        "**Chống thiên vị:** bias guard quét nhận xét của AI và của người phỏng vấn theo 7 nhóm thuộc tính được bảo vệ "
        "(giới tính, tuổi, hôn nhân/thai sản, vùng miền, tôn giáo/dân tộc, ngoại hình, sức khoẻ); nhận xét AI luôn ở "
        "trạng thái Chờ duyệt, nội dung bị gắn cờ phải sửa hoặc ghi chú mới được duyệt.",
        "**Phân quyền:** dependency require(permission) trên từng API; phạm vi phòng ban áp ngay trong truy vấn; serializer "
        "che PII (mã ứng viên + viết tắt, email n***@gmail.com); audit log ghi thao tác quan trọng.",
    ])

    # ---------------------------------------------------------------- 3.2 Giao diện
    b.heading(2, "3.2. Xây dựng giao diện sản phẩm")
    b.para("Giao diện Streamlit gồm 10 trang, menu được tạo động theo quyền nên mỗi vai trò chỉ thấy chức năng được phép. "
           "Người dùng đăng nhập bằng tài khoản được cấp (JWT); trang đăng nhập có mục tài khoản demo phục vụ chấm điểm.")
    b.heading(3, "3.2.1. Dashboard pipeline tuyển dụng (HR)")
    b.para("Phía trên là bộ lọc dùng chung (thời gian, phòng ban, vị trí, nguồn) và các ô KPI; khối **Điểm nghẽn** liệt kê "
           "cảnh báo tự động; **phễu tuyển dụng** (demo Task 3) cho thấy 329 hồ sơ còn 24 người nhận việc (7,3%), vòng có tỷ "
           "lệ qua thấp nhất là phỏng vấn chuyên môn (47,3%).")
    b.figure("dash1", SHOT / "f02_dash_top.jpg", "3|Dashboard – KPI, điểm nghẽn và phễu tuyển dụng")
    b.para("Biểu đồ thời gian chuyển vòng so sánh trung vị với SLA (vạch đen): bước “PV HR → PV chuyên môn” mất 7,0 ngày "
           "so với SLA 4 ngày, 76% hồ sơ vượt SLA – điểm nghẽn về lịch phỏng vấn chuyên môn. Bên dưới là xu hướng theo "
           "tuần; tiếp theo là hiệu quả nguồn (TopCV nhiều hồ sơ nhất – 92 – nhưng tỷ lệ tuyển chỉ 4,3%, LinkedIn 13,9%), "
           "phân bố lý do loại/rút và pipeline theo vị trí.")
    b.figure("dash2", SHOT / "f03_dash_duration.jpg", "3|Dashboard – thời gian chuyển vòng so với SLA và xu hướng tuần")
    b.figure("dash3", SHOT / "f04_dash_source.jpg", "3|Dashboard – hiệu quả nguồn tuyển dụng")
    b.heading(3, "3.2.2. Nhập dữ liệu (ETL)")
    b.para("Demo Task 1: HR tải lên tệp (có thể kèm bộ dữ liệu mẫu) và bấm Chạy ETL; kết quả hiển thị các chỉ số và log. "
           f"Hình {F('etlui')} là lần nạp bổ sung 4 câu trả lời Form: tạo 2 ứng viên mới, nhận ra 1 ứng viên đã có (email "
           "viết hoa, SĐT +84, tên không dấu) để gộp và loại 1 bản ghi thiếu liên hệ.")
    b.figure("etlui", SHOT / "f06_etl.jpg", "3|Nhập dữ liệu đa nguồn và log ETL")
    b.heading(3, "3.2.3. Quản lý ứng viên và hồ sơ")
    b.para("HR tìm kiếm, lọc theo vị trí, vòng, trạng thái, hồ sơ quá SLA; chọn một dòng để xem 5 thẻ: Hồ sơ (liên hệ, "
           "kỹ năng đã phân nhóm, bản ghi trùng đã gộp), Hành trình tuyển dụng, CV, Nhận xét AI và Ghi nhận kết quả vòng.")
    b.figure("cand", SHOT / "f07_cand_profile.jpg", "3|Danh sách hồ sơ và thông tin ứng viên (vai trò HR)")
    b.figure("journey", SHOT / "f08_cand_journey.jpg", "3|Hành trình tuyển dụng của một hồ sơ qua các vòng")
    b.heading(3, "3.2.4. AI phân tích CV và gợi ý câu hỏi phỏng vấn")
    b.para("Demo Task 4: HR chọn vị trí cần đối chiếu, tải lên CV (PDF/DOCX/TXT) hoặc chọn CV mẫu. Kết quả gồm tóm tắt, "
           "điểm nổi bật có bằng chứng, điểm cần làm rõ, độ phủ kỹ năng JD, phân nhóm kỹ năng, danh sách thông tin đã ẩn và "
           "văn bản CV đã ẩn danh (dữ liệu AI thực sự nhận được). Thẻ câu hỏi phỏng vấn sinh bộ câu hỏi có cấu trúc theo JD; "
           "thẻ lý do rớt phân tích 269 hồ sơ bị loại/rút (nhiều nhất: kinh nghiệm chưa phù hợp 33,8%, thiếu kỹ năng 29,0%).")
    b.figure("aicv1", SHOT / "f10_ai_cv_a.jpg", "3|AI phân tích một CV mẫu – tóm tắt và đối chiếu JD")
    b.figure("aicv2", SHOT / "f11_ai_cv_b.jpg", "3|Phân nhóm kỹ năng và văn bản CV đã ẩn danh gửi cho AI")
    b.figure("aiq", SHOT / "f12_ai_questions.jpg", "3|Gợi ý câu hỏi phỏng vấn có cấu trúc theo JD")
    b.figure("airej", SHOT / "f13_ai_rejection.jpg", "3|Phân tích lý do rớt phổ biến và đề xuất cải tiến")
    b.heading(3, "3.2.5. Kiểm duyệt nhận xét AI và báo cáo tuần")
    b.para("HR lọc nhận xét theo trạng thái và loại, xem nội dung và cờ thiên vị, có thể chỉnh sửa rồi Duyệt hoặc Từ chối "
           "(nhận xét đã xử lý có thể mở lại). Báo cáo tuần gồm tóm tắt, bảng chỉ số so với tuần trước, điểm nổi bật, điểm "
           "nghẽn, hành động đề xuất; ở trạng thái Bản nháp đến khi HR duyệt và có thể tải Markdown/HTML.")
    b.figure("review", SHOT / "f14_review.jpg", "3|Kiểm duyệt nhận xét AI")
    b.figure("report", SHOT / "f16_report.jpg", "3|Báo cáo pipeline tuần do hệ thống tạo")
    b.heading(3, "3.2.6. Giám sát công bằng và cảnh báo thiên vị")
    b.para("Trang giám sát công bằng hiển thị tỷ lệ qua vòng theo giới tính và tỷ lệ tác động: vòng phỏng vấn chuyên môn có "
           "tỷ lệ 0,70 (nam 42,3% – 26 hồ sơ, nữ 60,6% – 33 hồ sơ) nên được đánh dấu “cần xem xét” – tín hiệu để rà soát, "
           "chưa phải kết luận. Bộ lọc đã phát hiện 3 nhận xét phỏng vấn thiên vị trong dữ liệu nhập về. Khi người dùng nhập "
           "nhận xét dựa trên thuộc tính được bảo vệ, hệ thống chặn lưu và chỉ rõ cụm từ vi phạm.")
    b.figure("fair", SHOT / "f15_fairness.jpg", "3|Giám sát công bằng theo quy tắc 4/5")
    b.figure("biaswarn", SHOT / "f20_bias_warning.jpg", "3|Cảnh báo khi nhận xét phỏng vấn có nội dung thiên vị")
    b.heading(3, "3.2.7. Hai vai trò thấy dữ liệu khác nhau (hiring manager)")
    b.para("Demo Task 5: tài khoản quản lý khối Dữ liệu & AI chỉ thấy menu được phép, dashboard tự giới hạn 106 hồ sơ của "
           "3 vị trí (HR thấy 331 hồ sơ toàn công ty), danh sách và chi tiết ứng viên ở chế độ ẩn danh, chỉ thấy nhận xét "
           f"AI và báo cáo đã được HR duyệt (Bảng {T('haivaitro')}).")
    b.figure("mgrdash", SHOT / "f17_mgr_dash.jpg", "3|Dashboard của hiring manager – chỉ dữ liệu phòng ban mình")
    b.figure("mgrdetail", SHOT / "f19_mgr_detail.jpg", "3|Chi tiết ứng viên dưới góc nhìn hiring manager (đã che PII)")
    b.table("haivaitro", "3|So sánh dữ liệu hiển thị cho HR và hiring manager",
            ["Nội dung", "HR (hr.lan)", "Hiring manager (manager.data)"],
            [["Phạm vi hồ sơ", "Toàn công ty – 331 hồ sơ, 10 vị trí", "Khối Dữ liệu & AI – 106 hồ sơ, 3 vị trí"],
             ["Tên ứng viên (cùng một người)", "Phan Thị Mỹ Duyên", "UV-00316 · P.T.M.D."],
             ["Email / SĐT", "duyen.phan01@gmail.com / 0386555777", "d***@gmail.com / 03******77"],
             ["Giới tính, ngày sinh, nơi ở; CV", "Hiển thị; nguyên bản", "Ẩn; đã ẩn danh"],
             ["Nhận xét AI", "Tất cả (kể cả chờ duyệt)", "Chỉ bản đã duyệt"],
             ["Gọi /api/users, /api/etl/runs…", "Được phép (trừ quản lý người dùng)", "HTTP 403"]],
            [4.6, 5.4, 6.0])
    b.heading(3, "3.2.8. Quản trị người dùng và nhật ký")
    b.para("Admin xem danh sách tài khoản và ma trận phân quyền, tạo tài khoản (hiring manager bắt buộc gắn phòng ban), đổi "
           "vai trò/phòng ban, khoá tài khoản, đặt lại mật khẩu; trang nhật ký liệt kê các thao tác quan trọng.")
    b.figure("users", SHOT / "f22_users.jpg", "3|Quản lý người dùng và ma trận phân quyền")

    # ---------------------------------------------------------------- 3.3 Kiểm thử & triển khai
    b.heading(2, "3.3. Kiểm thử, thực nghiệm và triển khai")
    b.para("Bộ kiểm thử pytest chạy trên CSDL PostgreSQL riêng, nạp dữ liệu mẫu qua đúng luồng khởi động của ứng dụng; kết "
           f"quả **45/45 ca đạt** trong khoảng 11 giây (Bảng {T('test')}). Bộ dữ liệu mẫu có đáp án biết trước: 314 ứng viên "
           f"và 329 hồ sơ thật được rải thành 500 bản ghi thô ở 4 nguồn kèm 185 CV; kết quả ETL ở Bảng {T('thucnghiem')}.")
    b.table("test", "3|Kết quả kiểm thử tự động",
            ["Tệp kiểm thử", "Số ca", "Nội dung kiểm tra", "Kết quả"],
            [["test_normalize.py", "26", "Chuẩn hoá SĐT, email, tên, ngày giờ, kinh nghiệm, lương, điểm; ánh xạ nguồn, vòng, "
              "trạng thái, vị trí", "Đạt"],
             ["test_etl.py", "4", "Khôi phục đúng 314/329, không email trùng, email rút hồ sơ, chạy lại không sinh trùng", "Đạt"],
             ["test_ai.py", "6", "Kỹ năng, ẩn danh, bias guard, phân loại lý do, engine nội bộ, lời gọi Claude (giả lập)", "Đạt"],
             ["test_api.py", "9", "Hai vai trò khác nhau, 403, dashboard, kiểm duyệt AI, chặn thiên vị, báo cáo, người dùng",
              "Đạt"]],
            [3.2, 1.4, 9.6, 1.8])
    b.table("thucnghiem", "3|Kết quả ETL trên bộ dữ liệu mẫu",
            ["Chỉ tiêu", "Kết quả"],
            [["Bản ghi thô → hợp lệ / bị loại", "500 → 485 / 5 (2 vị trí lạ, 1 thiếu tên, 1 thiếu liên hệ, 1 email không khớp)"],
             ["Ứng viên sau khử trùng", "314 – đúng đáp án (gộp 160 bản ghi trùng: 158 theo email, 2 theo SĐT)"],
             ["Hồ sơ ứng tuyển", "329 – đúng đáp án (145 bản ghi hồ sơ trùng được gộp)"],
             ["Trạng thái", "36 đang xử lý, 24 nhận việc, 221 bị loại, 48 rút (11 hồ sơ chỉ biết qua email) – khớp"],
             ["Chạy lại cùng dữ liệu", "0 bản ghi mới (idempotent); thời gian chạy ≈ 6 giây"]],
            [5.0, 11.0])
    b.para(f"**Triển khai online** (Hình {F('deploy')}): một Dockerfile dùng chung, biến SERVICE chọn chạy API, giao diện "
           "hoặc cả hai. Tệp render.yaml mô tả một CSDL PostgreSQL và hai dịch vụ web trên Render; khi đẩy mã lên GitHub, "
           "Render tự build và cấp URL HTTPS công khai; lần khởi động đầu API tự tạo bảng, tài khoản demo và nạp dữ liệu "
           "mẫu. Phương án khác: Hugging Face Spaces + Neon PostgreSQL hoặc docker compose trên máy chủ riêng (docs/DEPLOY.md). "
           "Địa chỉ sản phẩm: ……………………………………………… (nhóm điền URL sau khi triển khai).")
    b.figure("deploy", IMG / "trien_khai.png", "3|Sơ đồ triển khai online")
    b.table("danhgia", "3|Đánh giá mức độ đáp ứng yêu cầu",
            ["Yêu cầu", "Kết quả", "Mức độ"],
            [["Task 1 – ETL đa nguồn, FastAPI, Streamlit", "4 nguồn + CV, staging, log; 34 endpoint; 10 trang", "Đạt"],
             ["Task 2 – DDL, chuẩn hoá, khử trùng", "14 bảng, schema.sql, 10 truy vấn mẫu, đúng 314/329", "Đạt"],
             ["Task 3 – Chuyển đổi, thời gian, điểm nghẽn", "Phễu, SLA, 4 quy tắc điểm nghẽn, nguồn, xu hướng", "Đạt"],
             ["Task 4 – CV, kỹ năng, lý do rớt, câu hỏi PV", "Claude + engine NLP nội bộ, demo CV mẫu", "Đạt"],
             ["Task 5 – RBAC, ẩn PII, kiểm duyệt, báo cáo, deploy", "3 vai trò, che PII, bias guard, Docker/Render", "Đạt"],
             ["Web hoàn chỉnh, đăng nhập, quản lý user, URL online", "Đủ chức năng; đã chuẩn bị cấu hình deploy",
              "Cần nhóm deploy"]],
            [6.0, 7.0, 3.0])

    # ============================================================ KẾT LUẬN
    b.heading(1, "KẾT LUẬN", page_break=True)
    b.heading(2, "1. Kết quả đạt được")
    b.para("Đề tài đã xây dựng TalentLens – sản phẩm web hoàn chỉnh viết bằng Python, đáp ứng các mục tiêu ở Chương 1. "
           "Hệ thống hợp nhất bốn nguồn rời rạc vào kho PostgreSQL theo lược đồ hình sao; ETL chuẩn hoá lỗi định dạng, khử "
           "trùng ứng viên, chống nạp trùng và ghi log, khôi phục chính xác 314 ứng viên và 329 hồ sơ từ 500 bản ghi thô. "
           "Dashboard cung cấp phễu, tỷ lệ qua vòng, thời gian so với SLA, điểm nghẽn tự động, hiệu quả nguồn và lý do rớt. "
           "Mô-đun AI tóm tắt CV, phân nhóm kỹ năng, gợi ý câu hỏi phỏng vấn, phân tích lý do rớt và viết báo cáo tuần với "
           "hai engine (Claude và NLP nội bộ). Về an toàn, hệ thống có phân quyền ba vai trò, che thông tin cá nhân, ẩn danh "
           "CV trước khi gửi AI, bộ lọc thiên vị, kiểm duyệt bắt buộc, giám sát công bằng và nhật ký kiểm toán; chất lượng mã "
           "nguồn được đảm bảo bằng 45 kiểm thử tự động. Bài học rút ra: chất lượng dữ liệu quyết định chất lượng phân tích, "
           "ETL phải chạy lại được an toàn, và AI trong nhân sự luôn cần cơ chế để con người kiểm soát.")
    b.heading(2, "2. Hạn chế")
    b.bullets([
        "Dữ liệu thực nghiệm là giả lập, chưa kiểm chứng trên dữ liệu tuyển dụng thật.",
        "Engine NLP nội bộ dựa trên luật nên tóm tắt còn đơn giản; dùng Claude cần API key (có chi phí); chưa có bộ đánh "
        "giá định lượng chất lượng tóm tắt.",
        "Chưa hỗ trợ CV ảnh scan (OCR), chưa kết nối trực tiếp API của ATS/Gmail; giám sát công bằng mới xét giới tính.",
    ])
    b.heading(2, "3. Hướng phát triển")
    b.para("Trước mắt: triển khai chính thức và theo dõi vận hành, bổ sung OCR, lập lịch ETL hằng ngày, gửi báo cáo tuần "
           "qua email, lưu lịch sử trạng thái để báo cáo quá khứ chính xác. Lâu dài: kết nối API của ATS, Gmail, Google "
           "Sheets; xây dựng bộ đánh giá chất lượng AI; mở rộng giám sát công bằng với kiểm định thống kê; dự báo thời gian "
           "tuyển và khả năng ứng viên rút hồ sơ bằng học máy.")

    # ============================================================ TÀI LIỆU THAM KHẢO
    b.heading(1, "DANH MỤC TÀI LIỆU THAM KHẢO", page_break=True)
    refs = [
        "R. Kimball and M. Ross, *The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling*, 3rd ed. "
        "Indianapolis, IN, USA: Wiley, 2013.",
        "W. H. Inmon, *Building the Data Warehouse*, 4th ed. Indianapolis, IN, USA: Wiley, 2005.",
        "W. McKinney, *Python for Data Analysis*, 3rd ed. Sebastopol, CA, USA: O’Reilly Media, 2022.",
        "F. Pedregosa et al., “Scikit-learn: Machine learning in Python,” *Journal of Machine Learning Research*, vol. "
        "12, pp. 2825–2830, 2011.",
        "A. Vaswani et al., “Attention is all you need,” in *Advances in Neural Information Processing Systems 30 "
        "(NIPS 2017)*, 2017, pp. 5998–6008.",
        "G. Salton and C. Buckley, “Term-weighting approaches in automatic text retrieval,” *Information Processing & "
        "Management*, vol. 24, no. 5, pp. 513–523, 1988.",
        "R. S. Sandhu, E. J. Coyne, H. L. Feinstein, and C. E. Youman, “Role-based access control models,” *IEEE "
        "Computer*, vol. 29, no. 2, pp. 38–47, 1996.",
        "Equal Employment Opportunity Commission et al., “Uniform Guidelines on Employee Selection Procedures,” 29 CFR "
        "Part 1607, 1978.",
        "J. Dastin, “Amazon scraps secret AI recruiting tool that showed bias against women,” *Reuters*, Oct. 10, 2018.",
        "M. Raghavan, S. Barocas, J. Kleinberg, and K. Levy, “Mitigating bias in algorithmic hiring: Evaluating claims "
        "and practices,” in *Proc. FAT* ’20*, 2020, pp. 469–481.",
        "Quốc hội nước CHXHCN Việt Nam, *Bộ luật Lao động*, Luật số 45/2019/QH14, 2019.",
        "Chính phủ nước CHXHCN Việt Nam, *Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân*, 17/4/2023.",
        "P. Christen, *Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate "
        "Detection*. Berlin, Germany: Springer, 2012.",
        "Anthropic, “Claude API documentation.” [Online]. Available: https://docs.anthropic.com (truy cập 11/2026).",
        "FastAPI, PostgreSQL 16, Streamlit, SQLAlchemy 2.0, Plotly – tài liệu chính thức. [Online]. Available: "
        "fastapi.tiangolo.com, postgresql.org/docs/16, docs.streamlit.io, docs.sqlalchemy.org, plotly.com/python "
        "(truy cập 11/2026).",
    ]
    for i, ref in enumerate(refs, start=1):
        b.para(f"[{i}] {ref}", style="ThamKhao")

    # ============================================================ PHỤ LỤC
    b.heading(1, "PHỤ LỤC", page_break=True)
    b.heading(2, "Phụ lục A. Cài đặt, chạy hệ thống và tài khoản demo")
    b.code("""cd recruitment-ai-warehouse
pip install -r requirements.txt
cp .env.example .env                  # sửa DATABASE_URL, JWT_SECRET, ANTHROPIC_API_KEY (tuỳ chọn)
uvicorn app.main:app --port 8000      # lần đầu tự tạo bảng, tài khoản demo, nạp dữ liệu mẫu
streamlit run frontend/app.py         # mở http://localhost:8501
docker compose up --build             # hoặc chạy toàn bộ bằng Docker
pytest -q                             # 45 kiểm thử (cần TEST_DATABASE_URL)""")
    b.table("taikhoan", "PL|Tài khoản demo",
            ["Tài khoản", "Mật khẩu", "Vai trò", "Phạm vi"],
            [["admin", "Admin@123", "Quản trị", "Toàn bộ + người dùng, nhật ký"],
             ["hr.lan", "Demo@123", "HR", "Toàn công ty, có thông tin cá nhân"],
             ["manager.data", "Demo@123", "Hiring manager", "Khối Dữ liệu & AI, dữ liệu đã che"],
             ["manager.tech", "Demo@123", "Hiring manager", "Khối Công nghệ, dữ liệu đã che"]],
            [3.2, 2.8, 3.6, 6.4])
    b.heading(2, "Phụ lục B. Cấu trúc mã nguồn")
    b.code("""recruitment-ai-warehouse/
├── app/            Backend FastAPI: etl/ (extract, normalize, transform, load, pipeline)
│                   ai/ (skills, anonymizer, bias_guard, cv_parser, rejection, engines, service)
│                   services/ (analytics, reports, audit), routers/, models.py, rbac.py, security.py
├── frontend/       Streamlit: app.py + views/ (10 trang)
├── data/raw/       Dữ liệu mẫu 4 nguồn + 185 CV
├── sql/            schema.sql (DDL), sample_queries.sql
├── scripts/        Sinh dữ liệu mẫu, xuất DDL
├── tests/          45 kiểm thử pytest
├── docs/           Sơ đồ, hướng dẫn triển khai, báo cáo
└── Dockerfile, docker-compose.yml, render.yaml, start.sh, requirements.txt""")
