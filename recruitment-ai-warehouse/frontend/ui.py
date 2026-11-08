"""Thành phần giao diện dùng chung: CSS, biểu đồ Plotly, hiển thị nhận xét AI."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from api import ApiError

# Bảng màu đã kiểm tra an toàn cho người mù màu (validate_palette.js – PASS)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
STATUS = {"good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b"}
GRID, AXIS, MUTED, INK, INK2, SURFACE = "#e1e0d9", "#c3c2b7", "#898781", "#0b0b0b", "#52514e", "#fcfcfb"
FONT = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'

STATUS_BADGE = {"active": ("Đang xử lý", "blue"), "hired": ("Đã nhận việc", "green"), "rejected": ("Bị loại", "red"),
                "withdrawn": ("Rút hồ sơ", "orange"), "on_hold": ("Tạm dừng", "gray"),
                "pending_review": ("Chờ duyệt", "orange"), "approved": ("Đã duyệt", "green"),
                "draft": ("Bản nháp", "gray")}
FIELD_LABELS = {"ho_ten": "Họ tên", "ngay_sinh": "Ngày sinh/tuổi", "gioi_tinh": "Giới tính", "hon_nhan": "Hôn nhân",
                "dia_chi": "Địa chỉ/quê quán", "ton_giao": "Tôn giáo", "dan_toc": "Dân tộc", "suc_khoe": "Sức khoẻ",
                "anh": "Ảnh", "lien_he": "Email/SĐT", "lien_ket": "Liên kết MXH"}

CSS = """
<style>
  .block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1400px;}
  [data-testid="stSidebar"] {background: #f3f4f1;}
  h1, h2, h3 {letter-spacing: -0.01em;}
  .tl-brand {font-weight: 700; font-size: 1.15rem; color: #0d366b; margin-bottom: .2rem;}
  .tl-sub {color: #52514e; font-size: .85rem;}
  .tl-callout {border-left: 4px solid #ec835a; background: #fff6f1; padding: .6rem .9rem; border-radius: 6px;
               margin-bottom: .5rem; font-size: .92rem;}
  .tl-callout.info {border-left-color: #2a78d6; background: #f0f6fd;}
  .tl-callout.good {border-left-color: #0ca30c; background: #f1faf1;}
  .tl-chip {display:inline-block; padding: 2px 9px; margin: 2px 4px 2px 0; border-radius: 999px; font-size: .8rem;
            background:#eef2f8; color:#184f95; border:1px solid #d5e2f5;}
  .tl-chip.miss {background:#fff4ef; color:#8a3a17; border-color:#f6d2c2;}
  .tl-chip.ok {background:#eef8ee; color:#006300; border-color:#cfe9cf;}
  .tl-muted {color:#898781; font-size:.82rem;}
  div[data-testid="stMetric"] {background: #ffffff; border: 1px solid rgba(11,11,11,.08); border-radius: 10px;
                               padding: .7rem .9rem;}
  div[data-testid="stMetricValue"] {font-size: 1.35rem;}
  div[data-testid="stMetricLabel"] p {font-size: .82rem;}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def user() -> dict:
    return st.session_state.get("user", {})


def can(permission: str) -> bool:
    return permission in user().get("permissions", [])


def show_error(exc: Exception) -> None:
    if isinstance(exc, ApiError):
        st.error(f"⚠️ {exc}")
    else:
        st.exception(exc)


def fmt_dt(value, with_time: bool = False) -> str:
    if not isinstance(value, str) or not value:  # None / NaN (pandas) → "–"
        return "–"
    dt = datetime.fromisoformat(value)
    return dt.strftime("%d/%m/%Y %H:%M" if with_time else "%d/%m/%Y")


def badge(status: str) -> str:
    label, color = STATUS_BADGE.get(status, (status, "gray"))
    return f":{color}-badge[{label}]"


def chips(items: list[str], kind: str = "") -> str:
    if not items:
        return "<span class='tl-muted'>–</span>"
    return "".join(f"<span class='tl-chip {kind}'>{i}</span>" for i in items)


def callout(text: str, kind: str = "") -> None:
    st.markdown(f"<div class='tl-callout {kind}'>{text}</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Biểu đồ
# --------------------------------------------------------------------------- #
def style_fig(fig: go.Figure, height: int = 340, legend: bool = False) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=16, t=30, b=8), paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font=dict(family=FONT, size=13, color=INK2), showlegend=legend, hoverlabel=dict(font_family=FONT),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None),
        bargap=0.35,
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=AXIS, zeroline=False, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, linecolor=AXIS, zeroline=False, tickfont=dict(color=INK2))
    return fig


def hbar(labels: list[str], values: list[float], value_suffix: str = "", height: int | None = None,
         colors: list[str] | None = None, hover: list[str] | None = None) -> go.Figure:
    """Cột ngang xếp hạng, một màu, nhãn giá trị ở cuối cột."""
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h", marker=dict(color=colors or SERIES[0], cornerradius=4),
        text=[f"{v:g}{value_suffix}" if v is not None else "" for v in values], textposition="outside",
        textfont=dict(color=INK2), cliponaxis=False,
        hovertext=hover, hovertemplate="%{y}: %{x}" + value_suffix + ("<br>%{hovertext}" if hover else "") +
                                        "<extra></extra>"))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    top = max([v for v in values if v is not None] or [1])
    fig.update_xaxes(showticklabels=False, showgrid=False, range=[0, top * 1.22])
    return style_fig(fig, height or max(220, 46 * len(labels) + 40))


def show_table(df: pd.DataFrame, label: str = "Xem bảng số liệu") -> None:
    with st.expander(label):
        st.dataframe(df, hide_index=True, width="stretch")


# --------------------------------------------------------------------------- #
# Hiển thị kết quả AI
# --------------------------------------------------------------------------- #
def render_insight(ins: dict) -> None:
    content = ins.get("content", {})
    kind = ins.get("insight_type")
    provider = "Claude (Anthropic)" if ins.get("provider") == "claude" else "Engine NLP nội bộ"
    meta_line = f"{provider} · {ins.get('model_name')} · tạo bởi {ins.get('created_by') or '–'} lúc {fmt_dt(ins.get('created_at'), True)}"
    if ins.get("reviewed_by"):
        meta_line += f" · kiểm duyệt: {ins['reviewed_by']}"
    st.markdown(f"{badge(ins.get('status'))} <span class='tl-muted'>{meta_line}</span>", unsafe_allow_html=True)
    if content.get("engine_note"):
        st.caption(f"ℹ️ {content['engine_note']} – đã dùng engine dự phòng.")
    if ins.get("bias_flags"):
        cats = sorted({f["category"] for f in ins["bias_flags"]})
        callout("⚠️ <b>Bộ lọc thiên vị gắn cờ:</b> " + ", ".join(cats) + ". Cần chỉnh sửa hoặc ghi chú trước khi duyệt.")
    if kind == "cv_analysis":
        _render_cv(content, ins.get("removed_fields", []))
    elif kind == "interview_questions":
        _render_questions(content)
    elif kind == "rejection_insights":
        _render_rejections(content)
    if ins.get("review_note"):
        st.caption(f"📝 Ghi chú kiểm duyệt: {ins['review_note']}")


def _render_cv(c: dict, removed: list[str]) -> None:
    st.markdown(f"#### {c.get('headline', '')}")
    st.write(c.get("summary", ""))
    jd = c.get("jd_match") or {}
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("**Điểm nổi bật (có bằng chứng trong CV)**")
        for h in c.get("highlights") or ["–"]:
            st.markdown(f"- {h}")
        st.markdown("**Điểm cần làm rõ khi phỏng vấn**")
        for g in c.get("gaps") or ["Không có"]:
            st.markdown(f"- {g}")
    with col2:
        cov = jd.get("required_coverage_pct")
        if cov is not None:
            st.markdown(f"**Độ phủ kỹ năng bắt buộc của JD: {cov}%**")
            st.progress(min(int(cov), 100) / 100)
            st.markdown("Đáp ứng: " + chips(jd.get("matched_required", []), "ok"), unsafe_allow_html=True)
            st.markdown("Chưa thấy trong CV: " + chips(jd.get("missing_required", []), "miss"), unsafe_allow_html=True)
            if jd.get("matched_nice_to_have"):
                st.markdown("Ưu tiên có: " + chips(jd["matched_nice_to_have"]), unsafe_allow_html=True)
        if c.get("content_similarity_pct") is not None:
            st.caption(f"Độ tương đồng nội dung CV–JD (TF-IDF cosine): {c['content_similarity_pct']}% – chỉ tham khảo.")
        st.caption("Độ phủ kỹ năng là chỉ số tham khảo, không phải điểm xếp hạng ứng viên.")
    groups = c.get("skill_groups") or []
    if groups:
        st.markdown("**Phân nhóm kỹ năng**")
        gcol1, gcol2 = st.columns([1, 1])
        with gcol1:
            g_sorted = sorted(groups, key=lambda g: len(g["skills"]), reverse=True)
            st.plotly_chart(hbar([g["group"] for g in g_sorted], [len(g["skills"]) for g in g_sorted], " kỹ năng",
                                 hover=[", ".join(g["skills"]) for g in g_sorted]), width="stretch",
                            config={"displayModeBar": False})
        with gcol2:
            for g in g_sorted:
                st.markdown(f"<b>{g['group']}</b><br>{chips(g['skills'])}", unsafe_allow_html=True)
    if removed:
        st.markdown("🛡️ Thông tin đã ẩn trước khi gửi AI: " + chips([FIELD_LABELS.get(r, r) for r in removed]),
                    unsafe_allow_html=True)
    if c.get("anonymized_preview"):
        with st.expander("Xem văn bản CV đã ẩn danh (dữ liệu AI nhận được)"):
            st.text(c["anonymized_preview"])


def _render_questions(c: dict) -> None:
    questions = c.get("questions", [])
    by_cat: dict[str, list] = {}
    for q in questions:
        by_cat.setdefault(q.get("category", "Khác"), []).append(q)
    n = 0
    for cat, items in by_cat.items():
        st.markdown(f"**{cat}**")
        for q in items:
            n += 1
            st.markdown(f"{n}. {q['question']}")
            st.caption(f"🎯 {q.get('purpose', '')} · ✅ Tín hiệu tốt: {q.get('good_answer_signals', '')} · "
                       f"Yêu cầu: {q.get('related_requirement', '')}")
    if c.get("scoring_guide"):
        st.info(c["scoring_guide"])
    if c.get("avoid_topics"):
        callout("🚫 <b>Không hỏi các chủ đề:</b> " + "; ".join(c["avoid_topics"]))


def _render_rejections(c: dict) -> None:
    st.write(c.get("overview", ""))
    reasons = c.get("top_reasons", [])
    if reasons:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.plotly_chart(hbar([r["label"] for r in reasons], [r["share_pct"] for r in reasons], "%",
                                 hover=[f"{r['count']} hồ sơ" for r in reasons]), width="stretch",
                            config={"displayModeBar": False})
        with col2:
            for r in reasons[:4]:
                st.markdown(f"**{r['label']}** – {r['count']} hồ sơ ({r['share_pct']}%), vòng: "
                            f"{', '.join(r.get('main_stages', []))}")
                if r.get("insight"):
                    st.caption(r["insight"])
                st.caption(f"💡 {r.get('recommendation', '')}")
        show_table(pd.DataFrame([{"Nhóm lý do": r["label"], "Số hồ sơ": r["count"], "Tỷ lệ %": r["share_pct"],
                                  "Vòng chính": ", ".join(r.get("main_stages", [])),
                                  "Ví dụ": " | ".join(r.get("examples", []))} for r in reasons]))
    if c.get("actions"):
        st.markdown("**Hành động đề xuất**")
        for a in c["actions"]:
            st.markdown(f"- {a}")
