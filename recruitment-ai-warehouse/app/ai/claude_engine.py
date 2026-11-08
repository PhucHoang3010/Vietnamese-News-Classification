"""Engine AI dùng Claude (Anthropic SDK) với structured outputs (JSON Schema).

Nguyên tắc chống thiên vị được đặt trong system prompt; dữ liệu gửi đi đã được ẩn danh.
Các chỉ số định lượng (độ phủ kỹ năng JD, thống kê lý do rớt) vẫn tính bằng code để đảm
bảo nhất quán – Claude chỉ viết phần tóm tắt, nhận định và gợi ý.
"""
from __future__ import annotations

import json

from app.ai.local_engine import AVOID_TOPICS, LocalEngine
from app.ai.skills import extract_skills, group_skills, match_jd

SYSTEM_PROMPT = """Bạn là trợ lý phân tích tuyển dụng (HR Analytics) cho một doanh nghiệp Việt Nam.
Nguyên tắc bắt buộc:
1. Chỉ dựa trên bằng chứng liên quan đến công việc có trong dữ liệu được cung cấp (kỹ năng, kinh nghiệm, dự án, học vấn).
2. Không suy đoán và không nhắc tới giới tính, tuổi, tình trạng hôn nhân/kế hoạch sinh con, quê quán/vùng miền,
   dân tộc, tôn giáo, ngoại hình, sức khoẻ. Dữ liệu cá nhân đã được ẩn và bạn không cố khôi phục.
3. Không đưa ra quyết định tuyển/loại và không xếp hạng hay chấm điểm con người; chỉ tóm tắt, chỉ ra điểm cần làm rõ
   và gợi ý câu hỏi. Quyết định cuối cùng thuộc về con người.
4. Khi thông tin không đủ, nói rõ là chưa có bằng chứng thay vì phỏng đoán.
5. Viết bằng tiếng Việt, ngắn gọn, chuyên nghiệp."""

FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}


def _obj(properties: dict) -> dict:
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


_STR = {"type": "string"}
_STR_LIST = {"type": "array", "items": {"type": "string"}}

CV_SCHEMA = _obj({
    "headline": _STR,
    "summary": _STR,
    "highlights": _STR_LIST,
    "skills": _STR_LIST,
    "gaps": _STR_LIST,
})

QUESTIONS_SCHEMA = _obj({
    "questions": {"type": "array", "items": _obj({
        "category": {"type": "string", "enum": ["Chuyên môn", "Làm rõ yêu cầu JD", "Làm rõ CV", "Tình huống",
                                                 "Hành vi (STAR)"]},
        "question": _STR,
        "purpose": _STR,
        "good_answer_signals": _STR,
        "related_requirement": _STR,
    })},
    "scoring_guide": _STR,
})

REJECTION_SCHEMA = _obj({
    "overview": _STR,
    "insights": {"type": "array", "items": _obj({"category": _STR, "insight": _STR, "recommendation": _STR})},
    "actions": _STR_LIST,
})

WEEKLY_SCHEMA = _obj({"summary": _STR, "highlights": _STR_LIST, "risks": _STR_LIST, "actions": _STR_LIST})


class AIRefusalError(RuntimeError):
    pass


