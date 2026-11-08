"""Engine NLP nội bộ (không cần Internet / API key).

Dùng làm phương án dự phòng khi chưa cấu hình Claude hoặc khi gọi API lỗi.
Kỹ thuật: từ điển kỹ năng, tách mục CV, TF-IDF cosine CV–JD, luật từ khoá, mẫu câu.
"""
from __future__ import annotations

import re

from app.ai.cv_parser import guess_education, guess_years_experience, split_sections
from app.ai.rejection import CATEGORY_LABELS, RECOMMENDATIONS
from app.ai.skills import extract_skills, group_skills, match_jd
from app.utils import strip_accents

AVOID_TOPICS = [
    "Tuổi, năm sinh, kế hoạch kết hôn/sinh con, tình trạng hôn nhân",
    "Quê quán, vùng miền, giọng nói, dân tộc, tôn giáo",
    "Ngoại hình, chiều cao, cân nặng, tình trạng sức khoẻ không liên quan công việc",
    "Nghề nghiệp/thu nhập của bố mẹ, vợ/chồng",
]

QUESTION_BANK: dict[str, list[str]] = {
    "SQL": ["Hãy viết (mô tả) truy vấn SQL tính tỷ lệ chuyển đổi giữa hai vòng tuyển dụng theo từng tháng. "
            "Bạn dùng JOIN/CTE/Window function nào và vì sao?",
            "Một truy vấn chạy chậm trên bảng 50 triệu dòng – bạn sẽ chẩn đoán và tối ưu như thế nào?"],
    "Python": ["Bạn đã dùng Python (Pandas) để làm sạch một bộ dữ liệu bẩn như thế nào? Nêu các bước và cách kiểm "
               "chứng kết quả.",
               "Giải thích sự khác nhau giữa list, tuple, dict, set và khi nào bạn chọn từng loại."],
    "Power BI": ["Hãy kể về một dashboard Power BI bạn xây dựng: ai dùng, chỉ số chính là gì, mô hình dữ liệu ra sao?"],
    "Excel": ["Bạn xử lý 1 file Excel 100.000 dòng, nhiều định dạng ngày khác nhau như thế nào để báo cáo chính xác?"],
    "Thống kê": ["Khi so sánh tỷ lệ chuyển đổi của hai nguồn tuyển dụng, bạn kiểm tra ý nghĩa thống kê bằng cách nào?"],
    "ETL": ["Mô tả một pipeline ETL bạn từng làm: nguồn, cách xử lý lỗi, cách đảm bảo chạy lại không bị trùng dữ liệu "
            "(idempotent)."],
    "Airflow": ["Bạn thiết kế DAG Airflow thế nào để retry an toàn và theo dõi SLA?"],
    "PostgreSQL": ["Khi nào bạn dùng index B-tree, khi nào dùng partition trong PostgreSQL? Cho ví dụ thực tế."],
    "Machine Learning": ["Bạn đánh giá một mô hình phân loại mất cân bằng dữ liệu bằng các chỉ số nào và vì sao?"],
    "Deep Learning": ["Mô tả cách bạn xử lý overfitting khi huấn luyện mạng nơ-ron trên tập dữ liệu nhỏ."],
    "NLP": ["Với văn bản tiếng Việt, bạn xử lý tách từ, chuẩn hoá dấu và biểu diễn văn bản như thế nào?"],
    "PyTorch": ["Hãy mô tả vòng lặp huấn luyện PyTorch bạn hay dùng và cách theo dõi thí nghiệm."],
    "LLM": ["Khi tích hợp LLM vào sản phẩm, bạn kiểm soát ảo giác (hallucination) và dữ liệu nhạy cảm ra sao?"],
    "FastAPI": ["Bạn tổ chức một dự án FastAPI (router, dependency, schema, kiểm thử) như thế nào?"],
    "REST API": ["Thiết kế API phân trang, lọc và phân quyền cho danh sách ứng viên – bạn chọn chuẩn nào?"],
    "Git": ["Quy trình làm việc nhóm với Git của bạn (branch, pull request, xử lý conflict) như thế nào?"],
    "Docker": ["Bạn tối ưu kích thước Docker image và quản lý biến môi trường/bí mật như thế nào?"],
    "ReactJS": ["Giải thích cách bạn quản lý state và tối ưu re-render trong một ứng dụng React lớn."],
    "TypeScript": ["Lợi ích của TypeScript trong dự án của bạn là gì? Cho ví dụ về generic type bạn đã viết."],
    "JavaScript": ["Giải thích event loop trong JavaScript và một lỗi bất đồng bộ bạn từng gặp."],
    "HTML/CSS": ["Bạn đảm bảo giao diện responsive và dễ tiếp cận (accessibility) bằng cách nào?"],
    "Manual testing": ["Với chức năng đăng nhập, hãy liệt kê các test case quan trọng (bao gồm trường hợp biên)."],
    "Test case": ["Bạn ưu tiên test case thế nào khi thời gian kiểm thử bị rút ngắn một nửa?"],
    "Automation test": ["Khi nào nên tự động hoá kiểm thử và khi nào không? Bạn đo hiệu quả automation ra sao?"],
    "Tuyển dụng": ["Hãy kể về một vị trí khó tuyển bạn từng phụ trách: bạn tìm nguồn ứng viên như thế nào và kết quả?"],
    "Phỏng vấn": ["Bạn xây dựng bộ câu hỏi phỏng vấn có cấu trúc (structured interview) như thế nào để giảm cảm tính?"],
    "Bán hàng B2B": ["Mô tả chu trình bán hàng B2B dài nhất bạn từng chốt: các bên liên quan và bước then chốt."],
    "Đàm phán": ["Kể về một lần đàm phán khách hàng yêu cầu giảm giá mạnh – bạn xử lý thế nào?"],
    "CRM": ["Bạn dùng CRM để quản lý pipeline và dự báo doanh số như thế nào?"],
    "SEO": ["Bạn lên kế hoạch SEO cho một website mới ra sao và đo hiệu quả bằng chỉ số nào?"],
    "Facebook Ads": ["Chiến dịch Facebook Ads có CPA tăng 40% – bạn phân tích và tối ưu theo các bước nào?"],
    "Google Ads": ["Bạn cấu trúc tài khoản Google Ads và chọn chiến lược giá thầu như thế nào?"],
    "Kế toán": ["Trình bày quy trình khoá sổ cuối tháng bạn đang thực hiện."],
    "Thuế": ["Bạn cập nhật và áp dụng thay đổi chính sách thuế mới vào công việc như thế nào?"],
    "Báo cáo tài chính": ["Bạn kiểm tra tính nhất quán giữa các báo cáo tài chính bằng những bước nào?"],
}

