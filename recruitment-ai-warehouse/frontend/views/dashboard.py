"""Dashboard pipeline tuyển dụng: phễu, tỷ lệ chuyển đổi, thời gian xử lý, điểm nghẽn, nguồn."""
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import api
import ui

st.title("📈 Tổng quan pipeline tuyển dụng")
meta = api.meta()

# ---------------------------------------------------------------- Bộ lọc (một hàng phía trên biểu đồ)
c1, c2, c3, c4 = st.columns([1.4, 1, 1.4, 1])
with c1:
    period = st.date_input("Khoảng thời gian nộp hồ sơ", value=(date(2026, 8, 1), date.today()), format="DD/MM/YYYY")
depts = {d["name"]: d["id"] for d in meta["departments"]}
with c2:
    dept_name = st.selectbox("Phòng ban", ["Tất cả"] + list(depts), disabled=len(depts) <= 1)
positions = {p["title"]: p["id"] for p in meta["positions"]
             if dept_name == "Tất cả" or p["department_id"] == depts.get(dept_name)}
with c3:
    pos_name = st.selectbox("Vị trí", ["Tất cả"] + list(positions))
sources = {s["name"]: s["id"] for s in meta["sources"]}
with c4:
    src_name = st.selectbox("Nguồn", ["Tất cả"] + list(sources))

params = {}
if isinstance(period, (tuple, list)) and len(period) == 2:
    params["date_from"], params["date_to"] = period[0].isoformat(), period[1].isoformat()
if dept_name != "Tất cả":
    params["department_id"] = depts[dept_name]
if pos_name != "Tất cả":
    params["position_id"] = positions[pos_name]
if src_name != "Tất cả":
    params["source_id"] = sources[src_name]

try:
    with st.spinner("Đang tổng hợp dữ liệu từ kho…"):
        data = api.get("/analytics/dashboard", params=params)
except api.ApiError as exc:
    ui.show_error(exc)
    st.stop()

st.caption(f"Phạm vi dữ liệu: **{data['scope']}**" + ("" if ui.can("pii:read") else
           " · Thông tin cá nhân ứng viên đã được ẩn theo chính sách phân quyền"))
k = data["kpis"]
if not k.get("total_applications"):
    st.info("Chưa có hồ sơ trong phạm vi lọc.")
    st.stop()

trend = pd.DataFrame(data["trend"])
m = st.columns(7)
m[0].metric("Tổng hồ sơ", k["total_applications"], f"+{k['new_last_7_days']} / 7 ngày", delta_color="off")
m[1].metric("Ứng viên", k["unique_candidates"], help="Sau khi khử trùng giữa các nguồn")
m[2].metric("Đang xử lý", k["active"])
m[3].metric("Đã nhận việc", k["hired"])
m[4].metric("Tỷ lệ tuyển", f"{k['hire_rate_pct']}%", help="Số nhận việc / tổng hồ sơ")
m[5].metric("TG tuyển TB", f"{k['avg_time_to_hire_days'] or '–'} ngày",
            help=f"Trung vị {k['median_time_to_hire_days'] or '–'} ngày (từ nộp hồ sơ đến nhận việc)")
m[6].metric("Tỷ lệ nhận offer", f"{k['offer_acceptance_pct'] or '–'}%")

# ---------------------------------------------------------------- Điểm nghẽn
if data["bottlenecks"]:
    st.markdown("#### 🚧 Điểm nghẽn phát hiện tự động")
    cols = st.columns(len(data["bottlenecks"]))
    for col, b in zip(cols, data["bottlenecks"]):
        with col:
            ui.callout(("🔴 " if b["severity"] == "high" else "🟠 ") + b["message"])