class ClaudeEngine:
    provider = "claude"

    def __init__(self, api_key: str, model: str, effort: str = "medium", timeout: float = 90.0, client=None):
        if client is None:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key, timeout=timeout, max_retries=2)
        self.client = client
        self.model_name = model
        self.effort = effort
        self._local = LocalEngine()

    def _json_call(self, prompt: str, schema: dict) -> dict:
        kwargs: dict = {
            "model": self.model_name,
            "max_tokens": 16000,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
            "output_config": {"effort": self.effort, "format": {"type": "json_schema", "schema": schema}},
        }
        if self.model_name in FALLBACK_MODELS:
            # Nếu bộ lọc an toàn từ chối, API tự chạy lại trên mô hình dự phòng phù hợp
            kwargs["betas"] = ["server-side-fallback-2026-07-01"]
            kwargs["fallbacks"] = "default"
            response = self.client.beta.messages.create(**kwargs)
        else:
            response = self.client.messages.create(**kwargs)
        if response.stop_reason == "refusal":
            raise AIRefusalError("Mô hình từ chối xử lý yêu cầu")
        if response.stop_reason == "max_tokens":
            raise RuntimeError("Phản hồi AI bị cắt do vượt giới hạn token")
        text = next((b.text for b in response.content if b.type == "text"), None)
        if not text:
            raise RuntimeError("Phản hồi AI không có nội dung")
        return json.loads(text)

    # ------------------------------------------------------------------ CV
    def analyze_cv(self, cv_text: str, position: dict | None, context: dict | None = None) -> dict:
        base = self._local.analyze_cv(cv_text, position, context)  # chỉ số định lượng, nhất quán
        jd_block = ""
        if position:
            jd_block = (f"\n\nVị trí: {position.get('title')}\nYêu cầu bắt buộc: {', '.join(position.get('required_skills', []))}"
                        f"\nƯu tiên: {', '.join(position.get('nice_to_have_skills', []))}\nMô tả công việc: {position.get('jd_text')}")
        prompt = (
            "Hãy phân tích CV (đã ẩn danh) dưới đây.\n"
            "- headline: 1 dòng mô tả hồ sơ nghề nghiệp.\n- summary: 3–4 câu tóm tắt kinh nghiệm & năng lực chính.\n"
            "- highlights: tối đa 4 điểm nổi bật có bằng chứng trong CV.\n- skills: danh sách kỹ năng cứng/mềm xuất hiện.\n"
            "- gaps: các điểm cần làm rõ khi phỏng vấn so với yêu cầu vị trí (không phải lý do loại)."
            f"{jd_block}\n\n<cv>\n{cv_text[:60000]}\n</cv>"
        )
        result = self._json_call(prompt, CV_SCHEMA)
        skills = list(dict.fromkeys(base["skills"] + extract_skills(" ; ".join(result.get("skills", [])))))
        base.update({
            "headline": result["headline"],
            "summary": result["summary"],
            "highlights": result["highlights"],
            "gaps": result["gaps"],
            "skills": skills,
            "skill_groups": [{"group": g, "skills": s} for g, s in group_skills(skills).items()],
            "skills_mentioned_by_ai": result.get("skills", []),
            "jd_match": match_jd(skills, (position or {}).get("required_skills", []),
                                 (position or {}).get("nice_to_have_skills", [])),
            "evidence_note": "Tóm tắt do Claude sinh từ CV đã ẩn danh; độ phủ kỹ năng tính bằng từ điển kỹ năng.",
        })
        return base

    # ------------------------------------------------------- Câu hỏi PV
    def interview_questions(self, position: dict, analysis: dict | None) -> dict:
        analysis = analysis or {}
        prompt = (
            "Soạn 8–10 câu hỏi phỏng vấn có cấu trúc cho vị trí dưới đây, gắn với yêu cầu công việc và với các điểm cần "
            "làm rõ trong tóm tắt CV. Bao gồm câu chuyên môn, câu làm rõ yêu cầu JD còn thiếu, câu tình huống và câu "
            "hành vi theo STAR. Tuyệt đối không hỏi về chủ đề cá nhân bị cấm.\n\n"
            f"Vị trí: {position.get('title')}\nMô tả: {position.get('jd_text')}\n"
            f"Yêu cầu bắt buộc: {', '.join(position.get('required_skills', []))}\n\n"
            f"Tóm tắt CV: {analysis.get('summary', 'không có')}\n"
            f"Kỹ năng đáp ứng: {', '.join((analysis.get('jd_match') or {}).get('matched_required', []))}\n"
            f"Kỹ năng chưa thấy trong CV: {', '.join((analysis.get('jd_match') or {}).get('missing_required', []))}\n"
            f"Điểm cần làm rõ: {'; '.join(analysis.get('gaps', []))}"
        )
        result = self._json_call(prompt, QUESTIONS_SCHEMA)
        result["avoid_topics"] = AVOID_TOPICS
        return result

    # ------------------------------------------------- Lý do rớt phổ biến
    def rejection_insights(self, stats: dict) -> dict:
        base = self._local.rejection_insights(stats)
        prompt = (
            "Dưới đây là thống kê lý do ứng viên bị loại hoặc tự rút hồ sơ (đã phân nhóm). Hãy viết nhận định tổng quan, "
            "insight cho từng nhóm chính và đề xuất hành động cải thiện quy trình tuyển dụng. Không quy kết cho cá nhân.\n\n"
            + json.dumps({"total": stats.get("total"), "withdrawn": stats.get("withdrawn"),
                          "categories": base["top_reasons"]}, ensure_ascii=False)
        )
        result = self._json_call(prompt, REJECTION_SCHEMA)
        by_cat = {i["category"]: i for i in result.get("insights", [])}
        for item in base["top_reasons"]:
            ai_item = by_cat.get(item["category"]) or by_cat.get(item["label"])
            if ai_item:
                item["insight"] = ai_item["insight"]
                item["recommendation"] = ai_item["recommendation"] or item["recommendation"]
        base["overview"] = result["overview"]
        base["actions"] = result["actions"] or base["actions"]
        return base

    # ---------------------------------------------------- Báo cáo tuần
    def weekly_narrative(self, metrics: dict) -> dict:
        prompt = ("Viết báo cáo pipeline tuyển dụng tuần cho ban lãnh đạo dựa trên số liệu JSON sau: summary (2–3 câu), "
                  "highlights, risks (điểm nghẽn/rủi ro), actions (hành động tuần tới). Chỉ dùng số liệu được cung cấp.\n\n"
                  + json.dumps(metrics, ensure_ascii=False, default=str))
        return self._json_call(prompt, WEEKLY_SCHEMA)