BEHAVIORAL = [
    ("Hãy kể về một lần bạn phải hoàn thành công việc với thời hạn rất gấp. Bạn đã ưu tiên và phối hợp như thế nào? "
     "(trả lời theo STAR)", "Đánh giá khả năng quản lý thời gian & áp lực",
     "Nêu rõ tình huống, hành động cụ thể của bản thân, kết quả đo lường được"),
    ("Kể về một lần bạn bất đồng quan điểm với đồng nghiệp/quản lý. Bạn xử lý ra sao?",
     "Đánh giá giao tiếp & làm việc nhóm", "Lắng nghe, dựa trên dữ liệu, hướng tới giải pháp chung"),
    ("Kỹ năng/công nghệ mới gần nhất bạn tự học là gì và bạn đã áp dụng nó vào việc gì?",
     "Đánh giá khả năng tự học", "Có ví dụ cụ thể, có sản phẩm/kết quả"),
]

SITUATIONAL = {
    "DATA": ("Dashboard tuyển dụng cho thấy tỷ lệ qua vòng chuyên môn giảm 20% trong tháng này. Bạn sẽ phân tích "
             "nguyên nhân như thế nào và trình bày với quản lý ra sao?",
             "Tư duy phân tích dữ liệu", "Kiểm tra chất lượng dữ liệu, phân tách theo nguồn/vị trí, đề xuất hành động"),
    "TECH": ("API của hệ thống bị chậm vào giờ cao điểm sau một lần release. Bạn xử lý sự cố theo các bước nào?",
             "Xử lý sự cố kỹ thuật", "Khoanh vùng, đo lường, rollback/hotfix, rút kinh nghiệm"),
    "HR": ("Một hiring manager liên tục từ chối ứng viên mà không ghi lý do. Bạn sẽ làm gì?",
           "Phối hợp với hiring manager", "Thống nhất tiêu chí, dùng scorecard, dữ liệu để trao đổi"),
    "SALES": ("Khách hàng lớn đang so sánh bạn với đối thủ rẻ hơn 15%. Bạn sẽ tiếp cận như thế nào?",
              "Tư duy bán hàng giá trị", "Hiểu nhu cầu, chứng minh giá trị/ROI, không giảm giá vội"),
    "MKT": ("Ngân sách quảng cáo bị cắt 30% nhưng KPI không đổi. Bạn phân bổ lại như thế nào?",
            "Tối ưu ngân sách marketing", "Dựa trên dữ liệu hiệu quả kênh, thử nghiệm A/B"),
    "FIN": ("Phát hiện chênh lệch số dư công nợ giữa sổ sách và đối chiếu khách hàng. Bạn xử lý thế nào?",
            "Kiểm soát nghiệp vụ kế toán", "Đối chiếu chứng từ, tìm nguyên nhân, điều chỉnh đúng quy định"),
}