# ---------------------------------------------------------------- Phễu + tỷ lệ qua vòng
st.markdown("### Phễu tuyển dụng")
fn = pd.DataFrame(data["funnel"])
left, right = st.columns([1, 1.1])
with left:
    fig = go.Figure(go.Funnel(
        y=fn.stage_name, x=fn.reached, textinfo="value+percent initial", textposition="inside",
        textfont=dict(color="#ffffff"), marker=dict(color=ui.SERIES[0]),
        connector=dict(fillcolor="#e8eef7", line=dict(width=0)),
        hovertemplate="%{y}: %{x} hồ sơ<br>%{percentInitial:.1%} so với số nộp<br>%{percentPrevious:.1%} so với vòng trước"
                      "<extra></extra>"))
    st.plotly_chart(ui.style_fig(fig, 380), width="stretch", config={"displayModeBar": False})
with right:
    st.markdown("**Tỷ lệ qua từng vòng** (trên số hồ sơ đã có kết quả)")
    table = fn[fn.stage != "HIRED"][["stage_name", "reached", "pass_rate_pct", "failed", "withdrawn", "in_progress"]]
    st.dataframe(table, hide_index=True, width="stretch", column_config={
        "stage_name": "Vòng", "reached": st.column_config.NumberColumn("Đến vòng"),
        "pass_rate_pct": st.column_config.ProgressColumn("Tỷ lệ qua vòng", format="%.1f%%", min_value=0, max_value=100),
        "failed": "Bị loại", "withdrawn": "Rút", "in_progress": "Đang chờ"})
    worst = fn.dropna(subset=["pass_rate_pct"]).query("reached >= 10").sort_values("pass_rate_pct").head(1)
    if not worst.empty:
        st.caption(f"Vòng có tỷ lệ qua thấp nhất: **{worst.iloc[0].stage_name}** ({worst.iloc[0].pass_rate_pct}%).")

# ---------------------------------------------------------------- Thời gian xử lý
st.markdown("### Thời gian chuyển vòng (trung vị, ngày)")
dur = pd.DataFrame(data["stage_durations"]).dropna(subset=["median_days"])
left, right = st.columns([1.15, 1])
with left:
    over = dur.median_days > dur.sla_days
    colors = [ui.STATUS["serious"] if o else ui.SERIES[0] for o in over]
    fig = ui.hbar(dur.transition.tolist(), dur.median_days.tolist(), " ngày", colors=colors,
                  hover=[f"TB {a} ngày · P90 {p} ngày · SLA {s} ngày · {o}% vượt SLA" for a, p, s, o in
                         zip(dur.avg_days, dur.p90_days, dur.sla_days, dur.over_sla_pct)])
    fig.add_trace(go.Scatter(x=dur.sla_days, y=dur.transition, mode="markers", name="SLA",
                             marker=dict(symbol="line-ns", size=22, line=dict(width=2, color=ui.INK)),
                             hovertemplate="SLA: %{x} ngày<extra></extra>"))
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.caption("Vạch đen = SLA của vòng. Cột màu cam ⚠ = trung vị vượt SLA.")
with right:
    st.dataframe(dur[["transition", "n", "avg_days", "median_days", "p90_days", "sla_days", "over_sla_pct"]],
                 hide_index=True, width="stretch", column_config={
                     "transition": "Chuyển vòng", "n": "Số HS", "avg_days": "TB (ngày)", "median_days": "Trung vị",
                     "p90_days": "P90", "sla_days": "SLA",
                     "over_sla_pct": st.column_config.NumberColumn("% vượt SLA", format="%.1f%%")})

# ---------------------------------------------------------------- Xu hướng theo tuần
st.markdown("### Xu hướng theo tuần")
if not trend.empty:
    fig = go.Figure()
    for i, (col, name) in enumerate([("applications", "Hồ sơ mới"), ("interviews", "Lượt phỏng vấn"),
                                     ("hires", "Nhận việc")]):
        fig.add_trace(go.Scatter(x=trend.week_start, y=trend[col], name=name, mode="lines+markers",
                                 line=dict(width=2, color=ui.SERIES[i]), marker=dict(size=8),
                                 hovertemplate=f"{name}: %{{y}}<extra></extra>"))
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(tickformat="%d/%m", title=None)
    st.plotly_chart(ui.style_fig(fig, 320, legend=True), width="stretch", config={"displayModeBar": False})
    ui.show_table(trend.rename(columns={"week_start": "Tuần bắt đầu", "applications": "Hồ sơ mới",
                                        "interviews": "Phỏng vấn", "hires": "Nhận việc", "rejected": "Bị loại",
                                        "withdrawn": "Rút hồ sơ"}))

