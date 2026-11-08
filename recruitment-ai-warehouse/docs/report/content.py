"""Nội dung báo cáo (tiếng Việt). Mỗi khối gọi các hàm của ReportBuilder."""
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
    ("BI", "Business Intelligence – Phân tích kinh doanh thông minh"),
    ("CSDL", "Cơ sở dữ liệu"),
    ("CV", "Curriculum Vitae – Hồ sơ năng lực / sơ yếu lý lịch"),
    ("DDL", "Data Definition Language – Ngôn ngữ định nghĩa dữ liệu"),
    ("ERD", "Entity Relationship Diagram – Sơ đồ thực thể liên kết"),
    ("ETL", "Extract – Transform – Load: Trích xuất – Biến đổi – Nạp dữ liệu"),
    ("HR", "Human Resources – Bộ phận nhân sự"),
    ("HS", "Hồ sơ ứng tuyển"),
    ("JD", "Job Description – Bản mô tả công việc"),
    ("JSON", "JavaScript Object Notation – Định dạng trao đổi dữ liệu"),
    ("JWT", "JSON Web Token – Mã thông báo xác thực"),
    ("KPI", "Key Performance Indicator – Chỉ số đo lường hiệu quả"),
    ("LLM", "Large Language Model – Mô hình ngôn ngữ lớn"),
    ("NLP", "Natural Language Processing – Xử lý ngôn ngữ tự nhiên"),
    ("ORM", "Object Relational Mapping – Ánh xạ đối tượng – quan hệ"),
    ("PII", "Personally Identifiable Information – Thông tin định danh cá nhân"),
    ("PV", "Phỏng vấn"),
    ("RBAC", "Role-Based Access Control – Phân quyền theo vai trò"),
    ("REST", "Representational State Transfer – Kiến trúc dịch vụ web"),
    ("SLA", "Service Level Agreement – Thời hạn xử lý cam kết cho mỗi vòng"),
    ("SQL", "Structured Query Language – Ngôn ngữ truy vấn có cấu trúc"),
    ("TF-IDF", "Term Frequency – Inverse Document Frequency"),
    ("UI/UX", "User Interface / User Experience – Giao diện / Trải nghiệm người dùng"),
    ("UV", "Ứng viên"),
]


