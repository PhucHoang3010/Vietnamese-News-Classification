"""Giám sát công bằng: tỷ lệ qua vòng theo giới tính (quy tắc 4/5) & nhận xét phỏng vấn bị gắn cờ."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import api
import ui

st.title("⚖️ Giám sát công bằng & chống thiên vị")
try:
    fair = api.get("/analytics/fairness")
    flagged = api.get("/analytics/flagged-feedback")
    guidelines = api.get("/ai/guidelines")["guidelines"]
except api.ApiError as exc:
    ui.show_error(exc)
    st.stop()

with st.expander("Nguyên tắc sử dụng AI có trách nhiệm trong hệ thống", expanded=False):
    for g in guidelines:
        st.markdown(f"- {g}")

st.markdown("### Tỷ lệ qua vòng theo giới tính")
st.caption("Dữ liệu giới tính chỉ dùng cho thống kê tổng hợp, không hiển thị cho quản lý tuyển dụng và không gửi cho AI. "
           + fair.get("rule", ""))
rows = []
for s in fair["stages"]:
    for g in ["Nam", "Nữ"]:
        v = s["groups"].get(g)
        if v:
            rows.append({"Vòng": s["stage_name"], "Giới tính": g, "Tỷ lệ qua %": v["pass_rate_pct"], "Số HS": v["n"]})
df = pd.DataFrame(rows)
left, right = st.columns([1.2, 1])
with left:
    fig = go.Figure()
    for i, g in enumerate(["Nam", "Nữ"]):
        part = df[df["Giới tính"] == g]
        fig.add_trace(go.Bar(x=part["Vòng"], y=part["Tỷ lệ qua %"], name=g, marker=dict(color=ui.SERIES[i], cornerradius=4),
                             text=[f"{v:g}%" for v in part["Tỷ lệ qua %"]], textposition="outside", cliponaxis=False,
                             hovertemplate=g + ": %{y}%<br>%{customdata} hồ sơ<extra></extra>", customdata=part["Số HS"]))
    fig.update_layout(barmode="group", bargroupgap=0.08)
    fig.update_yaxes(range=[0, 105], ticksuffix="%")
    st.plotly_chart(ui.style_fig(fig, 360, legend=True), width="stretch", config={"displayModeBar": False})
with right:
    table = pd.DataFrame([{
        "Vòng": s["stage_name"], "Tỷ lệ tác động": s["impact_ratio"],
        "Đánh giá": ("⚠️ Cần xem xét" if s["flag"] else ("ℹ️ Mẫu nhỏ" if s["small_sample"] else "✅ Đạt (≥ 0,8)"))
        if s["impact_ratio"] is not None else "–"} for s in fair["stages"]])
    st.dataframe(table, hide_index=True, width="stretch")
    if any(s["flag"] for s in fair["stages"]):
        ui.callout("⚠️ Có vòng có tỷ lệ tác động < 0,8. Đây là <b>tín hiệu cần rà soát</b> (tiêu chí chấm, người phỏng vấn, "
                   "câu hỏi), chưa phải kết luận có phân biệt đối xử – cần xem thêm cỡ mẫu và bối cảnh.")
    else:
        ui.callout("✅ Chưa phát hiện chênh lệch đáng kể giữa các nhóm.", "good")
ui.show_table(df)

st.markdown("### Nhận xét phỏng vấn bị bộ lọc thiên vị gắn cờ")
st.caption("Bộ lọc quét nhận xét của người phỏng vấn và của AI để phát hiện nội dung dựa trên giới tính, tuổi, hôn nhân/thai "
           "sản, vùng miền, tôn giáo, ngoại hình, sức khoẻ.")
if flagged:
    st.dataframe(pd.DataFrame([{"Mã HS": f["application_code"], "Vị trí": f["position"], "Vòng": f["stage"],
                                "Người PV": f["interviewer"], "Ngày": ui.fmt_dt(f["entered_at"]),
                                "Nhóm thuộc tính": ", ".join(f["categories"]), "Nhận xét": f["feedback"]}
                               for f in flagged]), hide_index=True, width="stretch")
else:
    st.success("Không có nhận xét nào bị gắn cờ.")