# ---------------------------------------------------------------- Hiệu quả nguồn
st.markdown("### Hiệu quả nguồn tuyển dụng")
src = pd.DataFrame(data["sources"])
left, right = st.columns(2)
with left:
    st.markdown("**Số hồ sơ theo nguồn**")
    st.plotly_chart(ui.hbar(src.source.tolist(), src.applications.tolist()), width="stretch",
                    config={"displayModeBar": False})
with right:
    st.markdown("**Tỷ lệ tuyển được theo nguồn (%)**")
    s2 = src.sort_values("hire_rate_pct", ascending=False)
    st.plotly_chart(ui.hbar(s2.source.tolist(), s2.hire_rate_pct.fillna(0).tolist(), "%",
                            hover=[f"{h} nhận việc / {a} hồ sơ" for h, a in zip(s2.hires, s2.applications)]),
                    width="stretch", config={"displayModeBar": False})
ui.show_table(src.drop(columns=["source_code"]).rename(columns={
    "source": "Nguồn", "applications": "Hồ sơ", "passed_screening_pct": "% qua sàng lọc",
    "reached_tech_pct": "% đến PV chuyên môn", "offers": "Offer", "hires": "Nhận việc", "hire_rate_pct": "% tuyển",
    "avg_time_to_hire_days": "TG tuyển TB (ngày)"}), "Xem bảng hiệu quả nguồn")

# ---------------------------------------------------------------- Lý do rớt
st.markdown("### Lý do loại / rút hồ sơ")
cats = data["rejections"]["categories"]
if cats:
    left, right = st.columns([1.2, 1])
    with left:
        st.plotly_chart(ui.hbar([c["label"] for c in cats], [c["share_pct"] for c in cats], "%",
                                hover=[f"{c['count']} hồ sơ · vòng {', '.join(c['main_stages'])}" for c in cats]),
                        width="stretch", config={"displayModeBar": False})
    with right:
        st.dataframe(pd.DataFrame([{"Nhóm lý do": c["label"], "Số HS": c["count"], "Rút": c["withdrawn"],
                                    "Vòng chính": ", ".join(c["main_stages"])} for c in cats]),
                     hide_index=True, width="stretch")
        st.caption(f"Phân loại tự động (NLP) {data['rejections']['total']} hồ sơ bị loại/rút hồ sơ. "
                   "Xem nhận định chi tiết ở trang AI phân tích CV → Lý do rớt phổ biến.")

# ---------------------------------------------------------------- Vị trí
st.markdown("### Pipeline theo vị trí")
pos = pd.DataFrame(data["positions"])
if not pos.empty:
    pos["Đang xử lý theo vòng"] = pos.active_by_stage.apply(lambda d: ", ".join(f"{k}: {v}" for k, v in d.items()))
    pos["fill"] = (pos.hired / pos.headcount * 100).clip(upper=100)
    st.dataframe(pos[["position", "department", "applications", "active", "hired", "headcount", "fill",
                      "Đang xử lý theo vòng"]], hide_index=True, width="stretch", column_config={
                     "position": "Vị trí", "department": "Phòng ban", "applications": "Hồ sơ",
                     "active": "Đang xử lý", "hired": "Đã tuyển", "headcount": "Chỉ tiêu",
                     "fill": st.column_config.ProgressColumn("% chỉ tiêu", format="%.0f%%", min_value=0,
                                                             max_value=100)})

if data["stuck"]:
    with st.expander(f"⏰ {len(data['stuck'])} hồ sơ đang quá hạn SLA ở vòng hiện tại"):
        st.dataframe(pd.DataFrame(data["stuck"])[["application_code", "position", "stage_name", "days_in_stage",
                                                  "sla_days"]], hide_index=True, width="stretch",
                     column_config={"application_code": "Mã hồ sơ", "position": "Vị trí", "stage_name": "Vòng",
                                    "days_in_stage": "Số ngày ở vòng", "sla_days": "SLA"})
