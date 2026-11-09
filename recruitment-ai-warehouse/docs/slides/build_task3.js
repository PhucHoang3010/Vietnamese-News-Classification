// Bộ slide Task 3 – Dashboard phân tích pipeline tuyển dụng (Trần Phúc Hoàng)
// Phong cách: báo cáo phân tích nền sáng, mực xanh đậm + điểm nhấn hổ phách, biểu đồ gốc PowerPoint.
// Chạy: NODE_PATH=<node_modules> node build_task3.js
const path = require("path");
const pptxgen = require("pptxgenjs");
const { fitImage, ASSETS } = require("./common");

const APPLY_THEME = process.env.APPLY_THEME_JS;
const OUT = path.join(__dirname, "Slide_Task3_Dashboard_TranPhucHoang.pptx");

const THEME = {
  name: "TalentLens Analytics",
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  colors: {
    dk1: "14213D", lt1: "FFFFFF", dk2: "33415C", lt2: "F1F4F8",
    accent1: "FCA311", accent2: "2A9D8F", accent3: "8D99AE", accent4: "E76F51",
    accent5: "457B9D", accent6: "A8DADC", hlink: "457B9D", folHlink: "8D99AE",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333" × 7.5"
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Task 3 – Dashboard phân tích pipeline tuyển dụng";
pres.author = "Trần Phúc Hoàng";
pres.company = "Nhóm 8 – Học viện Hàng không Việt Nam";
const C = pres.SchemeColor;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "A_TITLE",
  background: { color: HEX.dk1 },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 0.75, y: 1.35, w: 7.6, h: 0.45, fontSize: 13, bold: true, color: C.accent1, charSpacing: 2, align: "left" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.75, y: 1.85, w: 7.6, h: 2.1, fontSize: 42, bold: true, color: C.background1, valign: "top", align: "left" }, text: "" } },
    { placeholder: { options: { name: "subtitle", type: "body", x: 0.75, y: 4.05, w: 7.6, h: 0.95, fontSize: 18, color: C.background2, valign: "top", align: "left" }, text: "" } },
    { placeholder: { options: { name: "presenter", type: "body", x: 0.75, y: 5.55, w: 7.6, h: 0.9, fontSize: 15, color: C.background1, valign: "top", align: "left" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "A_CONTENT",
  background: { color: HEX.lt1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.38, w: 12.1, h: 0.85, fontSize: 32, bold: true, color: C.text1, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Nhóm 8 · Task 3 – Dashboard pipeline tuyển dụng · Trần Phúc Hoàng", options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: C.accent3, margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.55, h: 0.3, fontSize: 10, color: HEX.accent3, align: "right" },
});
pres.defineSlideMaster({
  title: "A_CLOSING",
  background: { color: HEX.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.38, w: 12.1, h: 0.85, fontSize: 32, bold: true, color: C.background1, valign: "middle", align: "left", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.55, h: 0.3, fontSize: 10, color: HEX.accent3, align: "right" },
});

const card = (slide, x, y, w, h, name, fill = C.background2) =>
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { color: fill, width: 0 }, objectName: name });
const badge = (slide, x, y, label, name, fill = C.accent1, color = C.text1) => {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 0.62, h: 0.62, rectRadius: 0.1, fill: { color: fill }, line: { color: fill, width: 0 }, objectName: name });
  slide.addText(label, { x, y, w: 0.62, h: 0.62, fontSize: 16, bold: true, color, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `${name}-text` });
};
const chartText = { catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt", titleFontFace: "+mn-lt" };

const FUNNEL = [["Nộp hồ sơ", 329], ["Sàng lọc CV", 321], ["PV HR", 176], ["PV chuyên môn", 96], ["PV cuối", 44], ["Offer", 37], ["Nhận việc", 24]];

async function build() {
  // ================================================================ 1. Tiêu đề
  pres.addSection({ title: "Mở đầu" });
  let s = pres.addSlide({ masterName: "A_TITLE", sectionTitle: "Mở đầu" });
  s.addText("NHÓM 8 · ĐỀ TÀI AI 9 · LẬP TRÌNH PYTHON", { placeholder: "kicker" });
  s.addText("Dashboard phân tích pipeline tuyển dụng", { placeholder: "title" });
  s.addText("Task 3 – Tỷ lệ chuyển đổi, thời gian xử lý và điểm nghẽn từng vòng", { placeholder: "subtitle" });
  s.addText([{ text: "Trần Phúc Hoàng", options: { bold: true, breakLine: true } }, { text: "MSSV 2431540018 · Lớp 24ĐHTT01" }], { placeholder: "presenter" });
  // phễu cách điệu bằng hình khối
  const cx = 10.75, maxW = 3.5, top = 1.45, barH = 0.5, gap = 0.14;
  FUNNEL.forEach(([label, n], i) => {
    const w = 0.75 + (maxW - 0.75) * (n / 329);
    const y = top + i * (barH + gap);
    const fill = label === "PV chuyên môn" ? C.accent1 : C.accent2;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx - w / 2, y, w, h: barH, rectRadius: 0.08, fill: { color: fill }, line: { color: fill, width: 0 }, objectName: `funnel-bar-${i}` });
    s.addText(String(n), { x: cx - w / 2, y, w, h: barH, fontSize: 14, bold: true, color: label === "PV chuyên môn" ? C.text1 : C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `funnel-n-${i}` });
  });
  s.addText("Phễu 7 vòng · 329 hồ sơ → 24 người nhận việc", { x: 8.9, y: 6.0, w: 3.7, h: 0.4, fontSize: 12, color: C.background2, align: "center", margin: 0, isTextBox: true, objectName: "funnel-caption" });
  s.addNotes("Xin chào thầy/cô và các bạn. Em là Trần Phúc Hoàng, phụ trách Task 3 – xây dựng dashboard phân tích pipeline tuyển dụng trong hệ thống TalentLens của nhóm 8. Phần trình bày gồm: bài toán, mô hình pipeline, công thức chỉ số, cách code, demo phễu tuyển dụng, thời gian xử lý, phát hiện điểm nghẽn và giao diện thực tế.");

  // ================================================================ 2. Bài toán
  pres.addSection({ title: "Bài toán" });
  s = pres.addSlide({ masterName: "A_CONTENT", sectionTitle: "Bài toán" });
  s.addText("HR cần trả lời 4 câu hỏi về pipeline", { placeholder: "title" });
  const Q = [
    ["01", "Bao nhiêu hồ sơ đi tiếp qua mỗi vòng?", "Tỷ lệ chuyển đổi và tỷ lệ qua vòng – vẽ thành phễu tuyển dụng"],
    ["02", "Mỗi vòng mất bao lâu?", "Thời gian chuyển vòng (trung vị, P90) so với SLA của vòng"],
    ["03", "Pipeline đang kẹt ở đâu?", "Điểm nghẽn tự động theo 4 quy tắc: chuyển đổi, thời gian, tồn đọng, rút hồ sơ"],
    ["04", "Nguồn tuyển nào hiệu quả?", "Số hồ sơ, tỷ lệ qua sàng lọc và tỷ lệ tuyển theo từng nguồn"],
  ];
  Q.forEach(([no, q, a], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.55 + Math.floor(i / 2) * 2.45;
    card(s, x, y, 5.95, 2.25, `q-card-${i}`);
    badge(s, x + 0.35, y + 0.35, no, `q-badge-${i}`);
    s.addText(q, { x: x + 1.2, y: y + 0.3, w: 4.5, h: 0.75, fontSize: 19, bold: true, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: `q-title-${i}` });
    s.addText(a, { x: x + 1.2, y: y + 1.1, w: 4.5, h: 0.9, fontSize: 15, color: C.text2, valign: "top", margin: 0, isTextBox: true, objectName: `q-answer-${i}` });
  });
  s.addText("Dữ liệu dùng chung: kho PostgreSQL – fact_application (329 hồ sơ) và fact_stage_event (1.027 sự kiện qua các vòng)", { x: 0.6, y: 6.5, w: 12.1, h: 0.35, fontSize: 12, italic: true, color: C.accent3, margin: 0, isTextBox: true, objectName: "data-note" });
  s.addNotes("Bộ phận nhân sự thường không trả lời được bốn câu hỏi cơ bản vì dữ liệu rời rạc. Dashboard của em trả lời từng câu bằng một nhóm chỉ số: phễu và tỷ lệ chuyển đổi, thời gian chuyển vòng so với SLA, điểm nghẽn tự động và hiệu quả nguồn. Tất cả đều tính trên kho dữ liệu chung đã được Task 1 và Task 2 làm sạch, khử trùng.");

  // ================================================================ 3. Pipeline 7 vòng
  pres.addSection({ title: "Thiết kế" });
  s = pres.addSlide({ masterName: "A_CONTENT", sectionTitle: "Thiết kế" });
  s.addText("Pipeline 7 vòng và SLA của từng vòng", { placeholder: "title" });
  const STAGES = [["Nộp hồ sơ", "2"], ["Sàng lọc CV", "3"], ["PV HR", "4"], ["PV chuyên môn", "4"], ["PV cuối", "3"], ["Offer", "5"], ["Nhận việc", "–"]];
  STAGES.forEach(([name, sla], i) => {
    const x = 0.6 + i * 1.72;
    s.addShape(i === 0 ? pres.shapes.PENTAGON : pres.shapes.CHEVRON, { x, y: 1.7, w: 1.85, h: 1.0, fill: { color: C.text1 }, line: { color: C.background1, width: 1.5 }, objectName: `stage-${i}` });
    s.addText(name, { x: x + (i === 0 ? 0.1 : 0.32), y: 1.7, w: 1.3, h: 1.0, fontSize: 13, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `stage-name-${i}` });
    s.addText(sla === "–" ? "Kết thúc" : `SLA ${sla} ngày`, { x: x + 0.15, y: 2.85, w: 1.5, h: 0.35, fontSize: 13, color: C.text2, align: "center", margin: 0, isTextBox: true, objectName: `stage-sla-${i}` });
  });
  card(s, 0.6, 3.65, 6.6, 3.05, "event-card");
  s.addText("Mô hình sự kiện trong kho dữ liệu", { x: 0.95, y: 3.85, w: 6, h: 0.45, fontSize: 18, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "event-title" });
  s.addText([
    { text: "Mỗi lần hồ sơ đi vào một vòng = 1 dòng fact_stage_event", options: { bullet: true, breakLine: true } },
    { text: "entered_at, exited_at → thời lượng vòng (giờ)", options: { bullet: true, breakLine: true } },
    { text: "outcome: passed · failed · no_show · withdrawn · pending", options: { bullet: true, breakLine: true } },
    { text: "dim_stage lưu thứ tự vòng và SLA (số ngày cam kết)", options: { bullet: true } },
  ], { x: 0.95, y: 4.4, w: 6.0, h: 2.1, fontSize: 15, color: C.text2, paraSpaceAfter: 6, valign: "top", margin: 0, isTextBox: true, objectName: "event-list" });
  card(s, 7.5, 3.65, 5.2, 3.05, "outcome-card");
  s.addText("3 kết cục ở mỗi vòng", { x: 7.85, y: 3.85, w: 4.6, h: 0.45, fontSize: 18, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "outcome-title" });
  [["Đạt → chuyển sang vòng kế tiếp", C.accent2], ["Không đạt / vắng mặt → đóng hồ sơ", C.accent4], ["Ứng viên tự rút → đóng hồ sơ", C.accent1]].forEach(([t, col], i) => {
    const y = 4.55 + i * 0.65;
    s.addShape(pres.shapes.OVAL, { x: 7.9, y: y + 0.08, w: 0.28, h: 0.28, fill: { color: col }, line: { color: col, width: 0 }, objectName: `outcome-dot-${i}` });
    s.addText(t, { x: 8.35, y, w: 4.2, h: 0.45, fontSize: 15, color: C.text2, valign: "middle", margin: 0, isTextBox: true, objectName: `outcome-text-${i}` });
  });
  s.addNotes("Quy trình gồm 7 vòng, mỗi vòng có một SLA – số ngày xử lý cam kết, lưu trong bảng dim_stage. Điểm quan trọng của thiết kế là mô hình sự kiện: mỗi lần hồ sơ đi vào một vòng sinh ra một dòng trong fact_stage_event với thời điểm vào, ra và kết quả. Nhờ vậy mọi chỉ số về chuyển đổi và thời gian đều tính trực tiếp từ bảng này.");

  // ================================================================ 4. Công thức
  s = pres.addSlide({ masterName: "A_CONTENT", sectionTitle: "Thiết kế" });
  s.addText("Định nghĩa các chỉ số", { placeholder: "title" });
  const F = [
    ["Tỷ lệ chuyển đổi", "N(i+1) / N(i) × 100%", "N(i) = số hồ sơ đã đi tới vòng i. Cho biết bao nhiêu phần trăm hồ sơ đi tiếp so với vòng trước."],
    ["Tỷ lệ qua vòng", "N(i+1) / (N(i+1) + loại + rút)", "Chỉ tính hồ sơ đã có kết quả ở vòng i, không bị hồ sơ đang chờ làm sai lệch."],
    ["Thời gian chuyển vòng", "vào vòng i+1 − vào vòng i", "Chỉ tính hồ sơ đi tiếp. Tóm tắt bằng trung vị và P90, so sánh với SLA."],
  ];
  F.forEach(([h, f, d], i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 1.55, 3.9, 3.75, `f-card-${i}`);
    badge(s, x + 0.3, 1.8, String(i + 1), `f-badge-${i}`);
    s.addText(h, { x: x + 1.05, y: 1.8, w: 2.7, h: 0.62, fontSize: 18, bold: true, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: `f-title-${i}` });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.3, y: 2.65, w: 3.3, h: 0.85, rectRadius: 0.08, fill: { color: C.background1 }, line: { color: C.accent3, width: 0.75 }, objectName: `f-formula-box-${i}` });
    s.addText(f, { x: x + 0.3, y: 2.65, w: 3.3, h: 0.85, fontSize: 15, italic: true, bold: true, color: C.text1, align: "center", valign: "middle", margin: 0.05, isTextBox: true, objectName: `f-formula-${i}` });
    s.addText(d, { x: x + 0.3, y: 3.7, w: 3.3, h: 1.45, fontSize: 14, color: C.text2, valign: "top", margin: 0, isTextBox: true, objectName: `f-desc-${i}` });
  });
  const extra = [["Trung vị thay vì trung bình", "phân phối thời gian lệch phải – vài hồ sơ bị bỏ quên kéo trung bình lên"],
    ["Time-to-hire", "từ lúc nộp hồ sơ đến khi nhận việc: trung bình 24,5 ngày"],
    ["Tỷ lệ nhận offer", "số nhận việc / số offer đã có kết quả: 66,7%"]];
  extra.forEach(([h, d], i) => {
    s.addText([{ text: h, options: { bold: true, color: C.text1, breakLine: true } }, { text: d, options: { color: C.text2 } }],
      { x: 0.6 + i * 4.1, y: 5.55, w: 3.9, h: 1.1, fontSize: 14, valign: "top", margin: 0, isTextBox: true, objectName: `extra-${i}` });
  });
  s.addNotes("Em định nghĩa thống nhất ba chỉ số chính. Tỷ lệ chuyển đổi so số hồ sơ vòng sau với vòng trước. Tỷ lệ qua vòng chỉ tính trên hồ sơ đã có kết quả nên không bị hồ sơ đang chờ làm sai lệch. Thời gian chuyển vòng chỉ tính các hồ sơ thực sự đi tiếp và dùng trung vị vì dữ liệu thời gian thường lệch phải.");

  // ================================================================ 5. Kiến trúc code
  pres.addSection({ title: "Hiện thực" });
  s = pres.addSlide({ masterName: "A_CONTENT", sectionTitle: "Hiện thực" });
  s.addText("Từ kho dữ liệu đến biểu đồ", { placeholder: "title" });
  const FLOW = [["PostgreSQL", "dim_* và fact_* lược đồ hình sao"], ["analytics.py", "SQLAlchemy → pandas, lọc theo quyền"], ["FastAPI", "GET /api/analytics/dashboard"], ["Streamlit + Plotly", "phễu, cột, đường, bảng số liệu"]];
  FLOW.forEach(([t, d], i) => {
    const x = 0.6 + i * 3.17;
    card(s, x, 1.5, 2.6, 1.35, `flow-${i}`, i === 1 ? C.text1 : C.background2);
    s.addText([{ text: t, options: { bold: true, fontSize: 17, breakLine: true } }, { text: d, options: { fontSize: 13 } }],
      { x: x + 0.15, y: 1.5, w: 2.3, h: 1.35, color: i === 1 ? C.background1 : C.text1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `flow-text-${i}` });
    if (i < 3) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 2.68, y: 1.98, w: 0.42, h: 0.4, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0 }, objectName: `flow-arrow-${i}` });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 3.2, w: 6.55, h: 3.5, rectRadius: 0.1, fill: { color: C.text1 }, line: { color: C.text1, width: 0 }, objectName: "code-box" });
  const code = [
    "def funnel(apps, events):",
    "    rows, prev = [], None",
    "    for code in PIPELINE:          # 7 vòng",
    "        ev = events[events.stage == code]",
    "        reached = ev.application_id.nunique()",
    "        rows.append({",
    "            \"stage\": code, \"reached\": reached,",
    "            \"conversion_from_prev_pct\":",
    "                pct(reached, prev),",
    "            \"failed\": ev.outcome.isin(FAIL).sum()})",
    "        prev = reached",
    "    return rows",
  ];
  s.addText(code.map((line, i) => ({ text: line, options: { breakLine: i < code.length - 1, color: line.trim().startsWith("def") ? C.accent1 : C.background1 } })),
    { x: 0.85, y: 3.35, w: 6.1, h: 3.2, fontFace: "Courier New", fontSize: 12, valign: "top", margin: 0, isTextBox: true, objectName: "code-text" });
  const FN = [["kpis()", "tổng hồ sơ, nhận việc, tỷ lệ tuyển, time-to-hire"], ["funnel()", "số hồ sơ tới từng vòng, tỷ lệ chuyển đổi, qua vòng"], ["stage_durations()", "trung vị, P90, % vượt SLA mỗi bước"], ["bottlenecks()", "4 quy tắc phát hiện điểm nghẽn"], ["source_performance()", "hiệu quả từng nguồn tuyển"], ["weekly_trend()", "hồ sơ, phỏng vấn, nhận việc theo tuần"]];
  const fnRuns = [];
  FN.forEach(([f, d], i) => {
    fnRuns.push({ text: `${f}  `, options: { bold: true, color: C.text1, fontFace: "Courier New" } });
    fnRuns.push({ text: d, options: { color: C.text2, breakLine: i < FN.length - 1 } });
  });
  s.addText(fnRuns, { x: 7.5, y: 3.25, w: 5.2, h: 3.45, fontSize: 14, paraSpaceAfter: 8, valign: "top", margin: 0, isTextBox: true, objectName: "fn-list" });
  s.addNotes("Về hiện thực: module analytics.py nạp hồ sơ và sự kiện từ PostgreSQL bằng SQLAlchemy, đưa vào DataFrame của pandas, áp dụng bộ lọc và phạm vi theo quyền người dùng. Sáu hàm chính tính các nhóm chỉ số. FastAPI trả toàn bộ kết quả qua một endpoint JSON và giao diện Streamlit vẽ bằng Plotly. Bên trái là hàm funnel: duyệt 7 vòng theo thứ tự, đếm số hồ sơ duy nhất tới mỗi vòng và tính tỷ lệ so với vòng trước.");

  // ================================================================ 6. Demo phễu
  pres.addSection({ title: "Kết quả" });
  s = pres.addSlide({ masterName: "A_CONTENT", sectionTitle: "Kết quả" });
  s.addText("Demo: phễu tuyển dụng trên dữ liệu mẫu", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [{ name: "Số hồ sơ", labels: FUNNEL.map((f) => f[0]), values: FUNNEL.map((f) => f[1]) }], {
    x: 0.6, y: 1.45, w: 7.7, h: 5.35, barDir: "bar", catAxisOrientation: "maxMin", barGapWidthPct: 45,
    chartColors: FUNNEL.map((f) => (f[0] === "PV chuyên môn" ? HEX.accent1 : HEX.dk1)),
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: HEX.dk2, dataLabelFontSize: 14, dataLabelFontBold: true,
    valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    catAxisLabelColor: HEX.dk2, catAxisLabelFontSize: 14, catAxisLineShow: false, showLegend: false,
    showTitle: true, title: "Số hồ sơ đi tới từng vòng", titleColor: HEX.dk1, titleFontSize: 15, ...chartText,
    objectName: "funnel-chart",
  });
  [["7,3%", "tỷ lệ tuyển: 24 / 329 hồ sơ", C.text1], ["47,3%", "tỷ lệ qua PV chuyên môn – thấp nhất", C.accent1], ["66,7%", "tỷ lệ nhận offer", C.text1]].forEach(([n, l, col], i) => {
    const y = 1.6 + i * 1.65;
    s.addText(n, { x: 8.75, y, w: 4.0, h: 0.95, fontSize: 48, bold: true, color: col, margin: 0, isTextBox: true, objectName: `stat-n-${i}` });
    s.addText(l, { x: 8.75, y: y + 0.95, w: 4.0, h: 0.45, fontSize: 15, color: C.text2, margin: 0, isTextBox: true, objectName: `stat-l-${i}` });
  });
  s.addText("Tỷ lệ qua vòng = đi tiếp / (đi tiếp + bị loại + rút)", { x: 8.75, y: 6.45, w: 4.0, h: 0.35, fontSize: 11, italic: true, color: C.accent3, margin: 0, isTextBox: true, objectName: "stat-note" });
  s.addNotes("Đây là demo chính của Task 3 – phễu tuyển dụng. Từ 329 hồ sơ, 176 hồ sơ qua sàng lọc, 96 hồ sơ tới phỏng vấn chuyên môn và cuối cùng 24 người nhận việc, tức tỷ lệ tuyển 7,3%. Thanh màu cam là vòng phỏng vấn chuyên môn – nơi tỷ lệ qua vòng thấp nhất, chỉ 47,3%. Tỷ lệ nhận offer là 66,7%.");

  // ================================================================ 7. Thời gian vs SLA
  s = pres.addSlide({ masterName: "A_CONTENT", sectionTitle: "Kết quả" });
  s.addText("Thời gian chuyển vòng so với SLA", { placeholder: "title" });
  const TR = ["Nộp → Sàng lọc", "Sàng lọc → PV HR", "PV HR → PV CM", "PV CM → PV cuối", "PV cuối → Offer", "Offer → Nhận việc"];
  s.addChart(pres.charts.BAR, [
    { name: "Trung vị thực tế (ngày)", labels: TR, values: [1.9, 2.3, 7.0, 4.0, 2.2, 5.0] },
    { name: "SLA (ngày)", labels: TR, values: [2, 3, 4, 4, 3, 5] },
  ], {
    x: 0.6, y: 1.45, w: 8.0, h: 5.35, barDir: "col", barGrouping: "clustered", barGapWidthPct: 60,
    chartColors: [HEX.accent1, HEX.accent3], showValue: true, dataLabelPosition: "outEnd", dataLabelColor: HEX.dk2,
    dataLabelFontSize: 12, dataLabelFormatCode: "0.0", valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    catAxisLabelColor: HEX.dk2, catAxisLabelFontSize: 12, showLegend: true, legendPos: "t", legendFontSize: 13, legendColor: HEX.dk2,
    ...chartText, objectName: "duration-chart",
  });
  s.addText("7,0 ngày", { x: 8.95, y: 1.6, w: 3.8, h: 0.95, fontSize: 48, bold: true, color: C.accent1, margin: 0, isTextBox: true, objectName: "dur-stat" });
  s.addText("PV HR → PV chuyên môn (SLA chỉ 4 ngày)", { x: 8.95, y: 2.55, w: 3.8, h: 0.45, fontSize: 15, color: C.text2, margin: 0, isTextBox: true, objectName: "dur-label" });
  s.addText("76%", { x: 8.95, y: 3.25, w: 3.8, h: 0.95, fontSize: 48, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "over-stat" });
  s.addText("hồ sơ ở bước này vượt SLA", { x: 8.95, y: 4.2, w: 3.8, h: 0.45, fontSize: 15, color: C.text2, margin: 0, isTextBox: true, objectName: "over-label" });
  card(s, 8.95, 4.95, 3.8, 1.85, "dur-insight");
  s.addText("Nghẽn về năng lực xử lý: lịch phỏng vấn chuyên môn của quản lý khối Công nghệ và Dữ liệu quá kín.", { x: 9.15, y: 5.05, w: 3.4, h: 1.65, fontSize: 14, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: "dur-insight-text" });
  s.addNotes("Biểu đồ so sánh trung vị thời gian thực tế của từng bước với SLA. Hầu hết các bước nằm trong hoặc sát SLA, riêng bước từ phỏng vấn HR sang phỏng vấn chuyên môn mất trung vị 7 ngày trong khi SLA chỉ 4 ngày, 76% hồ sơ vượt hạn. Đây là điểm nghẽn về năng lực: hồ sơ phải chờ lịch của quản lý chuyên môn.");

  // ================================================================ 8. Điểm nghẽn tự động
  s = pres.addSlide({ masterName: "A_CONTENT", sectionTitle: "Kết quả" });
  s.addText("Phát hiện điểm nghẽn tự động: 4 quy tắc", { placeholder: "title" });
  const R = [
    ["QUY TẮC 1 · CHUYỂN ĐỔI", "PV chuyên môn: 47,3%", "Vòng có tỷ lệ qua thấp nhất (≥ 10 hồ sơ) – 52 hồ sơ dừng lại ở vòng này", "Cao", C.accent4],
    ["QUY TẮC 2 · THỜI GIAN", "PV HR → PV CM: 7,0 ngày", "Tỷ số trung vị / SLA lớn nhất – SLA 4 ngày, 76% hồ sơ vượt", "Cao", C.accent4],
    ["QUY TẮC 3 · TỒN ĐỌNG", "15 hồ sơ quá SLA", "Hồ sơ đang xử lý nằm ở vòng hiện tại lâu hơn SLA – nhiều nhất ở vòng Nộp hồ sơ (6)", "Trung bình", C.accent1],
    ["QUY TẮC 4 · RÚT HỒ SƠ", "48 ứng viên tự rút", "Tập trung sau PV HR: chờ lâu nên nhận offer nơi khác", "Trung bình", C.accent1],
  ];
  R.forEach(([k, big, d, sev, col], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.55 + Math.floor(i / 2) * 2.62;
    card(s, x, y, 5.95, 2.42, `rule-card-${i}`);
    s.addText(k, { x: x + 0.35, y: y + 0.28, w: 3.6, h: 0.35, fontSize: 12, bold: true, color: C.accent3, charSpacing: 1, margin: 0, isTextBox: true, objectName: `rule-key-${i}` });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 4.25, y: y + 0.25, w: 1.4, h: 0.42, rectRadius: 0.2, fill: { color: col }, line: { color: col, width: 0 }, objectName: `rule-sev-${i}` });
    s.addText(sev, { x: x + 4.25, y: y + 0.25, w: 1.4, h: 0.42, fontSize: 12, bold: true, color: C.text1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `rule-sev-text-${i}` });
    s.addText(big, { x: x + 0.35, y: y + 0.75, w: 5.3, h: 0.7, fontSize: 24, bold: true, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: `rule-big-${i}` });
    s.addText(d, { x: x + 0.35, y: y + 1.5, w: 5.3, h: 0.8, fontSize: 14, color: C.text2, valign: "top", margin: 0, isTextBox: true, objectName: `rule-desc-${i}` });
  });
  s.addNotes("Hàm bottlenecks áp dụng 4 quy tắc và hiển thị cảnh báo ngay đầu dashboard. Quy tắc chuyển đổi tìm vòng có tỷ lệ qua thấp nhất; quy tắc thời gian tìm bước có trung vị so với SLA lớn nhất; quy tắc tồn đọng đếm hồ sơ đang quá hạn; quy tắc rút hồ sơ chỉ ra vòng mà ứng viên bỏ đi nhiều nhất. Kết quả khớp với kịch bản dữ liệu mẫu: chờ phỏng vấn chuyên môn quá lâu dẫn tới nhiều ứng viên rút hồ sơ.");

  // ================================================================ 9. Giao diện thực tế
  s = pres.addSlide({ masterName: "A_CONTENT", sectionTitle: "Kết quả" });
  s.addText("Giao diện dashboard trong hệ thống", { placeholder: "title" });
  await fitImage(s, path.join(ASSETS, "a_dashboard.jpg"), { x: 0.6, y: 1.45, w: 7.9, h: 5.35 }, { align: "left", alt: "Ảnh chụp dashboard pipeline: bộ lọc, KPI, cảnh báo điểm nghẽn và phễu", name: "dashboard-shot" });
  s.addText([
    { text: "Bộ lọc chung: ", options: { bold: true, color: C.text1 } }, { text: "thời gian, phòng ban, vị trí, nguồn", options: { breakLine: true } },
    { text: "7 ô KPI: ", options: { bold: true, color: C.text1 } }, { text: "hồ sơ, ứng viên, đang xử lý, nhận việc, tỷ lệ tuyển, time-to-hire, nhận offer", options: { breakLine: true } },
    { text: "Cảnh báo điểm nghẽn ", options: { bold: true, color: C.text1 } }, { text: "tự động ở đầu trang", options: { breakLine: true } },
    { text: "Biểu đồ: ", options: { bold: true, color: C.text1 } }, { text: "phễu, SLA, xu hướng tuần, nguồn, lý do rớt – kèm bảng số liệu", options: { breakLine: true } },
    { text: "Nguồn: ", options: { bold: true, color: C.text1 } }, { text: "TopCV 92 hồ sơ nhưng tuyển 4,3%; LinkedIn 13,9%", options: { breakLine: true } },
    { text: "Theo quyền: ", options: { bold: true, color: C.text1 } }, { text: "hiring manager chỉ thấy phòng ban mình" },
  ], { x: 8.8, y: 1.5, w: 3.95, h: 5.3, fontSize: 14, color: C.text2, paraSpaceAfter: 10, valign: "top", margin: 0, isTextBox: true, objectName: "ui-points" });
  s.addNotes("Đây là giao diện thật của dashboard trong sản phẩm. Phía trên là hàng bộ lọc dùng chung, tiếp theo là các ô KPI và cảnh báo điểm nghẽn. Mỗi biểu đồ đều có bảng số liệu đi kèm. Bảng màu được kiểm tra an toàn cho người mù màu. Dashboard tuân theo phân quyền: quản lý tuyển dụng chỉ thấy số liệu của phòng ban mình.");

  // ================================================================ 10. Kết luận
  pres.addSection({ title: "Kết luận" });
  s = pres.addSlide({ masterName: "A_CLOSING", sectionTitle: "Kết luận" });
  s.addText("Kết luận và tài liệu tham khảo", { placeholder: "title" });
  [["Dashboard trả lời 4 câu hỏi của HR", "từ một kho dữ liệu duy nhất, cập nhật sau mỗi lần ETL"],
    ["Chỉ ra đúng điểm nghẽn", "chờ PV chuyên môn 7,0 ngày, tỷ lệ qua vòng chỉ 47,3%"],
    ["Hướng phát triển", "cảnh báo SLA qua email, dự báo time-to-hire bằng học máy"]].forEach(([h, d], i) => {
    const y = 1.6 + i * 1.6;
    badge(s, 0.6, y, String(i + 1), `take-badge-${i}`);
    s.addText([{ text: h, options: { bold: true, fontSize: 19, color: C.background1, breakLine: true } }, { text: d, options: { fontSize: 15, color: C.background2 } }],
      { x: 1.45, y: y - 0.05, w: 5.2, h: 1.3, valign: "top", margin: 0, isTextBox: true, objectName: `take-${i}` });
  });
  s.addText("TÀI LIỆU THAM KHẢO", { x: 7.3, y: 1.6, w: 5.4, h: 0.4, fontSize: 13, bold: true, color: C.accent1, charSpacing: 2, margin: 0, isTextBox: true, objectName: "ref-head" });
  const refs = [
    "[1] R. Kimball, M. Ross, The Data Warehouse Toolkit, 3rd ed., Wiley, 2013.",
    "[2] W. McKinney, Python for Data Analysis, 3rd ed., O'Reilly, 2022.",
    "[3] PostgreSQL 16 Documentation – Window Functions, postgresql.org.",
    "[4] Plotly Python Graphing Library, plotly.com/python.",
    "[5] Streamlit Documentation, docs.streamlit.io.",
    "[6] FastAPI Documentation, fastapi.tiangolo.com.",
    "[7] Nhóm 8, Báo cáo “Kho dữ liệu tuyển dụng có AI phân tích pipeline ứng viên”, HVHK, 2026.",
  ];
  s.addText(refs.map((r, i) => ({ text: r, options: { breakLine: i < refs.length - 1 } })), { x: 7.3, y: 2.1, w: 5.4, h: 4.6, fontSize: 13, color: C.background2, paraSpaceAfter: 8, valign: "top", margin: 0, isTextBox: true, objectName: "refs" });
  s.addNotes("Tóm lại, dashboard giúp HR trả lời bốn câu hỏi về pipeline từ một nguồn dữ liệu duy nhất và đã chỉ ra đúng điểm nghẽn ở vòng phỏng vấn chuyên môn. Hướng phát triển là gửi cảnh báo SLA qua email và dự báo thời gian tuyển. Em xin cảm ơn thầy cô và các bạn đã lắng nghe.");

  await pres.writeFile({ fileName: OUT });
  if (APPLY_THEME) {
    const { applyTheme } = require(APPLY_THEME);
    await applyTheme(OUT, THEME);
  }
  console.log("Đã ghi", OUT);
}

build().catch((e) => { console.error(e); process.exit(1); });