def tfidf_similarity(text_a: str, text_b: str) -> float | None:
    """Độ tương đồng nội dung (cosine TF-IDF) giữa CV và JD, 0–100."""
    if not text_a or not text_b:
        return None
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:  # pragma: no cover
        return None
    docs = [strip_accents(text_a).lower(), strip_accents(text_b).lower()]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    matrix = vectorizer.fit_transform(docs)
    return round(float(cosine_similarity(matrix[0], matrix[1])[0][0]) * 100, 1)


def _bullets(section: str, limit: int = 3) -> list[str]:
    raw = [l.strip() for l in section.splitlines()]
    marked = [l for l in raw if l[:1] in "-•*+"]  # ưu tiên các gạch đầu dòng mô tả thành tích
    lines = [l.strip(" -•*+\t") for l in (marked or raw)]
    lines = [l for l in lines if 25 <= len(l) <= 220]
    scored = sorted(lines, key=lambda l: (bool(re.search(r"\d", l)), len(l)), reverse=True)
    return scored[:limit]


class LocalEngine:
    provider = "local"
    model_name = "talentlens-nlp-rules-v1"

    # ------------------------------------------------------------------ CV
    def analyze_cv(self, cv_text: str, position: dict | None, context: dict | None = None) -> dict:
        context = context or {}
        skills = extract_skills(cv_text + "\n" + (context.get("skills_text") or ""))
        groups = group_skills(skills)
        sections = split_sections(cv_text)
        years = context.get("years_experience")
        if years is None:
            years = guess_years_experience(cv_text)
        education = context.get("education_level") or guess_education(cv_text)
        title = context.get("current_title")

        jd_match = match_jd(skills, (position or {}).get("required_skills", []),
                            (position or {}).get("nice_to_have_skills", []))
        similarity = tfidf_similarity(cv_text, (position or {}).get("jd_text") or "")

        top_groups = sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True)[:3]
        group_txt = "; ".join(f"{g}: {', '.join(s[:4])}" for g, s in top_groups) or "chưa trích xuất được kỹ năng"
        exp_lines = _bullets(sections.get("experience", ""), 2)
        summary_parts = []
        if years is not None:
            summary_parts.append(f"Ứng viên có khoảng {years:g} năm kinh nghiệm")
        else:
            summary_parts.append("CV chưa nêu rõ số năm kinh nghiệm")
        if education:
            summary_parts[-1] += f", trình độ {education.lower()}"
        summary_parts[-1] += "."
        if exp_lines:
            summary_parts.append(f"Kinh nghiệm tiêu biểu: {exp_lines[0].rstrip('.')}.")
        summary_parts.append(f"Nhóm kỹ năng nổi bật – {group_txt}.")
        if position:
            summary_parts.append(
                f"So với yêu cầu vị trí {position.get('title')}: CV thể hiện "
                f"{len(jd_match['matched_required'])}/{len(position.get('required_skills', []))} kỹ năng bắt buộc."
            )

        highlights = _bullets(sections.get("experience", "") + "\n" + sections.get("projects", ""), 3)
        highlights += _bullets(sections.get("certificates", ""), 1)
        gaps = [f"Chưa thấy bằng chứng về {s} trong CV – nên hỏi thêm khi phỏng vấn." for s in jd_match["missing_required"]]
        if years is None:
            gaps.append("Cần xác nhận số năm kinh nghiệm thực tế.")

        headline_skills = ", ".join(skills[:3]) if skills else "chưa rõ kỹ năng"
        headline = f"{title or 'Ứng viên'} · {('%g năm KN' % years) if years is not None else 'KN chưa rõ'} · {headline_skills}"
        return {
            "headline": headline,
            "summary": " ".join(summary_parts),
            "highlights": highlights,
            "experience_years": years,
            "education": education,
            "skills": skills,
            "skill_groups": [{"group": g, "skills": s} for g, s in groups.items()],
            "jd_match": jd_match,
            "content_similarity_pct": similarity,
            "gaps": gaps,
            "evidence_note": "Tóm tắt được trích xuất tự động từ nội dung CV đã ẩn danh; không đánh giá con người.",
        }

    # ------------------------------------------------------- Câu hỏi PV
    def interview_questions(self, position: dict, analysis: dict | None) -> dict:
        analysis = analysis or {}
        jd_match = analysis.get("jd_match") or match_jd(analysis.get("skills", []), position.get("required_skills", []))
        questions: list[dict] = []
        for skill in jd_match.get("matched_required", [])[:4]:
            bank = QUESTION_BANK.get(skill)
            text = bank[0] if bank else (f"Hãy mô tả một dự án gần đây bạn sử dụng {skill}: bối cảnh, vai trò của bạn và "
                                          f"kết quả đo lường được.")
            questions.append({"category": "Chuyên môn", "question": text, "related_requirement": skill,
                              "purpose": f"Kiểm chứng mức độ thành thạo {skill} đã nêu trong CV",
                              "good_answer_signals": "Ví dụ cụ thể, giải thích được lựa chọn kỹ thuật, có số liệu"})
        for skill in jd_match.get("missing_required", [])[:3]:
            questions.append({
                "category": "Làm rõ yêu cầu JD", "related_requirement": skill,
                "question": f"Vị trí yêu cầu {skill}. Bạn đã tiếp xúc với {skill} ở mức độ nào? Nếu chưa, bạn sẽ học và áp "
                            f"dụng như thế nào trong 30 ngày đầu?",
                "purpose": f"CV chưa thể hiện {skill} – xác minh thay vì loại sớm",
                "good_answer_signals": "Trung thực về mức độ hiện tại, có kế hoạch học cụ thể, liên hệ kinh nghiệm tương đương",
            })
        for highlight in (analysis.get("highlights") or [])[:2]:
            questions.append({"category": "Làm rõ CV", "related_requirement": "Kinh nghiệm",
                              "question": f"CV có nêu: “{highlight[:140]}”. Vai trò cụ thể của bạn là gì và kết quả được "
                                          f"đo lường thế nào?",
                              "purpose": "Xác minh đóng góp cá nhân",
                              "good_answer_signals": "Phân biệt rõ phần việc cá nhân và của nhóm"})
        dept = position.get("department_code") or "DATA"
        sq = SITUATIONAL.get(dept, SITUATIONAL["DATA"])
        questions.append({"category": "Tình huống", "question": sq[0], "purpose": sq[1], "good_answer_signals": sq[2],
                          "related_requirement": "Giải quyết vấn đề"})
        for q, purpose, signals in BEHAVIORAL:
            questions.append({"category": "Hành vi (STAR)", "question": q, "purpose": purpose,
                              "good_answer_signals": signals, "related_requirement": "Kỹ năng mềm"})
        return {"questions": questions, "avoid_topics": AVOID_TOPICS,
                "scoring_guide": "Chấm từng câu theo thang 1–5 dựa trên tín hiệu trả lời tốt; ghi bằng chứng cụ thể."}

    # ------------------------------------------------- Lý do rớt phổ biến
    def rejection_insights(self, stats: dict) -> dict:
        total = stats.get("total", 0)
        top = []
        for item in stats.get("categories", [])[:6]:
            code = item["category"]
            top.append({
                "category": code, "label": CATEGORY_LABELS.get(code, code), "count": item["count"],
                "share_pct": item["share_pct"], "main_stages": item.get("main_stages", []),
                "examples": item.get("examples", [])[:3], "recommendation": RECOMMENDATIONS.get(code, ""),
            })
        if top:
            lead = top[0]
            overview = (f"Trong {total} hồ sơ bị loại/rút, nhóm lý do phổ biến nhất là “{lead['label']}” "
                        f"({lead['share_pct']}%), tập trung ở vòng {', '.join(lead['main_stages'][:2]) or 'nhiều vòng'}.")
            if len(top) > 1:
                overview += f" Tiếp theo là “{top[1]['label']}” ({top[1]['share_pct']}%)."
        else:
            overview = "Chưa có đủ dữ liệu lý do loại/rút hồ sơ."
        withdrawn = stats.get("withdrawn", 0)
        actions = [t["recommendation"] for t in top[:3] if t["recommendation"]]
        if withdrawn and total and withdrawn / total > 0.25:
            actions.append("Tỷ lệ ứng viên chủ động rút cao – cần rút ngắn thời gian phản hồi giữa các vòng.")
        return {"overview": overview, "top_reasons": top, "actions": actions}

    # ---------------------------------------------------- Báo cáo tuần
    def weekly_narrative(self, metrics: dict) -> dict:
        cur = metrics.get("current", {})
        prev = metrics.get("previous", {})

        def delta(key):
            a, b = cur.get(key, 0) or 0, prev.get(key, 0) or 0
            if b == 0:
                return ""
            return f" ({'+' if a >= b else ''}{(a - b) / b * 100:.0f}% so với tuần trước)"

        summary = (f"Tuần {metrics.get('week_label')}: nhận {cur.get('new_applications', 0)} hồ sơ mới"
                   f"{delta('new_applications')}, {cur.get('interviews', 0)} lượt phỏng vấn, "
                   f"{cur.get('offers', 0)} offer và {cur.get('hires', 0)} ứng viên nhận việc.")
        highlights = []
        if cur.get("top_source"):
            highlights.append(f"Nguồn mang lại nhiều hồ sơ nhất: {cur['top_source']}.")
        if cur.get("top_position"):
            highlights.append(f"Vị trí nhận nhiều hồ sơ nhất: {cur['top_position']}.")
        if cur.get("hires"):
            highlights.append(f"Có {cur['hires']} ứng viên nhận việc trong tuần.")
        risks = []
        for b in metrics.get("bottlenecks", [])[:2]:
            risks.append(b.get("message", ""))
        if cur.get("stuck_applications"):
            risks.append(f"{cur['stuck_applications']} hồ sơ đang quá hạn SLA ở vòng hiện tại.")
        if cur.get("top_rejection_reason"):
            risks.append(f"Lý do loại/rút phổ biến trong tuần: {cur['top_rejection_reason']}.")
        actions = ["Ưu tiên xử lý các hồ sơ quá hạn SLA trước cuối tuần tới.",
                   "Rà soát lịch phỏng vấn ở vòng đang là điểm nghẽn, bổ sung người phỏng vấn nếu cần."]
        if cur.get("withdrawn"):
            actions.append("Liên hệ lại ứng viên đang chờ lâu để giảm tỷ lệ rút hồ sơ.")
        return {"summary": summary, "highlights": highlights, "risks": [r for r in risks if r], "actions": actions}