def write(b) -> None:  # noqa: PLR0915
    # =================================================================== MỞ ĐẦU
    b.page_break()
    b.heading(1, "MỞ ĐẦU")
    b.para("Tuyển dụng là hoạt động then chốt quyết định chất lượng nguồn nhân lực của doanh nghiệp. Tuy vậy, ở nhiều "
           "doanh nghiệp vừa và nhỏ tại Việt Nam, dữ liệu tuyển dụng vẫn nằm rải rác ở nhiều nơi: câu trả lời Google "
           "Form, hộp thư tuyển dụng, hệ thống quản lý ứng viên (ATS) và các file Excel do từng chuyên viên nhân sự tự "
           "theo dõi. Khi dữ liệu không thống nhất, bộ phận nhân sự khó trả lời những câu hỏi rất cơ bản như: nguồn "
           "tuyển nào mang lại ứng viên tốt nhất, một hồ sơ mất bao lâu để đi hết quy trình, vòng nào đang làm tắc "
           "nghẽn pipeline, hay vì sao ứng viên rớt hoặc tự rút hồ sơ.")
    b.para("Đề tài **“Kho dữ liệu tuyển dụng có AI phân tích pipeline ứng viên”** (Nhóm 8 – Đề tài AI 9) xây dựng "
           "sản phẩm web hoàn chỉnh tên **TalentLens** bằng ngôn ngữ Python. Hệ thống thực hiện quy trình ETL đa nguồn "
           "để chuẩn hoá và khử trùng dữ liệu ứng viên vào kho dữ liệu PostgreSQL theo lược đồ hình sao; cung cấp "
           "dashboard phân tích pipeline (tỷ lệ chuyển đổi, thời gian xử lý, điểm nghẽn từng vòng); ứng dụng NLP và mô "
           "hình ngôn ngữ lớn Claude để tóm tắt CV, phân nhóm kỹ năng, phát hiện lý do rớt phổ biến, gợi ý câu hỏi phỏng "
           "vấn theo JD và soạn báo cáo pipeline hàng tuần.")
    b.para("Bên cạnh hiệu quả phân tích, đề tài đặc biệt chú trọng tính **có trách nhiệm** của AI trong tuyển dụng: "
           "phân quyền HR / hiring manager / quản trị viên, che giấu thông tin cá nhân, ẩn danh CV trước khi gửi cho AI, "
           "bộ lọc phát hiện nhận xét thiên vị và luồng kiểm duyệt bắt buộc để con người luôn là người quyết định "
           "cuối cùng. Sản phẩm được đóng gói Docker và có cấu hình triển khai online trên nền tảng đám mây.")
    b.para("Báo cáo gồm phần Mở đầu, ba chương nội dung, phần Kết luận, Danh mục tài liệu tham khảo và Phụ lục. Bảng "
           "1.1 trong Chương 1 trình bày phân công nhiệm vụ của các thành viên theo năm nhóm công việc của đề tài.")

    # ============================================================ CHƯƠNG 1
    b.heading(1, "CHƯƠNG 1. GIỚI THIỆU", page_break=True)
    b.heading(2, "1.1. Lý do chọn đề tài")
    b.para("Trong bối cảnh chuyển đổi số, doanh nghiệp ngày càng tuyển dụng qua nhiều kênh song song: trang việc làm "
           "(TopCV, VietnamWorks, ITviec), mạng xã hội (LinkedIn, các nhóm Facebook), website tuyển dụng của công ty, "
           "giới thiệu nội bộ, ngày hội việc làm và email ứng tuyển trực tiếp. Mỗi kênh để lại dữ liệu ở một định dạng "
           "khác nhau. Dữ liệu từ form ứng tuyển là các dòng CSV; dữ liệu từ ATS là tệp JSON; tiến độ phỏng vấn thường "
           "được nhân viên nhân sự cập nhật thủ công trên Excel; còn email ứng tuyển và email xin rút hồ sơ chỉ nằm "
           "trong hộp thư.")
    b.para("Sự phân tán này gây ra nhiều vấn đề thực tế. Thứ nhất, một ứng viên có thể xuất hiện ở nhiều nguồn với tên, "
           "số điện thoại, email được viết theo những cách khác nhau, khiến số liệu bị đếm trùng và đánh giá sai hiệu "
           "quả nguồn. Thứ hai, không có một “nguồn sự thật” chung nên rất khó đo lường tỷ lệ chuyển đổi qua từng vòng, "
           "thời gian xử lý hay vòng nào đang là điểm nghẽn; báo cáo tuần thường phải tổng hợp thủ công, tốn thời gian "
           "và dễ sai sót. Thứ ba, việc đọc hàng trăm CV, tổng hợp lý do ứng viên rớt hay soạn câu hỏi phỏng vấn phù "
           "hợp với từng mô tả công việc chiếm nhiều công sức của bộ phận nhân sự.")
    b.para("Các công cụ trí tuệ nhân tạo hiện nay có khả năng hỗ trợ đọc hiểu văn bản rất tốt, nhưng việc đưa AI vào "
           "tuyển dụng cũng tiềm ẩn rủi ro thiên vị. Trường hợp công cụ tuyển dụng thử nghiệm của Amazon bị ngừng sử dụng "
           "vì đánh giá thấp hồ sơ của ứng viên nữ [11] là một ví dụ điển hình. Pháp luật Việt Nam cũng nghiêm cấm phân "
           "biệt đối xử trong lao động [13] và yêu cầu bảo vệ dữ liệu cá nhân [14]. Vì vậy, bài toán đặt ra không chỉ "
           "là “dùng AI” mà là dùng AI có kiểm soát: dữ liệu nhạy cảm phải được che giấu, nhận xét của AI phải được "
           "người phụ trách kiểm duyệt và quyền truy cập phải phân theo vai trò.")
    b.para("Nếu giải quyết được, bài toán đem lại lợi ích cho nhiều đối tượng: bộ phận nhân sự có dữ liệu sạch và "
           "dashboard để ra quyết định; quản lý tuyển dụng (hiring manager) nắm được tình trạng pipeline của phòng ban "
           "mình; ban lãnh đạo nhận báo cáo định kỳ; còn ứng viên được đánh giá công bằng hơn và được phản hồi nhanh hơn. "
           "Cách tiếp cận kho dữ liệu kết hợp AI có kiểm duyệt cũng có thể áp dụng cho các lĩnh vực có quy trình nhiều "
           "bước tương tự như tuyển sinh, chăm sóc khách hàng hay quản lý hồ sơ tín dụng. Đó là lý do nhóm lựa chọn đề "
           "tài này cho học phần Lập trình Python.")

    b.heading(2, "1.2. Mục tiêu đề tài")
    b.para("**Hệ thống làm gì và cho ai?** TalentLens là ứng dụng web giúp **bộ phận nhân sự (HR)** gom dữ liệu tuyển "
           "dụng từ nhiều nguồn về một kho dữ liệu thống nhất, theo dõi và phân tích pipeline ứng viên, sử dụng AI để hỗ "
           "trợ xử lý CV; giúp **quản lý tuyển dụng** của từng phòng ban xem pipeline và ghi nhận kết quả phỏng vấn cho "
           "các vị trí của mình trên dữ liệu đã được ẩn danh; và giúp **quản trị viên** quản lý người dùng, phân quyền và "
           "giám sát nhật ký hệ thống.")
    b.para("**Kết quả cần đạt về sản phẩm:**")
    b.bullets([
        "Quy trình ETL đọc được bốn loại nguồn (Google Form – CSV, ATS – JSON, Excel HR – XLSX, email – EML kèm CV "
        "PDF/DOCX/TXT), chuẩn hoá ứng viên, vị trí, nguồn, vòng phỏng vấn, trạng thái; khử trùng ứng viên; ghi log ETL.",
        "Kho dữ liệu PostgreSQL theo lược đồ hình sao, có DDL, ERD và bộ truy vấn mẫu.",
        "Dashboard pipeline: phễu tuyển dụng, tỷ lệ chuyển đổi, thời gian xử lý, điểm nghẽn từng vòng, hiệu quả nguồn.",
        "Mô-đun NLP/AI: trích văn bản CV, tóm tắt, phân nhóm kỹ năng, lý do rớt phổ biến, gợi ý câu hỏi phỏng vấn theo "
        "JD, báo cáo tuần.",
        "Phân quyền HR / hiring manager / admin, che thông tin nhạy cảm, chống chấm điểm thiên vị, kiểm duyệt nhận xét "
        "AI, quản lý người dùng; sản phẩm web hoàn chỉnh, có thể triển khai online với URL truy cập.",
    ])
    b.para("**Kết quả cần đạt về công nghệ:** vận dụng ngôn ngữ Python và hệ sinh thái thư viện (pandas, SQLAlchemy, "
           "FastAPI, Streamlit, Plotly, scikit-learn, Anthropic SDK) để xây dựng một hệ thống nhiều lớp; hiểu và áp dụng "
           "các khái niệm kho dữ liệu, ETL, BI, NLP, mô hình ngôn ngữ lớn, RBAC và kiểm thử tự động.")

    b.heading(2, "1.3. Phạm vi đề tài")
    b.bullets([
        "**Không gian:** quy trình tuyển dụng của một doanh nghiệp công nghệ quy mô vừa (giả định) có 6 phòng ban, 10 "
        "vị trí đang tuyển, tuyển dụng tại TP. Hồ Chí Minh, Hà Nội và Đà Nẵng.",
        "**Thời gian dữ liệu:** các hồ sơ ứng tuyển từ tháng 08/2026 đến tháng 11/2026; thời gian thực hiện đề tài "
        "trong học kỳ của học phần.",
        "**Dữ liệu:** do quy định bảo vệ dữ liệu cá nhân, nhóm không sử dụng CV thật mà xây dựng bộ dữ liệu **giả lập** "
        "có chủ đích chứa các lỗi thường gặp (trùng lặp, sai định dạng, thiếu thông tin). Hệ thống vẫn nhận tệp thật "
        "theo cùng định dạng qua chức năng tải lên.",
        "**Lĩnh vực:** HR Analytics – phân tích pipeline tuyển dụng; không bao gồm các nghiệp vụ sau tuyển dụng như "
        "tính lương, hợp đồng, đánh giá nhân viên.",
        "**Giới hạn kỹ thuật:** CV dạng ảnh scan (cần OCR) chưa được hỗ trợ; ETL đọc tệp xuất từ ATS/Excel/hộp thư thay "
        "vì kết nối API trực tiếp tới từng hệ thống bên ngoài.",
    ])

    b.heading(2, "1.4. Đối tượng nghiên cứu")
    b.bullets([
        "Dữ liệu tuyển dụng: ứng viên, vị trí, nguồn tuyển, các vòng phỏng vấn, trạng thái, lý do loại/rút hồ sơ, CV.",
        "Quy trình (pipeline) tuyển dụng nhiều vòng và các chỉ số đo lường: tỷ lệ chuyển đổi, thời gian xử lý, SLA, "
        "điểm nghẽn, hiệu quả nguồn.",
        "Kỹ thuật kho dữ liệu và ETL: lược đồ hình sao, staging, chuẩn hoá, định danh và khử trùng bản ghi.",
        "Kỹ thuật NLP và mô hình ngôn ngữ lớn trong xử lý CV tiếng Việt: trích xuất văn bản, từ điển kỹ năng, TF-IDF, "
        "phân loại văn bản dựa trên luật, structured outputs của Claude.",
        "Các biện pháp an toàn: phân quyền theo vai trò, che giấu và ẩn danh dữ liệu cá nhân, phát hiện thiên vị, "
        "kiểm duyệt có con người tham gia (human-in-the-loop), nhật ký kiểm toán.",
    ])

    b.heading(2, "1.5. Phương pháp nghiên cứu")
    b.bullets([
        "**Phương pháp thu thập thông tin:** đọc tài liệu về kho dữ liệu [1], [2], phân tích dữ liệu bằng Python [3], "
        "xử lý văn bản [4], [6], mô hình ngôn ngữ lớn [5], phân quyền [7], [8] và công bằng trong tuyển dụng tự động "
        "[10], [12]; tìm hiểu biểu mẫu thực tế của Google Form, tệp xuất ATS và bảng theo dõi tuyển dụng trên Excel.",
        "**Phương pháp xử lý thông tin:** định lượng (tính tỷ lệ chuyển đổi, trung vị và phân vị 90 của thời gian xử lý, "
        "tỷ lệ tác động bất lợi theo quy tắc 4/5) và định tính (phân nhóm lý do rớt, nhận định về điểm nghẽn).",
        "**Phương pháp thực nghiệm:** sinh bộ dữ liệu giả lập có “đáp án” biết trước (314 ứng viên, 329 hồ sơ) để kiểm "
        "tra độ chính xác của ETL; xây dựng 45 kiểm thử tự động bằng pytest; chạy thử toàn bộ hệ thống trên PostgreSQL "
        "và trình duyệt với hai vai trò khác nhau.",
        "**Phương pháp phát triển phần mềm:** chia đề tài thành 5 nhóm công việc, phát triển lặp theo từng mô-đun, quản "
        "lý mã nguồn bằng Git/GitHub, đóng gói bằng Docker để triển khai.",
    ])

    b.heading(2, "1.6. Phân công thực hiện")
    b.para("Nhóm có 4 thành viên nên hai nhóm công việc “NLP/AI xử lý CV” và “Phân quyền, chống thiên vị, báo cáo, "
           "triển khai” được gộp cho một thành viên. Bảng 1.1 trình bày nội dung phụ trách và sản phẩm demo tương ứng.")
    b.table("phancong", "1|Phân công nhiệm vụ của các thành viên",
            ["Thành viên", "Nhiệm vụ", "Nội dung chính", "Demo"],
            [["Nguyễn Phan Khánh Vy\n(Nhóm trưởng)", "Task 1 – Phân tích bài toán, ETL và kiến trúc công nghệ",
              "Script ETL đa nguồn vào PostgreSQL, API FastAPI, khung Streamlit", "Log ETL thành công"],
             ["Trần Phúc Hoàng", "Task 2 – Chuẩn hoá dữ liệu ứng viên và mô hình kho dữ liệu",
              "DDL ứng viên/vị trí/nguồn/vòng/trạng thái, khử trùng", "ERD và truy vấn mẫu"],
             ["Đoàn Cường Thịnh", "Task 3 – Dashboard phân tích pipeline tuyển dụng",
              "Tỷ lệ chuyển đổi, thời gian xử lý, điểm nghẽn từng vòng, biểu đồ", "Phễu tuyển dụng"],
             ["Đoàn Thiên Thiên Khánh", "Task 4 + 5 – NLP/AI xử lý CV; phân quyền, chống thiên vị, báo cáo và triển khai",
              "Tóm tắt CV, phân nhóm kỹ năng, lý do rớt, câu hỏi PV; RBAC, ẩn thông tin nhạy cảm, kiểm duyệt AI, báo "
              "cáo tuần, deploy", "Xử lý một CV mẫu; hai vai trò thấy dữ liệu khác nhau"]],
            [3.2, 4.2, 5.4, 3.2])

    b.heading(2, "1.7. Bố cục đề tài")
    b.para("Phần còn lại của báo cáo được tổ chức như sau. Chương 2 trình bày cơ sở lý thuyết làm nền tảng cho hệ "
           "thống, bắt đầu từ bài toán pipeline tuyển dụng và các chỉ số đo lường, tiếp theo là khái niệm kho dữ liệu, "
           "lược đồ hình sao và quy trình ETL, sau đó giới thiệu ngôn ngữ Python cùng các thư viện, hệ quản trị PostgreSQL, "
           "framework FastAPI, Streamlit và Plotly, các kỹ thuật xử lý ngôn ngữ tự nhiên và mô hình ngôn ngữ lớn, và cuối "
           "cùng là các nguyên tắc phân quyền, bảo vệ dữ liệu cá nhân và sử dụng AI có trách nhiệm trong tuyển dụng.")
    b.para("Chương 3 trình bày đóng góp chính của đề tài, đó là nền tảng TalentLens. Phần phân tích hệ thống xác định "
           "các yêu cầu chức năng và phi chức năng, tác nhân và use case, kiến trúc tổng thể, thiết kế quy trình ETL với "
           "thuật toán định danh và khử trùng ứng viên, thiết kế kho dữ liệu, các chỉ số phân tích, mô-đun AI và các cơ "
           "chế chống thiên vị. Phần xây dựng sản phẩm mô tả từng giao diện theo tác nhân sử dụng, tiếp theo là kết quả "
           "kiểm thử, kết quả thực nghiệm trên bộ dữ liệu mẫu và phương án triển khai online. Phần Kết luận tổng kết "
           "những gì đã đạt được, những hạn chế còn tồn tại và hướng phát triển của hệ thống.")

    # ============================================================ CHƯƠNG 2
    b.heading(1, "CHƯƠNG 2. CƠ SỞ LÝ THUYẾT", page_break=True)
    b.para("Bài toán của đề tài là sự kết hợp của ba mảng: kỹ thuật dữ liệu (ETL, kho dữ liệu), phân tích kinh doanh "
           "(BI, dashboard) và trí tuệ nhân tạo (NLP, mô hình ngôn ngữ lớn), đặt trong một ứng dụng web có yêu cầu bảo "
           "mật cao vì xử lý dữ liệu cá nhân. Do đó, chương này lần lượt trình bày lý thuyết về pipeline tuyển dụng – "
           "đối tượng cần phân tích; kho dữ liệu và ETL – cách tổ chức dữ liệu; các công nghệ Python dùng để hiện thực; "
           "NLP và mô hình ngôn ngữ lớn – phần AI; và cuối cùng là các nguyên tắc phân quyền, bảo vệ dữ liệu, AI có trách "
           "nhiệm – điều kiện để đưa AI vào tuyển dụng một cách an toàn.")

    b.heading(2, "2.1. Pipeline tuyển dụng và các chỉ số đo lường")
    b.heading(3, "2.1.1. Khái niệm pipeline tuyển dụng")
    b.para("Pipeline tuyển dụng (recruitment pipeline) là chuỗi các vòng mà một hồ sơ ứng tuyển đi qua kể từ khi nộp "
           "đến khi ứng viên nhận việc hoặc dừng lại. Một quy trình điển hình gồm: nộp hồ sơ → sàng lọc CV → phỏng vấn "
           "nhân sự (HR) → phỏng vấn chuyên môn → phỏng vấn cuối với quản lý → đề nghị nhận việc (offer) → nhận việc. Ở "
           "mỗi vòng, hồ sơ có thể đạt và đi tiếp, bị loại, vắng mặt hoặc do ứng viên chủ động rút. Vì số hồ sơ giảm dần "
           "qua từng vòng nên pipeline thường được biểu diễn bằng **biểu đồ phễu** (funnel).")
    b.para("Hệ thống quản lý ứng viên (ATS – Applicant Tracking System) là phần mềm ghi nhận các vòng này. Tuy nhiên "
           "nhiều doanh nghiệp chỉ dùng ATS cho một số vị trí, phần còn lại theo dõi bằng Excel; dữ liệu đầu vào lại đến "
           "từ form và email. Đây chính là bối cảnh “dữ liệu rời rạc” mà đề tài giải quyết.")
    b.heading(3, "2.1.2. Các chỉ số pipeline")
    b.para("Để đánh giá hiệu quả quy trình, đề tài sử dụng các chỉ số phổ biến trong HR Analytics được định nghĩa thống "
           "nhất trong Bảng 2.1. Gọi N(i) là số hồ sơ đã đi tới vòng i, ta có:")
    b.formula("Tỷ lệ chuyển đổi (i → i+1) = N(i+1) / N(i) × 100%")
    b.formula("Tỷ lệ qua vòng i = N(i+1) / [N(i+1) + Số bị loại ở vòng i + Số rút ở vòng i] × 100%")
    b.formula("Thời gian chuyển vòng i = thời điểm vào vòng i+1 − thời điểm vào vòng i")
    b.formula("Tỷ lệ tuyển của nguồn s = Số nhận việc từ nguồn s / Số hồ sơ từ nguồn s × 100%")
    b.table("kpi", "2|Các chỉ số pipeline tuyển dụng sử dụng trong hệ thống",
            ["Chỉ số", "Ý nghĩa", "Dùng để"],
            [["Phễu tuyển dụng", "Số hồ sơ đi tới từng vòng", "Nhìn tổng quan quy mô và mức sụt giảm"],
             ["Tỷ lệ chuyển đổi / qua vòng", "Tỷ lệ hồ sơ đi tiếp sang vòng sau", "Phát hiện vòng loại nhiều nhất"],
             ["Thời gian chuyển vòng (trung vị, P90)", "Thời gian hồ sơ nằm ở một vòng trước khi chuyển tiếp",
              "So sánh với SLA, phát hiện vòng chậm"],
             ["SLA từng vòng", "Thời hạn xử lý cam kết (ngày)", "Cảnh báo hồ sơ quá hạn"],
             ["Time-to-hire", "Số ngày từ khi nộp hồ sơ đến khi nhận việc", "Đo tốc độ tuyển dụng"],
             ["Tỷ lệ nhận offer", "Số nhận việc / số offer đã có kết quả", "Đánh giá sức hấp dẫn của offer"],
             ["Hiệu quả nguồn", "Số hồ sơ, tỷ lệ qua sàng lọc, tỷ lệ tuyển theo nguồn", "Phân bổ ngân sách kênh"],
             ["Lý do loại / rút", "Phân nhóm lý do theo vòng", "Cải tiến JD, quy trình, chính sách lương"]],
            [3.6, 5.6, 4.8])
    b.para("Trong phân tích thời gian, đề tài ưu tiên dùng **trung vị** thay vì trung bình vì phân phối thời gian xử lý "
           "thường lệch phải (một số hồ sơ bị bỏ quên rất lâu sẽ kéo trung bình lên); phân vị 90 (P90) cho biết thời gian "
           "mà 90% hồ sơ được xử lý xong. **Điểm nghẽn** (bottleneck) được hiểu theo hai nghĩa: vòng có tỷ lệ qua thấp "
           "nhất (nghẽn về chất lượng đầu vào) và vòng có thời gian chuyển tiếp vượt SLA nhiều nhất (nghẽn về năng lực "
           "xử lý). Hồ sơ đang ở một vòng lâu hơn SLA được gọi là hồ sơ quá hạn.")

    b.heading(2, "2.2. Kho dữ liệu và quy trình ETL")
    b.heading(3, "2.2.1. Lịch sử và khái niệm kho dữ liệu")
    b.para("Khái niệm kho dữ liệu (data warehouse) được W. H. Inmon phổ biến từ đầu thập niên 1990, định nghĩa là “một "
           "tập hợp dữ liệu hướng chủ đề, tích hợp, ổn định theo thời gian và không bị thay đổi, phục vụ việc ra quyết "
           "định” [2]. Song song, R. Kimball đề xuất phương pháp **mô hình hoá chiều** (dimensional modeling) với lược "
           "đồ hình sao, nhấn mạnh việc tổ chức dữ liệu sao cho người dùng nghiệp vụ dễ truy vấn [1]. Khác với cơ sở dữ "
           "liệu giao dịch (OLTP) tối ưu cho việc ghi từng bản ghi, kho dữ liệu (OLAP) tối ưu cho việc đọc, tổng hợp và "
           "phân tích lượng lớn dữ liệu lịch sử.")
    b.heading(3, "2.2.2. Lược đồ hình sao: bảng sự kiện và bảng chiều")
    b.para("Lược đồ hình sao gồm một hoặc nhiều **bảng sự kiện** (fact) ở trung tâm, chứa các sự kiện đo lường được "
           "(ví dụ một hồ sơ ứng tuyển, một lần chuyển vòng) cùng khoá ngoại tới các **bảng chiều** (dimension) mô tả "
           "ngữ cảnh: ai (ứng viên), cái gì (vị trí), từ đâu (nguồn), khi nào (ngày), ở vòng nào. Bảng chiều thời gian "
           "(dim_date) cho phép nhóm dữ liệu theo ngày, tuần, tháng, quý mà không phải tính toán lại. Ưu điểm của lược "
           "đồ hình sao là truy vấn đơn giản, hiệu năng tốt, dễ hiểu với người làm báo cáo; nhược điểm là có thể dư thừa "
           "dữ liệu ở bảng chiều và cần quy trình nạp dữ liệu chặt chẽ để đảm bảo nhất quán.")
    b.heading(3, "2.2.3. Quy trình ETL và chất lượng dữ liệu")
    b.para("ETL (Extract – Transform – Load) là quy trình đưa dữ liệu từ hệ thống nguồn vào kho: **trích xuất** dữ liệu "
           "thô, **biến đổi** (làm sạch, chuẩn hoá định dạng, ánh xạ mã, kiểm tra ràng buộc) và **nạp** vào các bảng "
           "đích. Một biến thể là ELT – nạp dữ liệu thô trước rồi biến đổi bên trong kho. Thực tiễn tốt thường giữ một "
           "vùng **staging** chứa bản ghi thô để truy vết nguồn gốc (data lineage) và để có thể chạy lại. Một yêu cầu "
           "quan trọng là ETL phải **idempotent**: chạy lại nhiều lần với cùng dữ liệu không làm phát sinh bản ghi trùng.")
    b.para("Khi tích hợp nhiều nguồn, cùng một thực thể (một ứng viên) có thể xuất hiện nhiều lần dưới các dạng khác "
           "nhau. Bài toán xác định các bản ghi cùng chỉ một thực thể được gọi là **định danh thực thể** (entity "
           "resolution) hay liên kết bản ghi (record linkage) [21]. Cách tiếp cận phổ biến là chuẩn hoá các trường định "
           "danh (email chữ thường, số điện thoại về một định dạng) rồi so khớp theo thứ tự ưu tiên các khoá có độ tin "
           "cậy cao; khi khớp thì gộp (merge) thông tin, bổ sung các trường còn thiếu.")

    b.heading(2, "2.3. Ngôn ngữ Python và các thư viện xử lý dữ liệu")
    b.para("Python do Guido van Rossum phát triển và công bố lần đầu năm 1991, là ngôn ngữ thông dịch, đa mô hình, có cú "
           "pháp rõ ràng và hệ sinh thái thư viện rất lớn, hiện là ngôn ngữ phổ biến hàng đầu trong khoa học dữ liệu và "
           "AI. Điểm mạnh của Python là năng suất phát triển cao và thư viện phong phú; điểm yếu là tốc độ thực thi chậm "
           "hơn ngôn ngữ biên dịch, tuy nhiên các thư viện tính toán chính đều được viết lõi bằng C nên đáp ứng tốt quy "
           "mô dữ liệu của đề tài. Các thư viện chính được sử dụng gồm:")
    b.bullets([
        "**pandas** (W. McKinney, 2008) [3]: cấu trúc DataFrame để đọc CSV/Excel, làm sạch và tổng hợp dữ liệu; dùng "
        "trong ETL và tính các chỉ số pipeline.",
        "**openpyxl, pypdf, python-docx**: đọc/ghi tệp Excel, trích văn bản từ CV PDF và DOCX; thư viện chuẩn "
        "**email** để phân tích tệp .eml và tệp đính kèm.",
        "**scikit-learn** [4]: cung cấp TfidfVectorizer và độ đo cosine để tính độ tương đồng nội dung CV – JD.",
        "**SQLAlchemy 2.0** [19]: ORM ánh xạ lớp Python sang bảng CSDL, cho phép viết truy vấn bằng Python và dùng chung "
        "mã cho PostgreSQL.",
        "**pytest**: framework kiểm thử tự động.",
    ])

    b.heading(2, "2.4. Hệ quản trị cơ sở dữ liệu PostgreSQL")
    b.para("PostgreSQL bắt nguồn từ dự án POSTGRES tại Đại học California, Berkeley (giữa thập niên 1980) và mang tên "
           "PostgreSQL từ năm 1996; hiện là hệ quản trị CSDL quan hệ mã nguồn mở mạnh mẽ, tuân thủ chuẩn SQL [16]. Đề tài "
           "khai thác các tính năng: ràng buộc khoá ngoại và UNIQUE để đảm bảo toàn vẹn và chống trùng; kiểu **JSONB** để "
           "lưu bản ghi thô ở staging và nội dung nhận xét AI có cấu trúc linh hoạt; **hàm cửa sổ** (window function) như "
           "LEAD để tính tỷ lệ chuyển đổi giữa các vòng liên tiếp; hàm **PERCENTILE_CONT** để tính trung vị, P90. Ưu điểm "
           "của PostgreSQL là ổn định, miễn phí, nhiều nhà cung cấp đám mây hỗ trợ (Render, Neon); nhược điểm là cần cấu "
           "hình và tối ưu khi dữ liệu rất lớn – điều chưa phát sinh ở quy mô đề tài.")

    b.heading(2, "2.5. Framework FastAPI và kiến trúc RESTful API")
    b.para("FastAPI là web framework Python hiện đại do Sebastián Ramírez phát hành năm 2018, xây dựng trên Starlette "
           "(ASGI) và Pydantic [15]. FastAPI dùng type hint của Python để tự động kiểm tra dữ liệu vào/ra và sinh tài liệu "
           "OpenAPI (Swagger) tương tác. Hệ thống tuân theo kiến trúc REST: mỗi tài nguyên (hồ sơ, nhận xét AI, báo cáo, "
           "lần chạy ETL) có URL riêng và được thao tác bằng các phương thức HTTP GET/POST/PATCH. Cơ chế **dependency "
           "injection** của FastAPI giúp gắn kiểm tra quyền vào từng endpoint một cách gọn gàng.")
    b.para("Xác thực sử dụng luồng OAuth2 password và **JSON Web Token** (JWT) [9]: sau khi đăng nhập thành công, máy "
           "chủ cấp một token có chữ ký HMAC-SHA256 chứa mã người dùng, vai trò và thời hạn; client gửi token trong header "
           "Authorization ở mỗi yêu cầu. Mật khẩu không bao giờ lưu dạng rõ mà được băm bằng PBKDF2-SHA256 với muối ngẫu "
           "nhiên và 260.000 vòng lặp.")

    b.heading(2, "2.6. Streamlit và Plotly cho dashboard")
    b.para("Streamlit (ra mắt năm 2019) là framework mã nguồn mở cho phép xây dựng ứng dụng web dữ liệu hoàn toàn bằng "
           "Python mà không cần viết HTML/JavaScript [17]. Ứng dụng Streamlit chạy lại kịch bản từ trên xuống mỗi khi "
           "người dùng tương tác, kết hợp session state để lưu phiên đăng nhập; tính năng điều hướng nhiều trang "
           "(st.navigation) cho phép hiển thị menu khác nhau theo vai trò. Plotly là thư viện biểu đồ tương tác [20], "
           "hỗ trợ sẵn biểu đồ phễu, cột, đường với tooltip khi rê chuột. Ưu điểm của bộ đôi này là phát triển nhanh, "
           "giao diện gọn đẹp; nhược điểm là khả năng tuỳ biến bố cục kém hơn framework frontend chuyên dụng.")
    b.para("Khi thiết kế dashboard, nhóm áp dụng các nguyên tắc trực quan hoá: một trục giá trị cho mỗi biểu đồ (không "
           "dùng hai trục y), màu theo vai trò dữ liệu (một màu cho một chuỗi, màu trạng thái riêng cho cảnh báo vượt SLA), "
           "bảng màu được kiểm tra an toàn cho người mù màu, nhãn giá trị trực tiếp có chọn lọc và luôn có bảng số liệu "
           "đi kèm biểu đồ.")

    b.heading(2, "2.7. Xử lý ngôn ngữ tự nhiên và mô hình ngôn ngữ lớn")
    b.heading(3, "2.7.1. Tiền xử lý văn bản tiếng Việt")
    b.para("Tiếng Việt dùng chữ Latinh có dấu; cùng một từ có thể được viết có dấu, không dấu, hoa, thường hoặc ở dạng "
           "Unicode tổ hợp khác nhau. Vì vậy bước chuẩn hoá gồm: đưa về chuẩn Unicode NFC, chuyển chữ thường, bỏ dấu "
           "(ví dụ “Phỏng vấn” → “phong van”, chú ý chữ “đ” → “d”), loại ký tự đặc biệt và gộp khoảng trắng. Văn bản đã "
           "chuẩn hoá được dùng làm khoá so khớp khi ánh xạ tên vị trí, nguồn, vòng phỏng vấn và khi trích xuất kỹ năng.")
    b.heading(3, "2.7.2. Trích xuất thông tin dựa trên từ điển và TF-IDF")
    b.para("Trích xuất kỹ năng bằng **từ điển kỹ năng** (skill taxonomy) là kỹ thuật NLP dựa trên luật: mỗi kỹ năng "
           "chuẩn có danh sách từ đồng nghĩa (ví dụ “Power BI”: power bi, powerbi, dax), được tìm theo ranh giới từ trong "
           "văn bản đã chuẩn hoá. Ưu điểm là minh bạch, giải thích được và nhất quán – rất quan trọng trong tuyển dụng; "
           "nhược điểm là phải bảo trì từ điển. **TF-IDF** [6] biểu diễn văn bản bằng véc-tơ trọng số, trong đó trọng số "
           "của một từ tăng theo tần suất trong văn bản và giảm theo mức phổ biến trong tập văn bản; độ tương đồng giữa "
           "CV và JD được đo bằng cosine giữa hai véc-tơ.")
    b.formula("tfidf(t, d) = tf(t, d) × log( N / df(t) ) ;   cos(a, b) = (a · b) / (‖a‖ × ‖b‖)")
    b.heading(3, "2.7.3. Mô hình ngôn ngữ lớn và Claude")
    b.para("Mô hình ngôn ngữ lớn (LLM) dựa trên kiến trúc Transformer [5] được huấn luyện trên lượng văn bản khổng lồ, có "
           "khả năng hiểu và sinh ngôn ngữ tự nhiên, phù hợp cho các tác vụ tóm tắt, trích xuất, phân loại và viết báo "
           "cáo. Claude là họ mô hình ngôn ngữ lớn do Anthropic phát triển, được truy cập qua Messages API và bộ SDK "
           "Python chính thức [18]. Tính năng **structured outputs** cho phép ràng buộc câu trả lời theo một JSON Schema, "
           "giúp chương trình đọc kết quả ổn định. Hạn chế của LLM là có thể “ảo giác” (sinh thông tin không có trong dữ "
           "liệu), có chi phí theo token và có thể phản ánh thiên kiến trong dữ liệu huấn luyện; do đó đề tài chỉ dùng "
           "LLM cho phần diễn giải, còn các chỉ số định lượng vẫn tính bằng mã nguồn.")

    b.heading(2, "2.8. Phân quyền, bảo vệ dữ liệu cá nhân và AI có trách nhiệm trong tuyển dụng")
    b.heading(3, "2.8.1. Phân quyền theo vai trò (RBAC)")
    b.para("Mô hình RBAC do Ferraiolo và Kuhn đề xuất năm 1992 [7] và được Sandhu và cộng sự chuẩn hoá [8]: quyền không "
           "gán trực tiếp cho người dùng mà gán cho **vai trò**; người dùng được gán vai trò. Nhờ đó việc quản lý quyền "
           "đơn giản, nhất quán và tuân thủ nguyên tắc đặc quyền tối thiểu. Kết hợp với RBAC, kỹ thuật **che giấu dữ "
           "liệu** (data masking) hiển thị một phần thông tin (ví dụ email n***@gmail.com) cho người không cần biết đầy đủ.")
    b.heading(3, "2.8.2. Bảo vệ dữ liệu cá nhân và chống phân biệt đối xử")
    b.para("Nghị định 13/2023/NĐ-CP của Chính phủ quy định về bảo vệ dữ liệu cá nhân, trong đó dữ liệu về sức khoẻ, đời "
           "sống tình dục, quan điểm chính trị, tôn giáo… thuộc nhóm dữ liệu nhạy cảm, việc xử lý phải có mục đích rõ "
           "ràng và hạn chế ở mức cần thiết [14]. Bộ luật Lao động 2019 nghiêm cấm phân biệt đối xử trong lao động dựa "
           "trên giới tính, dân tộc, tôn giáo, tình trạng hôn nhân, mang thai… [13]. CV ở Việt Nam lại thường chứa ngày "
           "sinh, giới tính, tình trạng hôn nhân, quê quán – những thông tin không liên quan đến năng lực nhưng dễ dẫn "
           "tới đánh giá thiên vị.")
    b.heading(3, "2.8.3. Công bằng trong tuyển dụng tự động và human-in-the-loop")
    b.para("Nghiên cứu về tuyển dụng bằng thuật toán chỉ ra rằng hệ thống có thể tái tạo thiên kiến lịch sử nếu học từ "
           "dữ liệu quá khứ [12]. Một công cụ giám sát phổ biến là **quy tắc 4/5** (four-fifths rule) trong Hướng dẫn "
           "thống nhất về thủ tục tuyển chọn nhân sự của Hoa Kỳ [10]: nếu tỷ lệ được chọn của một nhóm thấp hơn 80% tỷ "
           "lệ của nhóm cao nhất thì được xem là dấu hiệu tác động bất lợi cần xem xét.")
    b.formula("Tỷ lệ tác động (impact ratio) = min(tỷ lệ qua của các nhóm) / max(tỷ lệ qua của các nhóm);  cảnh báo khi < 0,8")
    b.para("Từ các cơ sở trên, đề tài áp dụng nguyên tắc **human-in-the-loop**: AI chỉ tóm tắt và gợi ý, không chấm "
           "điểm hay quyết định tuyển/loại; thông tin nhạy cảm bị loại khỏi dữ liệu gửi cho AI; mọi nhận xét của AI phải "
           "được người phụ trách kiểm duyệt trước khi người khác nhìn thấy; và mọi thao tác quan trọng đều được ghi nhật ký.")

    # ============================================================ CHƯƠNG 3
    b.heading(1, "CHƯƠNG 3. PHÂN TÍCH HỆ THỐNG VÀ XÂY DỰNG SẢN PHẨM", page_break=True)
    b.heading(2, "3.1. Phân tích hệ thống")
    b.heading(3, "3.1.1. Hiện trạng và dữ liệu đầu vào")
    b.para("Doanh nghiệp giả định có 6 phòng ban (Công nghệ, Dữ liệu & AI, Nhân sự, Kinh doanh, Marketing, Tài chính – Kế "
           "toán) và 10 vị trí đang tuyển. Khối Công nghệ và Dữ liệu dùng ATS cho phần lớn hồ sơ, các phòng ban khác chủ "
           "yếu theo dõi bằng Excel; ứng viên từ website, Facebook, ngày hội việc làm và giới thiệu nội bộ điền Google "
           "Form; một số ứng viên gửi email trực tiếp. Bảng 3.1 mô tả bốn nguồn dữ liệu và các vấn đề chất lượng dữ liệu "
           "điển hình mà ETL phải xử lý.")
    b.table("nguon", "3|Mô tả các nguồn dữ liệu tuyển dụng đầu vào",
            ["Nguồn", "Định dạng", "Nội dung", "Vấn đề chất lượng điển hình"],
            [["Google Form", ".csv (UTF-8)", "Thông tin cá nhân, vị trí, kênh biết tin, kinh nghiệm, kỹ năng, lương mong "
              "muốn, tệp CV", "Tên viết thường, email có khoảng trắng/viết hoa, SĐT +84, kinh nghiệm dạng chữ “1-2 năm”, "
              "lương “15tr”, “Thỏa thuận”"],
             ["ATS", ".json", "Danh mục vị trí + JD; hồ sơ; lịch sử từng vòng (vào/ra, kết quả, người PV, điểm, nhận xét)",
              "Tên tách họ/tên, mốc thời gian có múi giờ, điểm dạng “4/5”, trạng thái chưa cập nhật"],
             ["Excel HR", ".xlsx", "Bảng theo dõi: ngày từng vòng, kết quả, trạng thái, lý do loại/rút, ghi chú",
              "Tiêu đề không ở dòng 1, SĐT mất số 0, tên không dấu, ngày lẫn kiểu chuỗi, dòng nhập trùng, sheet hướng dẫn"],
             ["Email", ".eml + CV đính kèm", "Email ứng tuyển (kèm CV PDF/DOCX/TXT) và email xin rút hồ sơ",
              "Thông tin nằm trong văn bản tự do; email rút hồ sơ là thông tin cập nhật cho hồ sơ đã có ở nguồn khác"]],
            [2.2, 2.2, 5.6, 6.0])

    b.heading(3, "3.1.2. Yêu cầu chức năng")
    b.table("ycchucnang", "3|Yêu cầu chức năng của hệ thống",
            ["Mã", "Chức năng", "Mô tả", "Task"],
            [["F1", "Nhập dữ liệu đa nguồn (ETL)", "Tải lên CSV/JSON/XLSX/EML/CV; trích xuất, chuẩn hoá, khử trùng, nạp "
              "vào kho; xem log, bản ghi bị loại; chạy lại không trùng", "1, 2"],
             ["F2", "Quản lý hồ sơ ứng tuyển", "Danh sách, tìm kiếm, lọc theo vị trí/vòng/trạng thái/quá SLA; chi tiết "
              "hồ sơ, hành trình qua các vòng, CV", "2"],
             ["F3", "Ghi nhận kết quả vòng", "Đạt → chuyển vòng; không đạt/rút/vắng → đóng hồ sơ kèm lý do; kiểm tra "
              "thiên vị nhận xét", "3, 5"],
             ["F4", "Dashboard pipeline", "KPI, phễu, tỷ lệ qua vòng, thời gian chuyển vòng so với SLA, điểm nghẽn, xu "
              "hướng tuần, hiệu quả nguồn, lý do rớt, pipeline theo vị trí", "3"],
             ["F5", "AI xử lý CV", "Trích văn bản CV, ẩn danh, tóm tắt, phân nhóm kỹ năng, độ phủ kỹ năng JD", "4"],
             ["F6", "AI gợi ý câu hỏi phỏng vấn", "Bộ câu hỏi có cấu trúc theo JD và các điểm cần làm rõ trong CV", "4"],
             ["F7", "AI phân tích lý do rớt", "Phân nhóm lý do loại/rút, nhận định và đề xuất cải tiến", "4"],
             ["F8", "Kiểm duyệt nhận xét AI", "Duyệt / chỉnh sửa / từ chối; bắt buộc ghi chú với nội dung bị gắn cờ", "5"],
             ["F9", "Báo cáo tuần", "Tổng hợp số liệu tuần, nhận định AI, HR duyệt, tải Markdown/HTML", "5"],
             ["F10", "Giám sát công bằng", "Tỷ lệ qua vòng theo giới tính, quy tắc 4/5, danh sách nhận xét bị gắn cờ", "5"],
             ["F11", "Đăng nhập & phân quyền", "JWT, 3 vai trò, menu và dữ liệu theo vai trò, che PII", "5"],
             ["F12", "Quản trị", "Quản lý người dùng (tạo, đổi vai trò/phòng ban, khoá, đặt lại mật khẩu), nhật ký", "5"]],
            [1.2, 3.6, 9.2, 1.4])

    b.heading(3, "3.1.3. Yêu cầu phi chức năng")
    b.table("ycphichucnang", "3|Yêu cầu phi chức năng",
            ["Nhóm", "Yêu cầu"],
            [["Bảo mật", "Mật khẩu băm PBKDF2; JWT có hạn; kiểm tra quyền ở phía máy chủ cho mọi API; che PII theo vai trò; "
              "ghi nhật ký xem thông tin cá nhân"],
             ["Quyền riêng tư & công bằng", "Ẩn danh CV trước khi gửi AI; không gửi giới tính, tuổi, hôn nhân, quê quán; "
              "AI không chấm điểm người; nội dung AI phải được duyệt"],
             ["Tin cậy", "ETL idempotent; giao dịch CSDL nhất quán; khi Claude lỗi tự chuyển sang engine NLP nội bộ"],
             ["Hiệu năng", "ETL 500 bản ghi + 185 CV trong vài giây; dashboard phản hồi < 2 giây với vài trăm hồ sơ"],
             ["Khả dụng", "Giao diện tiếng Việt, bố cục rõ ràng, có bảng số liệu đi kèm biểu đồ"],
             ["Triển khai", "Đóng gói Docker; cấu hình bằng biến môi trường; triển khai online có URL công khai"],
             ["Bảo trì", "Mã nguồn chia lớp (ETL, AI, dịch vụ, API, giao diện); 45 kiểm thử tự động"]],
            [3.5, 12.5])

    b.heading(3, "3.1.4. Tác nhân và sơ đồ use case")
    b.para("Hệ thống có ba tác nhân. **HR** (chuyên viên tuyển dụng) quản lý toàn bộ dữ liệu, chạy ETL và AI, kiểm duyệt "
           "nhận xét AI và báo cáo. **Hiring manager** (quản lý tuyển dụng của phòng ban) chỉ xem dữ liệu của phòng ban "
           "mình ở dạng đã che thông tin cá nhân, ghi nhận kết quả phỏng vấn, xem nhận xét AI và báo cáo đã được duyệt. "
           "**Admin** (quản trị viên) có toàn bộ quyền của HR và thêm quyền quản lý người dùng, xem nhật ký hệ thống. "
           "Hình 3.1 thể hiện sơ đồ use case và Bảng 3.4 là ma trận phân quyền chi tiết.")
    b.figure("usecase", IMG / "use_case.png", "3|Sơ đồ use case theo tác nhân")
    b.table("rbac", "3|Ma trận phân quyền theo vai trò",
            ["Chức năng / dữ liệu", "Admin", "HR", "Hiring manager"],
            [["Phạm vi dữ liệu", "Toàn công ty", "Toàn công ty", "Chỉ phòng ban của mình"],
             ["Họ tên, email, SĐT, giới tính, ngày sinh, nơi ở", "Xem đầy đủ", "Xem đầy đủ", "Bị che (mã UV + viết tắt)"],
             ["Tìm kiếm theo thông tin cá nhân", "Có", "Có", "Không (chỉ theo mã)"],
             ["Chạy ETL, xem log", "Có", "Có", "Không"],
             ["Chạy AI phân tích", "Có", "Có", "Không"],
             ["Xem nhận xét AI", "Tất cả", "Tất cả", "Chỉ bản đã duyệt"],
             ["Kiểm duyệt nhận xét AI", "Có", "Có", "Không"],
             ["Ghi nhận kết quả phỏng vấn", "Có", "Có", "Có (phòng ban mình)"],
             ["Báo cáo tuần", "Tạo, duyệt", "Tạo, duyệt", "Xem bản đã duyệt"],
             ["Giám sát công bằng", "Có", "Có", "Không"],
             ["Quản lý người dùng, nhật ký hệ thống", "Có", "Không", "Không"]],
            [6.4, 2.8, 2.8, 4.0])

    b.heading(3, "3.1.5. Kiến trúc tổng thể")
    b.para("Hệ thống được thiết kế theo kiến trúc nhiều lớp (Hình 3.2). Lớp **nguồn dữ liệu** gồm bốn loại tệp rời rạc. "
           "Lớp **ETL** viết bằng Python thực hiện trích xuất, lưu staging, biến đổi, định danh và nạp dữ liệu. Lớp **kho "
           "dữ liệu** PostgreSQL gồm vùng staging, các bảng chiều, bảng sự kiện và bảng vận hành. Lớp **backend FastAPI** "
           "cung cấp REST API cho xác thực – phân quyền, phân tích, dịch vụ AI, báo cáo và ETL. Lớp **giao diện Streamlit** "
           "hiển thị dashboard và các màn hình nghiệp vụ. Dịch vụ AI gọi Claude API khi được cấu hình khoá, ngược lại dùng "
           "engine NLP nội bộ. Bảng 3.5 tóm tắt công nghệ ở từng lớp.")
    b.figure("kientruc", IMG / "kien_truc.png", "3|Kiến trúc tổng thể hệ thống TalentLens")
    b.table("congnghe", "3|Công nghệ sử dụng theo từng lớp",
            ["Lớp", "Công nghệ", "Vai trò"],
            [["ETL", "Python 3.13, pandas, openpyxl, email, pypdf, python-docx", "Đọc và làm sạch dữ liệu đa nguồn"],
             ["Kho dữ liệu", "PostgreSQL 16, SQLAlchemy 2, psycopg 3", "Lưu trữ lược đồ hình sao, truy vấn phân tích"],
             ["Backend", "FastAPI, Pydantic, PyJWT, Uvicorn", "REST API, xác thực, phân quyền"],
             ["Phân tích", "pandas, NumPy", "Tính phễu, chuyển đổi, thời gian, điểm nghẽn, công bằng"],
             ["AI / NLP", "Anthropic SDK (Claude), scikit-learn TF-IDF, từ điển kỹ năng", "Tóm tắt CV, kỹ năng, câu hỏi, "
              "lý do rớt, báo cáo"],
             ["Giao diện", "Streamlit, Plotly, httpx", "Dashboard và màn hình nghiệp vụ"],
             ["Kiểm thử & triển khai", "pytest, Docker, Docker Compose, Render", "Đảm bảo chất lượng, đưa lên môi trường "
              "online"]],
            [3.0, 7.0, 6.0])

    b.heading(3, "3.1.6. Thiết kế quy trình ETL")
    b.para("Quy trình ETL gồm 7 bước (Hình 3.3). Ở bước **Extract**, mỗi loại tệp có một bộ đọc riêng: CSV đọc bằng "
           "pandas; JSON của ATS tách thành bản ghi vị trí và bản ghi hồ sơ; Excel được dò tự động dòng tiêu đề (tìm dòng "
           "chứa “Họ tên”) và bỏ qua sheet không có dữ liệu; email được phân tích bằng thư viện email, văn bản CV đính "
           "kèm được trích ngay. Ở bước **Staging**, mỗi bản ghi thô được lưu vào bảng stg_raw_record cùng **vân tay "
           "SHA-256** của nội dung; nếu vân tay đã từng được nạp thành công thì bản ghi được bỏ qua – nhờ vậy ETL có tính "
           "idempotent.")
    b.figure("etl", IMG / "quy_trinh_etl.png", "3|Quy trình ETL đa nguồn và khử trùng ứng viên")
    b.para("Bước **Transform** đưa mọi bản ghi về một cấu trúc chuẩn (CanonicalApplication) theo các quy tắc trong Bảng "
           "3.6. Việc ánh xạ giá trị phân loại (vị trí, nguồn, vòng, trạng thái, thành phố, học vấn) dùng chung một thuật "
           "toán ba tầng: khớp chính xác sau khi chuẩn hoá → khớp cụm từ dài nhất xuất hiện trong chuỗi → khớp gần đúng "
           "bằng difflib với ngưỡng 0,78–0,85. Bước **Validate** loại các bản ghi thiếu họ tên, thiếu cả email lẫn số điện "
           "thoại, không xác định được vị trí hoặc thiếu ngày nộp; lý do được lưu lại và hiển thị trên giao diện.")
    b.table("chuanhoa", "3|Quy tắc chuẩn hoá dữ liệu ứng viên",
            ["Trường", "Ví dụ dữ liệu nguồn", "Giá trị chuẩn"],
            [["Họ tên", "“nguyễn   văn AN”, “NGUYEN VAN AN”", "Nguyễn Văn An (ưu tiên bản có dấu khi gộp)"],
             ["Email", "“ AN.NGUYEN@GMAIL.COM ”, “An <an@x.vn>”", "an.nguyen@gmail.com"],
             ["Số điện thoại", "+84 912 345 678; 912345678; 0912.345.678", "0912345678 (10 số, đầu 03/05/07/08/09)"],
             ["Ngày giờ", "15/09/2026 10:22:13; 2026-09-15T09:00+07:00; số serial Excel", "datetime giờ Việt Nam"],
             ["Kinh nghiệm", "“1-2 năm”, “Dưới 1 năm”, “Fresher”, “2,5”", "1,5 / 0,5 / 0 / 2,5 (năm)"],
             ["Lương mong muốn", "“15tr”, “15.000.000”, “15-18 triệu”, “Thỏa thuận”", "15 / 15 / 16,5 / trống (triệu)"],
             ["Vị trí", "“DA”, “Data analyst (Junior)”, “QC/Tester”", "DA-2026, DA-2026, QA-2026"],
             ["Nguồn", "“topcv.vn”, “Group Facebook tuyển dụng IT”, “Bạn bè giới thiệu”", "TOPCV, FACEBOOK, REFERRAL"],
             ["Vòng", "“CV Screening”, “PV kỹ thuật”, “Phỏng vấn vòng 1”", "SCREENING, TECH_INTERVIEW, HR_INTERVIEW"],
             ["Trạng thái / kết quả", "“Không đạt”, “Rút hồ sơ”, “Từ chối” (offer)", "rejected, withdrawn, withdrawn"],
             ["Điểm phỏng vấn", "“4/5”, “8/10”, “80%”", "4,0 (thang 1–5)"]],
            [2.6, 7.0, 6.4])
    b.para("Bước **Định danh** là trọng tâm của Task 2. Một chỉ mục định danh được dựng từ các ứng viên đã có trong kho; "
           "mỗi bản ghi mới được so khớp lần lượt theo **email → số điện thoại → (họ tên không dấu + ngày sinh)**. Nếu "
           "khớp, hệ thống gộp vào ứng viên cũ: bổ sung các trường còn thiếu, giữ CV dài hơn, ưu tiên họ tên có dấu và "
           "ghi lại danh tính đã gộp (merged_identities) để truy vết. Ở mức hồ sơ, cặp (ứng viên, vị trí) là duy nhất; "
           "nếu cùng một hồ sơ xuất hiện ở nhiều nguồn, hệ thống giữ ngày nộp sớm nhất, ghi nhận nguồn chạm đầu tiên "
           "(first-touch), hợp nhất các sự kiện theo từng vòng và chọn trạng thái kết thúc mới nhất. Email xin rút hồ sơ "
           "được xử lý sau cùng như một bản cập nhật cho hồ sơ đã có.")
    b.para("Bước **Load** và **Hậu xử lý** ghi dữ liệu vào các bảng dim/fact, sau đó tính lại vòng hiện tại, thời điểm "
           "rời vòng, thời lượng từng vòng, trích xuất kỹ năng từ CV, phân loại lý do loại/rút và quét cờ thiên vị cho "
           "nhận xét phỏng vấn. Mỗi lần chạy được ghi vào bảng etl_run với thống kê và log chi tiết; đoạn log dưới đây "
           "trích từ lần chạy đầu tiên trên bộ dữ liệu mẫu:")
    b.code("""[20:22:43] START     ETL run #1 – 26 tệp dữ liệu, 185 tệp CV/khác
[20:22:43] EXTRACT   ats_export.json: 10 vị trí, 191 hồ sơ ATS
[20:22:43] EXTRACT   google_form_responses.csv: 117 câu trả lời Google Form, 15 cột
[20:22:43] EXTRACT   hr_tracking.xlsx/Pipeline Q3-Q4 2026: 159 dòng (tiêu đề ở dòng 4)
[20:22:43] EXTRACT   Hộp thư tuyển dụng: 23 email (.eml)
[20:22:46] WARN      Loại hr_tracking.xlsx bản ghi 162: không xác định được vị trí
                     'Bảo vệ tòa nhà'
[20:22:47] INFO      003_rut_ho_so_tram.eml: cập nhật hồ sơ HS-00200 → rút hồ sơ
[20:22:48] TRANSFORM Hợp lệ 485 | bị loại 5 | bỏ qua do đã nạp trước đó 0
[20:22:48] LOAD      dim_candidate: +314 ứng viên mới, gộp 160 bản ghi trùng
                     (email=158, SĐT=2)
[20:22:48] LOAD      fact_application: +329 hồ sơ mới, 145 hồ sơ trùng được gộp
[20:22:48] LOAD      fact_stage_event: +1027 sự kiện, 208 sự kiện gộp
[20:22:48] NLP       Trích xuất kỹ năng cho 242 ứng viên; phân loại 269 lý do
[20:22:48] DONE      Hoàn tất sau 5.9s – trạng thái: PARTIAL""")

    b.heading(3, "3.1.7. Thiết kế kho dữ liệu")
    b.para("Kho dữ liệu được thiết kế theo lược đồ hình sao (Hình 3.4) với hai bảng sự kiện: **fact_application** (mỗi "
           "dòng là một hồ sơ ứng tuyển của một ứng viên vào một vị trí) và **fact_stage_event** (mỗi dòng là một lần hồ "
           "sơ đi qua một vòng, có thời điểm vào/ra, kết quả, người phỏng vấn, điểm, nhận xét). Các bảng chiều mô tả ứng "
           "viên, vị trí, phòng ban, nguồn, vòng (có thứ tự và SLA) và ngày. Bảng 3.7 mô tả vai trò của từng bảng; DDL "
           "đầy đủ được sinh tự động từ mô hình SQLAlchemy vào tệp sql/schema.sql.")
    b.figure("erd", IMG / "erd.png", "3|Sơ đồ ERD kho dữ liệu tuyển dụng (lược đồ hình sao)")
    b.table("bang", "3|Mô tả các bảng trong kho dữ liệu",
            ["Bảng", "Loại", "Nội dung chính", "Ràng buộc nổi bật"],
            [["dim_candidate", "Chiều", "Ứng viên đã khử trùng: định danh, thuộc tính nhạy cảm (tách riêng), kinh "
              "nghiệm, học vấn, kỹ năng, CV, danh tính đã gộp", "UNIQUE candidate_code"],
             ["dim_position", "Chiều", "Vị trí: mã, chức danh, phòng ban, JD, kỹ năng bắt buộc/ưu tiên, chỉ tiêu, các "
              "biến thể tên", "UNIQUE code; FK phòng ban, quản lý"],
             ["dim_department", "Chiều", "Phòng ban – dùng để giới hạn phạm vi của hiring manager", "UNIQUE code"],
             ["dim_source", "Chiều", "Nguồn tuyển và kênh (job board, social, referral…)", "UNIQUE code"],
             ["dim_stage", "Chiều", "7 vòng: thứ tự, SLA (ngày), vòng kết thúc", "UNIQUE code"],
             ["dim_date", "Chiều", "Lịch: ngày, tuần ISO, đầu tuần, tháng, quý, năm", "PK date_key YYYYMMDD"],
             ["fact_application", "Sự kiện", "Hồ sơ: ngày nộp, vòng hiện tại, trạng thái, ngày đóng, lý do và nhóm lý "
              "do, lương mong muốn, nguồn dữ liệu gốc", "UNIQUE (candidate_id, position_id)"],
             ["fact_stage_event", "Sự kiện", "Lịch sử vòng: vào/ra, kết quả, thời lượng, người PV, điểm, nhận xét, cờ "
              "thiên vị", "UNIQUE (application_id, stage_id)"],
             ["stg_raw_record, etl_run", "Staging", "Bản ghi thô (JSONB) + vân tay; log và thống kê mỗi lần ETL",
              "Index fingerprint"],
             ["ai_insight", "Vận hành", "Kết quả AI (JSONB), nhà cung cấp, mô hình, phiên bản prompt, trạng thái duyệt, "
              "cờ thiên vị, trường đã ẩn, người tạo/duyệt", "FK ứng viên, hồ sơ, vị trí"],
             ["weekly_report", "Vận hành", "Số liệu tuần, nội dung báo cáo, trạng thái nháp/duyệt", ""],
             ["app_user, audit_log", "Vận hành", "Tài khoản, vai trò, phòng ban; nhật ký thao tác", "UNIQUE username"]],
            [3.4, 1.6, 7.4, 3.6])
    b.para("Thiết kế này giúp các câu hỏi phân tích được trả lời bằng truy vấn SQL ngắn gọn. Ví dụ, truy vấn dưới đây dùng "
           "hàm cửa sổ LEAD để tính tỷ lệ chuyển đổi giữa hai vòng liên tiếp; kết quả trên dữ liệu mẫu được trình bày ở "
           "Bảng 3.8. Tệp sql/sample_queries.sql gồm 10 truy vấn mẫu (phễu, chuyển đổi, thời gian và SLA, hiệu quả nguồn, "
           "xu hướng tuần, lý do rớt theo vòng, kiểm tra khử trùng, lineage, hồ sơ quá hạn, pipeline theo phòng ban).")
    b.code("""WITH reached AS (
    SELECT s.stage_order, s.name, COUNT(DISTINCT e.application_id) AS n
    FROM fact_stage_event e JOIN dim_stage s ON s.id = e.stage_id
    GROUP BY s.stage_order, s.name)
SELECT name AS tu_vong, LEAD(name) OVER (ORDER BY stage_order) AS den_vong, n,
       LEAD(n) OVER (ORDER BY stage_order) AS n_tiep,
       ROUND(100.0 * LEAD(n) OVER (ORDER BY stage_order) / n, 1) AS ty_le_chuyen_doi
FROM reached ORDER BY stage_order;""")
    b.table("truyvan", "3|Kết quả truy vấn tỷ lệ chuyển đổi trên dữ liệu mẫu",
            ["Từ vòng", "Đến vòng", "Số hồ sơ", "Số đi tiếp", "Tỷ lệ chuyển đổi"],
            [["Nộp hồ sơ", "Sàng lọc CV", "329", "321", "97,6%"],
             ["Sàng lọc CV", "Phỏng vấn HR", "321", "176", "54,8%"],
             ["Phỏng vấn HR", "Phỏng vấn chuyên môn", "176", "96", "54,5%"],
             ["Phỏng vấn chuyên môn", "Phỏng vấn cuối", "96", "44", "45,8%"],
             ["Phỏng vấn cuối", "Offer", "44", "37", "84,1%"],
             ["Offer", "Nhận việc", "37", "24", "64,9%"]],
            [3.6, 3.6, 2.4, 2.4, 3.0])

    b.heading(3, "3.1.8. Thiết kế phân tích pipeline và phát hiện điểm nghẽn")
    b.para("Mô-đun phân tích (app/services/analytics.py) nạp các hồ sơ và sự kiện trong phạm vi quyền của người dùng "
           "vào DataFrame, áp dụng bộ lọc thời gian/phòng ban/vị trí/nguồn, rồi tính các chỉ số trong Bảng 2.1. Thời gian "
           "chuyển vòng chỉ tính trên các sự kiện có kết quả “đạt” (hồ sơ thực sự đi tiếp) để phản ánh đúng năng lực xử "
           "lý. Điểm nghẽn được phát hiện tự động theo bốn quy tắc:")
    b.bullets([
        "**Chuyển đổi:** vòng có tỷ lệ qua thấp nhất trong các vòng có ít nhất 10 hồ sơ (mức cao nếu < 50%).",
        "**Thời gian:** vòng có tỷ số trung vị thời gian / SLA lớn nhất (mức cao nếu trung vị vượt SLA).",
        "**Tồn đọng:** số hồ sơ đang xử lý đã nằm ở vòng hiện tại lâu hơn SLA, nhóm theo vòng.",
        "**Rút hồ sơ:** số ứng viên tự rút và vòng tập trung nhiều nhất.",
    ])

    b.heading(3, "3.1.9. Thiết kế mô-đun NLP/AI")
    b.para("Mô-đun AI (thư mục app/ai) được thiết kế với hai engine có cùng giao diện: **ClaudeEngine** gọi Claude qua "
           "Anthropic SDK và **LocalEngine** dùng các kỹ thuật NLP nội bộ. Lớp dịch vụ chọn Claude nếu có khoá API; nếu "
           "lời gọi lỗi, hệ thống tự chuyển sang LocalEngine và ghi chú lại để không gián đoạn công việc. Hình 3.5 mô tả "
           "luồng xử lý có kiểm duyệt.")
    b.figure("aiflow", IMG / "quy_trinh_ai.png", "3|Quy trình AI có kiểm duyệt và chống thiên vị")
    b.bullets([
        "**Trích văn bản CV:** pypdf cho PDF, python-docx cho DOCX (gồm cả bảng), giải mã nhiều bảng mã cho TXT; chuẩn "
        "hoá Unicode và khoảng trắng; tách các mục Mục tiêu, Kinh nghiệm, Học vấn, Kỹ năng, Dự án, Chứng chỉ.",
        "**Ẩn danh:** loại bỏ các dòng có nhãn nhạy cảm (họ tên, ngày sinh, giới tính, hôn nhân, địa chỉ, quê quán, tôn "
        "giáo, dân tộc, sức khoẻ, ảnh, liên hệ) và thay thế email, số điện thoại, đường link, ngày tháng, tuổi, tên ứng "
        "viên bằng nhãn giữ chỗ; danh sách trường đã ẩn được lưu kèm kết quả.",
        "**Tóm tắt & phân nhóm kỹ năng:** từ điển gồm 14 nhóm và khoảng 100 kỹ năng chuẩn; độ phủ kỹ năng bắt buộc của JD "
        "= số kỹ năng bắt buộc có trong CV / tổng số kỹ năng bắt buộc; độ tương đồng TF-IDF chỉ mang tính tham khảo. Với "
        "Claude, phần tiêu đề, tóm tắt, điểm nổi bật, điểm cần làm rõ do mô hình viết theo JSON Schema, còn độ phủ JD vẫn "
        "tính bằng từ điển để đảm bảo nhất quán.",
        "**Câu hỏi phỏng vấn theo JD:** câu chuyên môn cho kỹ năng đã có, câu làm rõ cho kỹ năng JD yêu cầu nhưng CV chưa "
        "thể hiện, câu làm rõ thành tích trong CV, câu tình huống theo phòng ban và câu hành vi theo phương pháp STAR, "
        "kèm mục đích, tín hiệu trả lời tốt và danh sách chủ đề cấm hỏi.",
        "**Lý do rớt phổ biến:** lý do dạng văn bản tự do được phân vào 12 nhóm bằng luật từ khoá tiếng Việt/Anh (Bảng "
        "3.9), sau đó tổng hợp theo vòng và sinh nhận định, đề xuất cải tiến.",
        "**Báo cáo tuần:** số liệu tuần này so với tuần trước, điểm nghẽn, lý do rớt nổi bật; phần nhận định do AI viết.",
    ])
    b.table("lydo", "3|Các nhóm lý do loại / rút hồ sơ và từ khoá nhận diện",
            ["Nhóm", "Từ khoá tiêu biểu (sau khi bỏ dấu)", "Đề xuất cải tiến"],
            [["Nhận offer nơi khác", "offer khac, cong ty khac, nhan viec noi khac", "Rút ngắn thời gian giữa các vòng"],
             ["Kỳ vọng lương/phúc lợi", "muc luong, ky vong luong, salary, dai ngo", "Công bố dải lương trong JD"],
             ["Quy trình kéo dài", "cho lau, keo dai, khong co phan hoi", "Đặt SLA, cảnh báo hồ sơ quá hạn"],
             ["Không phản hồi / vắng mặt", "khong phan hoi, khong den, no show", "Nhắc lịch tự động trước 24h"],
             ["Vị trí đã đóng", "da du nguoi, dong tuyen, headcount", "Đồng bộ trạng thái tin tuyển dụng"],
             ["Ngoại ngữ", "tieng anh, ielts, toeic", "Ghi rõ yêu cầu, câu hỏi sàng lọc"],
             ["Giao tiếp / trình bày", "giao tiep, trinh bay, thuyet trinh", "Chuẩn hoá tiêu chí trong scorecard"],
             ["Thiếu kỹ năng chuyên môn", "ky nang, chuyen mon, bai test, kien thuc", "Câu hỏi/bài test sàng lọc sớm"],
             ["Kinh nghiệm chưa phù hợp", "kinh nghiem, experience, junior, overqualified", "Làm rõ cấp độ trong JD"],
             ["Văn hoá / thái độ", "van hoa, thai do, dinh huong", "Mô tả hành vi cụ thể, kiểm duyệt nhận xét"],
             ["Địa điểm / thời gian", "dia diem, onsite, remote, xa nha", "Nêu rõ địa điểm, chế độ làm việc"],
             ["Lý do cá nhân", "ca nhan, gia dinh, du hoc", "Giữ liên hệ trong talent pool"]],
            [3.6, 6.4, 6.0])
    b.para("Khi dùng Claude, lời gọi API được thiết kế theo khuyến nghị hiện hành của Anthropic: mô hình mặc định "
           "claude-opus-5-5 (cấu hình được qua biến LLM_MODEL), tham số effort, đầu ra ràng buộc bằng JSON Schema và cơ "
           "chế fallback phía máy chủ khi bộ lọc an toàn từ chối. System prompt nêu rõ các nguyên tắc: chỉ dựa trên bằng "
           "chứng liên quan công việc, không suy đoán thuộc tính được bảo vệ, không xếp hạng hay quyết định thay con người.")
    b.code("""response = self.client.beta.messages.create(
    model=self.model_name, max_tokens=16000, system=SYSTEM_PROMPT,
    messages=[{"role": "user", "content": prompt}],   # prompt chứa CV đã ẩn danh
    output_config={"effort": self.effort,
                   "format": {"type": "json_schema", "schema": CV_SCHEMA}},
    betas=["server-side-fallback-2026-07-01"], fallbacks="default")
if response.stop_reason == "refusal":                 # → chuyển sang engine nội bộ
    raise AIRefusalError("Mô hình từ chối xử lý yêu cầu")
text = next(b.text for b in response.content if b.type == "text")
result = json.loads(text)""")

    b.heading(3, "3.1.10. Phân quyền, chống thiên vị và kiểm duyệt nhận xét AI")
    b.para("Phân quyền được thực hiện ở phía máy chủ bằng bảng quyền theo vai trò (app/rbac.py) và các dependency "
           "require(permission) gắn vào từng endpoint. Phạm vi dữ liệu của hiring manager được giới hạn ngay trong câu "
           "truy vấn theo phòng ban. Khi trả dữ liệu, bộ chuyển đổi (serializer) che thông tin cá nhân nếu người dùng "
           "không có quyền pii:read: họ tên thay bằng mã ứng viên kèm chữ viết tắt, email và số điện thoại bị che một "
           "phần, giới tính, ngày sinh, nơi ở bị ẩn, nội dung CV được ẩn danh.")
    b.para("**Bộ lọc thiên vị** (bias guard) quét nhận xét của AI và nhận xét phỏng vấn của con người theo 7 nhóm thuộc "
           "tính được bảo vệ (Bảng 3.10). Nhận xét phỏng vấn bị gắn cờ sẽ bị chặn lưu và người dùng được yêu cầu viết lại "
           "theo tiêu chí công việc (hoặc xác nhận lưu để HR kiểm tra); nhận xét AI bị gắn cờ chỉ được duyệt khi người duyệt "
           "chỉnh sửa hoặc ghi chú lý do. Mọi nhận xét AI được lưu ở trạng thái **Chờ duyệt**; chỉ HR/Admin được duyệt, sửa "
           "hoặc từ chối; hiring manager chỉ thấy bản đã duyệt. Trang giám sát công bằng tính tỷ lệ qua từng vòng theo giới "
           "tính và tỷ lệ tác động theo quy tắc 4/5, đồng thời liệt kê các nhận xét bị gắn cờ. Nhật ký audit ghi lại đăng "
           "nhập, xem thông tin cá nhân, chạy ETL, chạy AI, kiểm duyệt và quản lý tài khoản.")
    b.table("bias", "3|Các nhóm thuộc tính được bảo vệ trong bộ lọc thiên vị",
            ["Nhóm", "Ví dụ cụm từ bị gắn cờ"],
            [["Giới tính", "nữ giới, phụ nữ, đàn ông, con gái, giới tính"],
             ["Tuổi tác", "lớn tuổi, già, còn trẻ, quá trẻ, độ tuổi, “35 tuổi”"],
             ["Hôn nhân / thai sản", "kết hôn, lập gia đình, có con nhỏ, mang thai, thai sản, độc thân"],
             ["Vùng miền / quê quán", "quê quán, người miền…, giọng miền…, dân tỉnh"],
             ["Tôn giáo / dân tộc", "tôn giáo, theo đạo, dân tộc"],
             ["Ngoại hình", "ngoại hình, xinh, đẹp trai, cao ráo, béo, gầy"],
             ["Sức khoẻ / khuyết tật", "khuyết tật, bệnh nền, sức khoẻ yếu"]],
            [4.5, 11.5])

    b.heading(3, "3.1.11. Thiết kế API")
    b.para("Backend cung cấp 34 endpoint REST, được FastAPI tự động mô tả theo chuẩn OpenAPI tại đường dẫn /docs. Bảng "
           "3.11 liệt kê các endpoint chính cùng quyền yêu cầu.")
    b.table("api", "3|Các endpoint chính của backend FastAPI",
            ["Phương thức & đường dẫn", "Chức năng", "Quyền"],
            [["POST /api/auth/login", "Đăng nhập, nhận JWT", "Công khai"],
             ["GET /api/applications", "Danh sách hồ sơ (lọc, tìm kiếm, phân trang, che PII)", "Đã đăng nhập"],
             ["GET /api/applications/{id}", "Chi tiết hồ sơ, hành trình, nhận xét AI được phép xem", "Đã đăng nhập"],
             ["POST /api/applications/{id}/decision", "Ghi nhận kết quả vòng, kiểm tra thiên vị", "feedback:write"],
             ["GET /api/analytics/dashboard", "KPI, phễu, thời gian, điểm nghẽn, nguồn, xu hướng", "Đã đăng nhập"],
             ["GET /api/analytics/fairness", "Tỷ lệ qua vòng theo giới tính, quy tắc 4/5", "fairness:read"],
             ["POST /api/ai/analyze-cv-file", "Tải CV lên và phân tích", "ai:run"],
             ["POST /api/ai/applications/{id}/analyze-cv", "Phân tích CV của hồ sơ", "ai:run"],
             ["POST /api/ai/applications/{id}/interview-questions", "Gợi ý câu hỏi phỏng vấn", "ai:run"],
             ["POST /api/ai/rejection-insights", "Phân tích lý do rớt phổ biến", "ai:run"],
             ["POST /api/ai/insights/{id}/review", "Duyệt / sửa / từ chối nhận xét AI", "ai:review"],
             ["POST /api/etl/run; GET /api/etl/runs/{id}", "Chạy ETL với tệp tải lên; xem log và bản ghi bị loại",
              "etl:run"],
             ["POST /api/reports/weekly; …/approve; …/download", "Tạo, duyệt, tải báo cáo tuần", "reports:*"],
             ["GET/POST/PATCH /api/users…; GET /api/audit-logs", "Quản lý người dùng, nhật ký", "users:manage"]],
            [6.4, 6.6, 3.0])

    # ---------------------------------------------------------------- 3.2 Giao diện
    b.heading(2, "3.2. Xây dựng giao diện sản phẩm")
    b.para("Giao diện được xây dựng bằng Streamlit, gồm 10 trang chia thành ba nhóm menu: Phân tích, AI & Chống thiên vị, "
           "Dữ liệu & Quản trị. Menu được tạo động theo quyền của người dùng nên mỗi vai trò chỉ nhìn thấy các chức năng "
           "được phép. Các mục dưới đây trình bày giao diện theo từng tác nhân.")
    b.heading(3, "3.2.1. Giao diện đăng nhập")
    b.para("Chức năng đăng nhập cho phép người dùng nhập tên đăng nhập và mật khẩu để nhận phiên làm việc (JWT). Trang "
           "đăng nhập giới thiệu ngắn gọn sản phẩm và có mục “Tài khoản demo” phục vụ chấm điểm. Khi máy chủ miễn phí "
           "đang “ngủ”, giao diện hiển thị thông báo chờ khởi động thay vì báo lỗi.")
    b.figure("login", SHOT / "f01_login.jpg", "3|Giao diện đăng nhập", width_cm=11)
    b.heading(3, "3.2.2. Giao diện tổng quan pipeline (dashboard) – vai trò HR")
    b.para("Dashboard giúp HR nắm toàn cảnh pipeline. Phía trên là hàng bộ lọc dùng chung (khoảng thời gian nộp hồ sơ, "
           "phòng ban, vị trí, nguồn), tiếp theo là các ô KPI: tổng hồ sơ, số ứng viên sau khử trùng, đang xử lý, đã nhận "
           "việc, tỷ lệ tuyển, thời gian tuyển trung bình và tỷ lệ nhận offer. Khối **Điểm nghẽn phát hiện tự động** liệt "
           "kê các cảnh báo được tính theo bốn quy tắc ở mục 3.1.8. Biểu đồ **phễu tuyển dụng** (demo của Task 3) cho thấy "
           "329 hồ sơ giảm còn 24 người nhận việc (7,3%), bảng bên cạnh cho tỷ lệ qua từng vòng – thấp nhất là vòng phỏng "
           "vấn chuyên môn (47,3%).")
    b.figure("dash1", SHOT / "f02_dash_top.jpg", "3|Dashboard pipeline – KPI, điểm nghẽn và phễu tuyển dụng")
    b.para("Biểu đồ **thời gian chuyển vòng** thể hiện trung vị số ngày của từng bước chuyển, vạch đen là SLA, cột màu "
           "cam là bước có trung vị vượt SLA. Trên dữ liệu mẫu, bước “PV HR → PV chuyên môn” mất trung vị 7,0 ngày so với "
           "SLA 4 ngày và 76% hồ sơ vượt SLA – đây là điểm nghẽn về năng lực xử lý (lịch phỏng vấn của quản lý chuyên "
           "môn). Biểu đồ **xu hướng theo tuần** so sánh số hồ sơ mới, lượt phỏng vấn và số nhận việc trên cùng một trục.")
    b.figure("dash2", SHOT / "f03_dash_duration.jpg", "3|Dashboard – thời gian chuyển vòng so với SLA và xu hướng theo tuần")
    b.para("Khối **hiệu quả nguồn tuyển dụng** đặt hai biểu đồ cạnh nhau (không dùng biểu đồ hai trục): số hồ sơ theo "
           "nguồn và tỷ lệ tuyển được theo nguồn. TopCV mang lại nhiều hồ sơ nhất (92) nhưng tỷ lệ tuyển chỉ 4,3%, trong "
           "khi LinkedIn (13,9%) và nhân viên giới thiệu (13,2%) có chất lượng cao hơn – thông tin hữu ích để phân bổ ngân "
           "sách đăng tuyển.")
    b.figure("dash3", SHOT / "f04_dash_source.jpg", "3|Dashboard – hiệu quả nguồn tuyển dụng")
    b.para("Cuối trang là phân bố **lý do loại / rút hồ sơ** đã được phân nhóm tự động và bảng **pipeline theo vị trí** "
           "(số hồ sơ, đang xử lý theo vòng, đã tuyển so với chỉ tiêu).")
    b.figure("dash4", SHOT / "f05_dash_reason.jpg", "3|Dashboard – lý do loại/rút hồ sơ và pipeline theo vị trí")

    b.heading(3, "3.2.3. Giao diện quản lý ứng viên và hồ sơ")
    b.para("Trang Ứng viên & hồ sơ cho phép tìm kiếm (theo tên, email, SĐT, mã – với HR), lọc theo vị trí, vòng hiện tại, "
           "trạng thái và hồ sơ quá SLA. Khi chọn một dòng, phần chi tiết hiển thị năm thẻ: Hồ sơ, Hành trình tuyển dụng, "
           "CV, Nhận xét AI và Ghi nhận kết quả vòng. Thẻ Hồ sơ trình bày thông tin liên hệ, thông tin nghề nghiệp, kỹ năng "
           "đã được trích xuất và phân nhóm, cùng danh sách bản ghi trùng đã gộp từ các nguồn khác.")
    b.figure("cand", SHOT / "f07_cand_profile.jpg", "3|Danh sách hồ sơ và thông tin ứng viên (vai trò HR)")
    b.para("Thẻ **Hành trình tuyển dụng** vẽ dòng thời gian các vòng mà hồ sơ đã đi qua (xanh = đạt, đỏ = không đạt, cam "
           "= rút hồ sơ) và bảng chi tiết thời điểm vào/ra vòng, số ngày, kết quả, người phỏng vấn, điểm, nhận xét. Nếu "
           "nhận xét phỏng vấn bị bộ lọc thiên vị gắn cờ, hệ thống hiển thị cảnh báo ngay dưới bảng.")
    b.figure("journey", SHOT / "f08_cand_journey.jpg", "3|Hành trình tuyển dụng của một hồ sơ")
    b.para("Thẻ **Nhận xét AI** cho phép HR chạy “Tóm tắt & phân tích CV” hoặc “Gợi ý câu hỏi phỏng vấn” cho hồ sơ đang "
           "xem; kết quả được lưu ở trạng thái Chờ duyệt cùng thông tin nhà cung cấp AI, mô hình, người tạo.")
    b.figure("candai", SHOT / "f09_cand_ai.jpg", "3|Nhận xét AI gắn với hồ sơ ứng viên")

    b.heading(3, "3.2.4. Giao diện AI phân tích CV")
    b.para("Đây là giao diện demo của Task 4 – “xử lý một CV mẫu”. HR chọn vị trí cần đối chiếu (hệ thống hiển thị kỹ "
           "năng bắt buộc, ưu tiên và JD), tải lên một CV PDF/DOCX/TXT hoặc chọn CV mẫu rồi bấm Phân tích. Kết quả gồm "
           "tiêu đề hồ sơ, đoạn tóm tắt, các điểm nổi bật có bằng chứng trong CV, các điểm cần làm rõ khi phỏng vấn và "
           "**độ phủ kỹ năng bắt buộc của JD** (kỹ năng đáp ứng / chưa thấy trong CV). Hệ thống nhấn mạnh đây là chỉ số "
           "tham khảo, không phải điểm xếp hạng ứng viên.")
    b.figure("aicv1", SHOT / "f10_ai_cv_a.jpg", "3|AI phân tích một CV mẫu – tóm tắt và đối chiếu JD")
    b.para("Phần tiếp theo trình bày **phân nhóm kỹ năng** bằng biểu đồ cột và nhãn theo nhóm, danh sách các loại thông "
           "tin đã được ẩn trước khi gửi cho AI (địa chỉ, họ tên, hôn nhân, email/SĐT, ngày sinh) và văn bản CV đã ẩn danh "
           "– chính là dữ liệu mà AI nhận được, giúp người dùng kiểm chứng tính minh bạch.")
    b.figure("aicv2", SHOT / "f11_ai_cv_b.jpg", "3|Phân nhóm kỹ năng và văn bản CV đã ẩn danh gửi cho AI")
    b.para("Thẻ **Câu hỏi phỏng vấn theo JD** sinh bộ câu hỏi có cấu trúc được nhóm theo loại, mỗi câu kèm mục đích, tín "
           "hiệu trả lời tốt và yêu cầu liên quan, cuối cùng là hướng dẫn chấm điểm và danh sách chủ đề không được hỏi "
           "(tuổi, hôn nhân, quê quán, tôn giáo, ngoại hình…). Thẻ **Lý do rớt phổ biến** phân tích 269 hồ sơ bị loại/rút: "
           "hai nhóm lớn nhất là “Kinh nghiệm chưa phù hợp” (33,8%) và “Thiếu kỹ năng chuyên môn” (29,0%), kèm đề xuất "
           "hành động cụ thể.")
    b.figure("aiq", SHOT / "f12_ai_questions.jpg", "3|Gợi ý câu hỏi phỏng vấn có cấu trúc theo JD", width_cm=14.5)
    b.figure("airej", SHOT / "f13_ai_rejection.jpg", "3|Phân tích lý do rớt phổ biến và đề xuất cải tiến")

    b.heading(3, "3.2.5. Giao diện kiểm duyệt nhận xét AI")
    b.para("Trang kiểm duyệt hiện thực nguyên tắc “luôn cho phép người phụ trách kiểm duyệt nhận xét AI”. HR lọc theo "
           "trạng thái (Chờ duyệt, Đã duyệt, Đã từ chối) và loại nhận xét; mỗi nhận xét hiển thị đầy đủ nội dung, cờ thiên "
           "vị (nếu có), cho phép bật chế độ chỉnh sửa (tóm tắt, điểm nổi bật, bảng câu hỏi…), nhập ghi chú rồi Duyệt hoặc "
           "Từ chối. Nhận xét đã xử lý có thể được mở lại.")
    b.figure("review", SHOT / "f14_review.jpg", "3|Giao diện kiểm duyệt nhận xét AI")

    b.heading(3, "3.2.6. Giao diện giám sát công bằng và cảnh báo thiên vị")
    b.para("Trang giám sát công bằng hiển thị tỷ lệ qua từng vòng của hai nhóm giới tính, bảng tỷ lệ tác động và danh "
           "sách nhận xét phỏng vấn bị gắn cờ. Trên dữ liệu mẫu, vòng phỏng vấn chuyên môn có tỷ lệ tác động 0,70 (nam "
           "42,3% với 26 hồ sơ, nữ 60,6% với 33 hồ sơ) nên được đánh dấu “cần xem xét”; hệ thống lưu ý đây là tín hiệu "
           "để rà soát tiêu chí và người phỏng vấn, chưa phải kết luận có phân biệt đối xử. Bộ lọc đã phát hiện 3 nhận "
           "xét phỏng vấn mang tính thiên vị trong dữ liệu nhập về (liên quan hôn nhân/thai sản, tuổi tác, ngoại hình).")
    b.figure("fair", SHOT / "f15_fairness.jpg", "3|Giám sát công bằng theo quy tắc 4/5 và nhận xét bị gắn cờ")
    b.para("Khi người dùng (ví dụ hiring manager) nhập một nhận xét dựa trên thuộc tính được bảo vệ, hệ thống chặn việc "
           "lưu, hiển thị cảnh báo và chỉ rõ cụm từ vi phạm thuộc nhóm nào.")
    b.figure("biaswarn", SHOT / "f20_bias_warning.jpg", "3|Cảnh báo khi nhận xét phỏng vấn có nội dung thiên vị")

    b.heading(3, "3.2.7. Giao diện báo cáo pipeline tuần")
    b.para("HR chọn tuần (mặc định tuần trước) và bấm Tạo báo cáo tuần. Báo cáo gồm tóm tắt, bảng chỉ số tuần này so với "
           "tuần trước, điểm nổi bật, rủi ro và điểm nghẽn, hành động đề xuất và số hồ sơ mới theo nguồn. Báo cáo ở trạng "
           "thái Bản nháp cho tới khi HR bấm “Duyệt & phát hành cho quản lý”; có thể tải về dạng Markdown hoặc HTML.")
    b.figure("report", SHOT / "f16_report.jpg", "3|Báo cáo pipeline tuần do hệ thống tạo (bản nháp chờ duyệt)")

    b.heading(3, "3.2.8. Giao diện nhập dữ liệu (ETL)")
    b.para("Trang ETL là demo của Task 1. Người dùng tải lên một hoặc nhiều tệp (có thể kèm bộ dữ liệu mẫu trên máy chủ) "
           "rồi bấm Chạy ETL. Kết quả hiển thị các chỉ số của lần chạy và log chi tiết. Hình 3.22 là lần nạp bổ sung tệp "
           "google_form_tuan_moi.csv gồm 4 câu trả lời mới: hệ thống tạo 2 ứng viên mới, nhận ra 1 ứng viên đã có (cùng "
           "email nhưng viết hoa, SĐT dạng +84, tên không dấu) để gộp vào hồ sơ cũ và loại 1 bản ghi thiếu thông tin liên "
           "hệ. Bên dưới là lịch sử các lần chạy và tab xem các bản ghi bị loại kèm lý do.")
    b.figure("etlui", SHOT / "f06_etl.jpg", "3|Nhập dữ liệu đa nguồn và log ETL")

    b.heading(3, "3.2.9. Giao diện dành cho hiring manager – hai vai trò thấy dữ liệu khác nhau")
    b.para("Đây là demo của Task 5. Khi đăng nhập bằng tài khoản quản lý khối Dữ liệu & AI, menu chỉ còn các trang được "
           "phép, dashboard tự giới hạn phạm vi “Khối Dữ liệu & AI” (106 hồ sơ của 3 vị trí, so với 331 hồ sơ toàn công ty "
           "mà HR thấy sau lần nạp bổ sung), và trang ứng viên hiển thị ở chế độ ẩn danh.")
    b.figure("mgrdash", SHOT / "f17_mgr_dash.jpg", "3|Dashboard của hiring manager – chỉ dữ liệu phòng ban mình")
    b.figure("mgrcand", SHOT / "f18_mgr_cand.jpg", "3|Danh sách hồ sơ ở chế độ ẩn danh của hiring manager")
    b.para("Chi tiết ứng viên với hiring manager chỉ có mã ứng viên và chữ viết tắt, email và số điện thoại bị che, giới "
           "tính, ngày sinh, nơi ở bị ẩn; thẻ Nhận xét AI chỉ hiển thị những nhận xét đã được HR duyệt. Bảng 3.12 so sánh "
           "dữ liệu mà hai vai trò nhìn thấy với cùng một hệ thống.")
    b.figure("mgrdetail", SHOT / "f19_mgr_detail.jpg", "3|Chi tiết ứng viên dưới góc nhìn hiring manager (đã che PII)")
    b.table("haivaitro", "3|So sánh dữ liệu hiển thị cho HR và hiring manager",
            ["Nội dung", "HR (hr.lan)", "Hiring manager (manager.data)"],
            [["Phạm vi hồ sơ", "Toàn công ty – 331 hồ sơ, 10 vị trí", "Khối Dữ liệu & AI – 106 hồ sơ, 3 vị trí"],
             ["Tên ứng viên (cùng một người)", "Phan Thị Mỹ Duyên", "UV-00316 · P.T.M.D."],
             ["Email / SĐT", "duyen.phan01@gmail.com / 0386555777", "d***@gmail.com / 03******77"],
             ["Giới tính, ngày sinh, nơi ở", "Hiển thị", "Ẩn"],
             ["CV", "Nguyên bản", "Đã ẩn danh"],
             ["Nhận xét AI", "Tất cả (kể cả chờ duyệt)", "Chỉ bản đã duyệt"],
             ["Menu", "Có AI, kiểm duyệt, công bằng, ETL", "Chỉ tổng quan, ứng viên, báo cáo, tài khoản"],
             ["Gọi API quản trị (/api/users, /api/etl/runs…)", "Được phép (trừ quản lý người dùng)", "HTTP 403"]],
            [4.6, 5.4, 6.0])
    b.para("Báo cáo tuần chỉ xuất hiện với hiring manager sau khi đã được HR duyệt; chân báo cáo ghi rõ người kiểm duyệt.")
    b.figure("mgrreport", SHOT / "f21_mgr_report.jpg", "3|Hiring manager xem báo cáo tuần đã được duyệt")

    b.heading(3, "3.2.10. Giao diện quản trị: người dùng và nhật ký hệ thống")
    b.para("Quản trị viên xem danh sách tài khoản, ma trận phân quyền, tạo tài khoản mới (bắt buộc gắn phòng ban với "
           "hiring manager), đổi vai trò/phòng ban, khoá tài khoản và đặt lại mật khẩu. Trang nhật ký hệ thống liệt kê các "
           "thao tác quan trọng (đăng nhập, xem thông tin cá nhân, chạy AI, kiểm duyệt, tạo/duyệt báo cáo, chạy ETL) và "
           "cho phép lọc theo loại hành động.")
    b.figure("users", SHOT / "f22_users.jpg", "3|Quản lý người dùng và ma trận phân quyền", width_cm=15)
    b.figure("audit", SHOT / "f23_audit.jpg", "3|Nhật ký hệ thống (audit log)")

    # ---------------------------------------------------------------- 3.3 Kiểm thử & triển khai
    b.heading(2, "3.3. Kiểm thử, thực nghiệm và triển khai")
    b.heading(3, "3.3.1. Kiểm thử tự động")
    b.para("Bộ kiểm thử pytest chạy trên một cơ sở dữ liệu PostgreSQL riêng: trước khi chạy, toàn bộ lược đồ được tạo lại "
           "và bộ dữ liệu mẫu được nạp qua đúng luồng khởi động của ứng dụng. Kết quả: **45/45 kiểm thử đạt** trong "
           "khoảng 11 giây (Bảng 3.13).")
    b.table("test", "3|Kết quả kiểm thử tự động",
            ["Tệp kiểm thử", "Số ca", "Nội dung kiểm tra", "Kết quả"],
            [["test_normalize.py", "26", "Chuẩn hoá SĐT, email, tên, ngày giờ (múi giờ, serial Excel), kinh nghiệm, lương, "
              "điểm; ánh xạ nguồn/vòng/trạng thái; nhận diện vị trí", "Đạt"],
             ["test_etl.py", "4", "Khôi phục đúng 314 ứng viên/329 hồ sơ, không email trùng, không thời lượng âm, email rút "
              "hồ sơ cập nhật trạng thái, chạy lại không phát sinh dữ liệu", "Đạt"],
             ["test_ai.py", "6", "Trích xuất & phân nhóm kỹ năng, ẩn danh CV, bộ lọc thiên vị, phân loại lý do, engine nội "
              "bộ, định dạng lời gọi Claude (client giả lập)", "Đạt"],
             ["test_api.py", "9", "Đăng nhập, hai vai trò thấy dữ liệu khác nhau, 403 với quản lý, chỉ số dashboard, luồng "
              "kiểm duyệt AI, chặn nhận xét thiên vị, báo cáo tuần, quản lý người dùng", "Đạt"]],
            [3.2, 1.4, 9.6, 1.8])
    b.heading(3, "3.3.2. Kết quả thực nghiệm trên bộ dữ liệu mẫu")
    b.para("Bộ dữ liệu mẫu được sinh có chủ đích với “đáp án” biết trước: 314 ứng viên thật và 329 hồ sơ thật được rải "
           "trên 4 nguồn thành 500 bản ghi thô, kèm 185 tệp CV. Bảng 3.14 cho thấy ETL khôi phục chính xác số ứng viên và "
           "số hồ sơ, đúng 48 hồ sơ rút (trong đó 11 hồ sơ chỉ được biết là đã rút qua email) và loại đúng 5 bản ghi lỗi "
           "được cài sẵn.")
    b.table("thucnghiem", "3|Kết quả ETL trên bộ dữ liệu mẫu",
            ["Chỉ tiêu", "Kết quả", "Ghi chú"],
            [["Bản ghi thô", "500", "10 vị trí ATS, 191 hồ sơ ATS, 159 dòng Excel, 117 dòng Form, 23 email"],
             ["Bản ghi hợp lệ / bị loại", "485 / 5", "Loại: 2 vị trí không xác định, 1 thiếu tên, 1 thiếu liên hệ, 1 email "
              "rút hồ sơ không khớp"],
             ["Ứng viên sau khử trùng", "314 (đúng 314)", "Gộp 160 bản ghi trùng: 158 theo email, 2 theo SĐT"],
             ["Hồ sơ ứng tuyển", "329 (đúng 329)", "145 bản ghi hồ sơ trùng giữa các nguồn được gộp"],
             ["Sự kiện vòng", "1.027", "208 sự kiện trùng được hợp nhất"],
             ["Trạng thái", "36 đang xử lý, 24 nhận việc, 221 bị loại, 48 rút", "Khớp hoàn toàn dữ liệu gốc"],
             ["Kỹ năng / lý do", "242 ứng viên có kỹ năng; 269 lý do được phân nhóm", "NLP dựa trên từ điển và luật"],
             ["Chạy lại cùng dữ liệu", "0 bản ghi mới", "Toàn bộ bản ghi đã nạp được bỏ qua (idempotent)"],
             ["Thời gian chạy", "≈ 6 giây", "Bao gồm trích văn bản 185 CV"]],
            [4.0, 4.6, 7.4])
    b.para("Các chỉ số pipeline trên dữ liệu mẫu cũng phản ánh đúng các điểm nghẽn được cài vào kịch bản mô phỏng: thời "
           "gian chờ phỏng vấn chuyên môn dài ở khối Công nghệ và Dữ liệu (trung vị 7,0 ngày), tỷ lệ qua vòng chuyên môn "
           "thấp nhất (47,3%) và một phần đáng kể ứng viên rút hồ sơ vì đã nhận offer nơi khác trong lúc chờ. Điều này cho "
           "thấy các chỉ số và quy tắc phát hiện điểm nghẽn hoạt động đúng như thiết kế.")

    b.heading(3, "3.3.3. Triển khai online")
    b.para("Sản phẩm được đóng gói bằng một Dockerfile dùng chung; biến môi trường SERVICE chọn chạy API (api), giao diện "
           "(web) hoặc cả hai trong một container (all). Phương án khuyến nghị là Render (Hình 3.29): tệp render.yaml mô tả "
           "một CSDL PostgreSQL và hai dịch vụ web; khi đẩy mã lên GitHub, Render tự build và triển khai, cấp URL HTTPS "
           "công khai. Ở lần khởi động đầu, API tự tạo bảng, tài khoản demo và nạp bộ dữ liệu mẫu. Phương án thay thế là "
           "Hugging Face Spaces (một container, SERVICE=all) kết hợp PostgreSQL miễn phí của Neon, hoặc docker compose "
           "trên máy chủ riêng. Hướng dẫn chi tiết có trong tệp docs/DEPLOY.md.")
    b.figure("deploy", IMG / "trien_khai.png", "3|Sơ đồ triển khai online")
    b.bullets([
        "Mã nguồn: github.com/PhucHoang3010/Vietnamese-News-Classification (thư mục recruitment-ai-warehouse).",
        "Địa chỉ sản phẩm sau khi triển khai: ……………………………………………… (nhóm điền URL của dịch vụ talentlens-web).",
        "Tài liệu API: <URL dịch vụ talentlens-api>/docs.",
    ])

    b.heading(2, "3.4. Đánh giá mức độ đáp ứng yêu cầu")
    b.table("danhgia", "3|Đánh giá mức độ đáp ứng yêu cầu của đề tài",
            ["Yêu cầu", "Kết quả", "Mức độ"],
            [["Task 1 – ETL đa nguồn vào PostgreSQL, API FastAPI, khung Streamlit", "4 nguồn + CV; staging; log ETL; 34 "
              "endpoint; 10 trang giao diện", "Đạt"],
             ["Task 2 – DDL, chuẩn hoá, khử trùng", "Lược đồ hình sao 14 bảng; sql/schema.sql; 10 truy vấn mẫu; khôi phục "
              "đúng 314/329", "Đạt"],
             ["Task 3 – Tỷ lệ chuyển đổi, thời gian, điểm nghẽn, biểu đồ", "Phễu, tỷ lệ qua vòng, SLA, 4 quy tắc điểm "
              "nghẽn, nguồn, xu hướng", "Đạt"],
             ["Task 4 – Trích CV, tóm tắt, kỹ năng, lý do rớt, câu hỏi PV", "Engine Claude + engine NLP nội bộ; demo xử lý "
              "CV mẫu", "Đạt (Claude cần API key)"],
             ["Task 5 – RBAC, ẩn PII, kiểm duyệt AI, báo cáo tuần, deploy", "3 vai trò; che PII; bias guard; kiểm duyệt; "
              "báo cáo; Docker/Render", "Đạt (cần nhóm thực hiện deploy)"],
             ["Sản phẩm web hoàn chỉnh, đăng nhập & phân quyền, quản lý user", "Có đầy đủ; không phải notebook/CLI", "Đạt"],
             ["Deployed online có URL", "Đã chuẩn bị Dockerfile, render.yaml, hướng dẫn", "Cần triển khai lên tài khoản "
              "của nhóm"]],
            [6.0, 6.8, 3.2])

    # ============================================================ KẾT LUẬN
    b.heading(1, "KẾT LUẬN", page_break=True)
    b.heading(2, "1. Kết quả đạt được")
    b.para("Đề tài đã xây dựng thành công TalentLens – một sản phẩm web hoàn chỉnh viết bằng Python, đáp ứng mục tiêu "
           "đặt ra ở Chương 1. Về dữ liệu, hệ thống hợp nhất bốn nguồn rời rạc (Google Form, ATS, Excel, email kèm CV) vào "
           "kho dữ liệu PostgreSQL theo lược đồ hình sao; quy trình ETL chuẩn hoá được các lỗi định dạng phổ biến, khử "
           "trùng ứng viên theo email – số điện thoại – họ tên và ngày sinh, có staging, vân tay chống nạp trùng và log "
           "chi tiết. Trên bộ dữ liệu mẫu, ETL khôi phục chính xác 314 ứng viên và 329 hồ sơ từ 500 bản ghi thô.")
    b.para("Về phân tích, dashboard cung cấp đầy đủ phễu tuyển dụng, tỷ lệ qua từng vòng, thời gian chuyển vòng so với "
           "SLA, phát hiện điểm nghẽn tự động, hiệu quả nguồn, xu hướng tuần và lý do rớt. Về AI, hệ thống tóm tắt CV, "
           "phân nhóm kỹ năng, đối chiếu JD, gợi ý câu hỏi phỏng vấn, phân tích lý do rớt và viết báo cáo tuần, với kiến "
           "trúc hai engine (Claude và NLP nội bộ) giúp sản phẩm luôn hoạt động. Về an toàn, hệ thống có phân quyền ba "
           "vai trò, che thông tin cá nhân, ẩn danh CV trước khi gửi AI, bộ lọc thiên vị cho cả nhận xét của AI và của "
           "con người, luồng kiểm duyệt bắt buộc, giám sát công bằng theo quy tắc 4/5 và nhật ký kiểm toán. Chất lượng mã "
           "nguồn được đảm bảo bằng 45 kiểm thử tự động.")
    b.para("So với các giải pháp thủ công bằng Excel, sản phẩm giúp số liệu nhất quán, cập nhật nhanh và giảm công tổng "
           "hợp báo cáo. So với việc dùng trực tiếp các công cụ AI đại trà, sản phẩm kiểm soát tốt hơn dữ liệu cá nhân và "
           "rủi ro thiên vị. Qua đề tài, nhóm rút ra bài học: chất lượng dữ liệu quyết định chất lượng phân tích; cần thiết "
           "kế để chạy lại an toàn ngay từ đầu; và AI trong lĩnh vực nhân sự phải luôn đi kèm cơ chế để con người kiểm soát.")
    b.heading(2, "2. Hạn chế")
    b.bullets([
        "Dữ liệu thực nghiệm là dữ liệu giả lập; chưa kiểm chứng trên dữ liệu tuyển dụng thật của doanh nghiệp.",
        "Engine NLP nội bộ dựa trên luật và từ điển nên tóm tắt còn đơn giản; chất lượng cao hơn cần cấu hình Claude API "
        "(có chi phí). Chưa có bộ đánh giá (eval) định lượng chất lượng tóm tắt của AI.",
        "Chưa hỗ trợ CV dạng ảnh scan (OCR); ETL đọc tệp xuất thay vì kết nối trực tiếp API của ATS, Gmail, Google Sheets.",
        "Giám sát công bằng mới xét thuộc tính giới tính và chưa có kiểm định thống kê cho mẫu nhỏ; trạng thái hồ sơ "
        "trong báo cáo các tuần đã qua được tính gần đúng theo trạng thái hiện tại.",
        "Giao diện Streamlit phù hợp nội bộ nhưng hạn chế về tuỳ biến so với một frontend chuyên dụng.",
    ])
    b.heading(2, "3. Hướng phát triển")
    b.para("Trước hết, nhóm sẽ hoàn thiện các chức năng hiện có: triển khai chính thức và theo dõi vận hành trên môi "
           "trường online, bổ sung OCR cho CV ảnh, lập lịch ETL tự động hằng ngày, gửi báo cáo tuần qua email và lưu lịch "
           "sử trạng thái theo thời điểm (snapshot) để báo cáo quá khứ chính xác tuyệt đối.")
    b.para("Về lâu dài, hệ thống có thể kết nối trực tiếp với ATS, Gmail và Google Sheets qua API; xây dựng bộ đánh giá "
           "chất lượng tóm tắt CV và câu hỏi phỏng vấn để so sánh các mô hình; mở rộng giám sát công bằng sang nhiều thuộc "
           "tính hơn với kiểm định thống kê; dự báo thời gian tuyển và khả năng ứng viên rút hồ sơ bằng học máy; và chuyển "
           "giao diện sang một framework frontend (React) khi số người dùng tăng.")

    # ============================================================ TÀI LIỆU THAM KHẢO
    b.heading(1, "DANH MỤC TÀI LIỆU THAM KHẢO", page_break=True)
    refs = [
        "R. Kimball and M. Ross, *The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling*, 3rd ed. "
        "Indianapolis, IN, USA: Wiley, 2013.",
        "W. H. Inmon, *Building the Data Warehouse*, 4th ed. Indianapolis, IN, USA: Wiley, 2005.",
        "W. McKinney, *Python for Data Analysis: Data Wrangling with pandas, NumPy, and Jupyter*, 3rd ed. Sebastopol, "
        "CA, USA: O’Reilly Media, 2022.",
        "F. Pedregosa et al., “Scikit-learn: Machine learning in Python,” *Journal of Machine Learning Research*, vol. "
        "12, pp. 2825–2830, 2011.",
        "A. Vaswani et al., “Attention is all you need,” in *Advances in Neural Information Processing Systems 30 "
        "(NIPS 2017)*, 2017, pp. 5998–6008.",
        "G. Salton and C. Buckley, “Term-weighting approaches in automatic text retrieval,” *Information Processing & "
        "Management*, vol. 24, no. 5, pp. 513–523, 1988.",
        "D. F. Ferraiolo and D. R. Kuhn, “Role-based access controls,” in *Proc. 15th National Computer Security "
        "Conference*, Baltimore, MD, USA, 1992, pp. 554–563.",
        "R. S. Sandhu, E. J. Coyne, H. L. Feinstein, and C. E. Youman, “Role-based access control models,” *IEEE "
        "Computer*, vol. 29, no. 2, pp. 38–47, 1996.",
        "M. Jones, J. Bradley, and N. Sakimura, “JSON Web Token (JWT),” RFC 7519, Internet Engineering Task Force, "
        "May 2015.",
        "Equal Employment Opportunity Commission et al., “Uniform Guidelines on Employee Selection Procedures,” 29 CFR "
        "Part 1607, 1978.",
        "J. Dastin, “Amazon scraps secret AI recruiting tool that showed bias against women,” *Reuters*, Oct. 10, 2018.",
        "M. Raghavan, S. Barocas, J. Kleinberg, and K. Levy, “Mitigating bias in algorithmic hiring: Evaluating claims "
        "and practices,” in *Proc. 2020 Conference on Fairness, Accountability, and Transparency (FAT* ’20)*, 2020, "
        "pp. 469–481.",
        "Quốc hội nước Cộng hoà xã hội chủ nghĩa Việt Nam, *Bộ luật Lao động*, Luật số 45/2019/QH14, 2019.",
        "Chính phủ nước Cộng hoà xã hội chủ nghĩa Việt Nam, *Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân*, "
        "ngày 17/4/2023.",
        "S. Ramírez, “FastAPI documentation.” [Online]. Available: https://fastapi.tiangolo.com (truy cập 11/2026).",
        "The PostgreSQL Global Development Group, “PostgreSQL 16 Documentation.” [Online]. Available: "
        "https://www.postgresql.org/docs/16/ (truy cập 11/2026).",
        "Snowflake Inc., “Streamlit documentation.” [Online]. Available: https://docs.streamlit.io (truy cập 11/2026).",
        "Anthropic, “Claude API documentation.” [Online]. Available: https://docs.anthropic.com (truy cập 11/2026).",
        "SQLAlchemy authors, “SQLAlchemy 2.0 Documentation.” [Online]. Available: https://docs.sqlalchemy.org/en/20/ "
        "(truy cập 11/2026).",
        "Plotly Technologies Inc., “Plotly Python Graphing Library.” [Online]. Available: https://plotly.com/python/ "
        "(truy cập 11/2026).",
        "P. Christen, *Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate "
        "Detection*. Berlin, Germany: Springer, 2012.",
    ]
    for i, ref in enumerate(refs, start=1):
        b.para(f"[{i}] {ref}", style="ThamKhao")

    # ============================================================ PHỤ LỤC
    b.heading(1, "PHỤ LỤC", page_break=True)
    b.heading(2, "Phụ lục A. Hướng dẫn cài đặt và chạy hệ thống")
    b.para("Yêu cầu: Python 3.12+ và PostgreSQL 16 (hoặc Docker). Chạy trên máy cá nhân:")
    b.code("""cd recruitment-ai-warehouse
pip install -r requirements.txt
cp .env.example .env                      # sửa DATABASE_URL, JWT_SECRET, ANTHROPIC_API_KEY (tuỳ chọn)
uvicorn app.main:app --port 8000          # lần đầu tự tạo bảng, tài khoản demo, nạp dữ liệu mẫu
streamlit run frontend/app.py             # mở http://localhost:8501

# hoặc chạy toàn bộ bằng Docker
docker compose up --build

# kiểm thử
TEST_DATABASE_URL=postgresql+psycopg://hr_admin:hr_admin_pw@localhost:5432/recruitment_test pytest -q""")
    b.table("taikhoan", "PL|Tài khoản demo",
            ["Tài khoản", "Mật khẩu", "Vai trò", "Phạm vi"],
            [["admin", "Admin@123", "Quản trị hệ thống", "Toàn bộ + quản lý người dùng, nhật ký"],
             ["hr.lan", "Demo@123", "HR", "Toàn công ty, có thông tin cá nhân"],
             ["manager.data", "Demo@123", "Hiring manager", "Khối Dữ liệu & AI, dữ liệu đã che"],
             ["manager.tech", "Demo@123", "Hiring manager", "Khối Công nghệ, dữ liệu đã che"]],
            [3.2, 2.8, 3.6, 6.4])
    b.heading(2, "Phụ lục B. Cấu trúc mã nguồn")
    b.code("""recruitment-ai-warehouse/
├── app/                    Backend FastAPI
│   ├── etl/                extract · normalize · transform · load · pipeline
│   ├── ai/                 skills · anonymizer · bias_guard · cv_parser · rejection
│   │                       local_engine · claude_engine · service
│   ├── services/           analytics · reports · audit
│   ├── routers/            auth · candidates · analytics · ai · etl · reports
│   ├── models.py           Mô hình kho dữ liệu (SQLAlchemy)
│   ├── rbac.py, security.py  Phân quyền, che dữ liệu, JWT, băm mật khẩu
│   └── main.py, seed.py    Khởi tạo ứng dụng và dữ liệu
├── frontend/               Streamlit: app.py + views/ (10 trang)
├── data/raw/               Dữ liệu mẫu 4 nguồn + 185 CV
├── sql/                    schema.sql (DDL) · sample_queries.sql
├── scripts/                Sinh dữ liệu mẫu, xuất DDL
├── tests/                  45 kiểm thử pytest
├── docs/                   Sơ đồ, hướng dẫn triển khai, báo cáo
├── Dockerfile, docker-compose.yml, render.yaml, start.sh
└── requirements.txt""")
    b.heading(2, "Phụ lục C. Trích đoạn mã nguồn tiêu biểu")
    b.para("**C.1. Chuẩn hoá số điện thoại Việt Nam** (app/etl/normalize.py)", style="NoiDung")
    b.code("""def normalize_phone(value):
    \"\"\"Chuẩn hoá số di động Việt Nam về dạng 0xxxxxxxxx (10 số).\"\"\"
    if is_blank(value):
        return None
    if isinstance(value, float):
        value = f"{value:.0f}"
    digits = re.sub(r"\\D", "", str(value))
    if digits.startswith("84") and len(digits) == 11:
        digits = "0" + digits[2:]
    elif len(digits) == 9 and not digits.startswith("0"):      # Excel làm mất số 0
        digits = "0" + digits
    if len(digits) == 10 and digits.startswith("0") and digits[1] in "35789":
        return digits
    return None""")
    b.para("**C.2. Định danh ứng viên khi khử trùng** (app/etl/load.py)", style="NoiDung")
    b.code("""def find(self, rec):
    if rec.email and rec.email in self.by_email:
        return self.by_email[rec.email], "email"
    if rec.phone and rec.phone in self.by_phone:
        return self.by_phone[rec.phone], "phone"
    key = name_dob_key(rec.full_name, rec.date_of_birth)     # họ tên không dấu + ngày sinh
    if key and key in self.by_name_dob:
        return self.by_name_dob[key], "name+dob"
    return None, None""")
    b.para("**C.3. Che dữ liệu theo vai trò** (app/serializers.py)", style="NoiDung")
    b.code("""pii = has_perm(user, "pii:read")
data = {
    "display_name": c.full_name if pii else f"{c.candidate_code} · {initials(c.full_name)}",
    "email": c.email if pii else mask_email(c.email),       # n***@gmail.com
    "phone": c.phone if pii else mask_phone(c.phone),       # 09******78
    "gender": c.gender if pii else None,
    "date_of_birth": iso(c.date_of_birth) if pii else None,
    ...
}""")
    b.para("**C.4. Bắt buộc ghi chú khi duyệt nhận xét AI bị gắn cờ thiên vị** (app/ai/service.py)", style="NoiDung")
    b.code("""if action == "approve":
    if insight.bias_flags and not (note or "").strip():
        raise HTTPException(400, "Nội dung có cờ thiên vị – cần chỉnh sửa "
                                 "hoặc ghi chú lý do trước khi duyệt")
    insight.status = "approved"
insight.reviewed_by, insight.reviewed_at, insight.review_note = user.id, now_vn(), note
log_action(db, user, f"ai:review:{action}", "ai_insight", insight.id)""")
