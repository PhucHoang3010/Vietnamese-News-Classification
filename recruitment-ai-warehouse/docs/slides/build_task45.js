// Bộ slide Task 4 + 5 – NLP/AI xử lý CV; Phân quyền, chống thiên vị, báo cáo & triển khai (Nguyễn Phan Khánh Vy)
// Phong cách: nền tối tím than, tiêu đề serif (Cambria), điểm nhấn san hô + bạc hà, icon trong vòng tròn.
// Chạy: NODE_PATH=<node_modules> node build_task45.js
const path = require("path");
const pptxgen = require("pptxgenjs");
const lu = require("react-icons/lu");
const { iconPng, fitImage, ASSETS } = require("./common");

const APPLY_THEME = process.env.APPLY_THEME_JS;
const OUT = path.join(__dirname, "Slide_Task4-5_AI_PhanQuyen_NguyenPhanKhanhVy.pptx");

const THEME = {
  name: "TalentLens Responsible AI",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1A1428", lt1: "FFFFFF", dk2: "2B2342", lt2: "E9E3F5",
    accent1: "FF7A59", accent2: "6FD3A8", accent3: "B9A6E8", accent4: "FFCF5C",
    accent5: "6B5B95", accent6: "A79FC4", hlink: "B9A6E8", folHlink: "A79FC4",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Task 4 + 5 – NLP/AI xử lý CV; Phân quyền, chống thiên vị, báo cáo & triển khai";
pres.author = "Nguyễn Phan Khánh Vy";
pres.company = "Nhóm 8 – Học viện Hàng không Việt Nam";
const C = pres.SchemeColor;

pres.defineSlideMaster({
  title: "B_TITLE",
  background: { color: HEX.dk1 },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 0.75, y: 1.3, w: 7.4, h: 0.45, fontSize: 13, bold: true, color: C.accent2, charSpacing: 2, align: "left" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.75, y: 1.8, w: 7.4, h: 1.9, fontSize: 44, bold: true, color: C.background1, valign: "top", align: "left" }, text: "" } },
    { placeholder: { options: { name: "subtitle", type: "body", x: 0.75, y: 3.8, w: 7.2, h: 1.2, fontSize: 18, color: C.background2, valign: "top", align: "left" }, text: "" } },
    { placeholder: { options: { name: "presenter", type: "body", x: 0.75, y: 5.5, w: 7.2, h: 0.9, fontSize: 15, color: C.background1, valign: "top", align: "left" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "B_CONTENT",
  background: { color: HEX.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.38, w: 12.1, h: 0.85, fontSize: 32, bold: true, color: C.background1, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Nhóm 8 · Task 4 + 5 – NLP/AI xử lý CV & Phân quyền · Nguyễn Phan Khánh Vy", options: { x: 0.6, y: 7.0, w: 9, h: 0.3, fontSize: 10, color: C.accent6, margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.55, h: 0.3, fontSize: 10, color: HEX.accent6, align: "right" },
});

const ICON_CACHE = {};
async function icon(name, hex = HEX.dk1) {
  const key = `${name}-${hex}`;
  if (!ICON_CACHE[key]) ICON_CACHE[key] = await iconPng(lu[name], hex);
  return ICON_CACHE[key];
}
// Motif: icon trong vòng tròn màu
async function iconCircle(slide, name, x, y, d, fill, objName) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill, width: 0 }, objectName: `${objName}-circle` });
  const pad = d * 0.24;
  slide.addImage({ data: await icon(name), x: x + pad, y: y + pad, w: d - 2 * pad, h: d - 2 * pad, altText: "", objectName: `${objName}-icon` });
}
const card = (slide, x, y, w, h, name, fill = C.text2) =>
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.14, fill: { color: fill }, line: { color: fill, width: 0 }, objectName: name });
const text = (slide, t, o) => slide.addText(t, { margin: 0, isTextBox: true, valign: "top", ...o });
const chartText = { catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt", titleFontFace: "+mn-lt" };

async function build() {
  // ================================================================ 1. Tiêu đề
  pres.addSection({ title: "Mở đầu" });
  let s = pres.addSlide({ masterName: "B_TITLE", sectionTitle: "Mở đầu" });
  s.addText("NHÓM 8 · ĐỀ TÀI AI 9 · LẬP TRÌNH PYTHON", { placeholder: "kicker" });
  s.addText("AI xử lý CV có kiểm soát", { placeholder: "title" });
  s.addText([{ text: "Task 4 – NLP/AI xử lý CV", options: { breakLine: true } }, { text: "Task 5 – Phân quyền, chống thiên vị, báo cáo tuần và triển khai" }], { placeholder: "subtitle" });
  s.addText([{ text: "Nguyễn Phan Khánh Vy · Nhóm trưởng", options: { bold: true, breakLine: true } }, { text: "MSSV 2431540032 · Lớp 24ĐHTT01" }], { placeholder: "presenter" });
  const HERO = [["LuBrain", HEX.accent3, "Hiểu CV", 1.35], ["LuShieldCheck", HEX.accent1, "Bảo vệ dữ liệu", 2.95], ["LuUserCheck", HEX.accent2, "Con người quyết định", 4.55]];
  for (const [ic, col, label, y] of HERO) {
    await iconCircle(s, ic, 9.0, y, 1.3, col, `hero-${label}`);
    text(s, label, { x: 10.55, y: y + 0.2, w: 2.2, h: 0.9, fontSize: 17, bold: true, color: C.background1, valign: "middle", objectName: `hero-label-${label}` });
  }
  s.addNotes("Em là Nguyễn Phan Khánh Vy, nhóm trưởng, phụ trách Task 4 – xử lý CV bằng NLP và AI, và Task 5 – phân quyền, chống thiên vị, báo cáo tuần và triển khai. Thông điệp chính của phần này: AI trong tuyển dụng phải hiểu được CV, bảo vệ dữ liệu cá nhân và luôn để con người ra quyết định cuối cùng.");

  // ================================================================ 2. Cơ hội & rủi ro
  pres.addSection({ title: "Bài toán" });
  s = pres.addSlide({ masterName: "B_CONTENT", sectionTitle: "Bài toán" });
  s.addText("AI giúp được nhiều, nhưng phải an toàn", { placeholder: "title" });
  const COLS = [
    ["Cơ hội", "LuSparkles", HEX.accent2, [["LuFileText", "Đọc và tóm tắt hàng trăm CV trong vài giây"], ["LuMessagesSquare", "Gợi ý câu hỏi phỏng vấn theo JD"], ["LuFileChartColumn", "Tổng hợp lý do rớt, viết báo cáo tuần"]]],
    ["Rủi ro", "LuTriangleAlert", HEX.accent1, [["LuScale", "Thiên vị: Amazon ngừng công cụ AI tuyển dụng vì đánh giá thấp CV nữ (2018)"], ["LuLock", "Dữ liệu cá nhân: NĐ 13/2023; Bộ luật Lao động 2019 cấm phân biệt đối xử"], ["LuBrain", "LLM có thể “ảo giác” – sinh thông tin không có trong CV"]]],
  ];
  for (const [ci, [head, ic, col, items]] of COLS.entries()) {
    const x = 0.6 + ci * 6.15;
    card(s, x, 1.5, 5.95, 4.15, `col-card-${ci}`);
    await iconCircle(s, ic, x + 0.35, 1.75, 0.7, col, `col-head-${ci}`);
    text(s, head, { x: x + 1.25, y: 1.8, w: 4.4, h: 0.6, fontSize: 22, bold: true, color: C.background1, fontFace: "Cambria", valign: "middle", objectName: `col-title-${ci}` });
    for (const [ii, [iic, t]] of items.entries()) {
      const y = 2.75 + ii * 0.95;
      await iconCircle(s, iic, x + 0.4, y, 0.55, col, `col-${ci}-item-${ii}`);
      text(s, t, { x: x + 1.15, y: y - 0.05, w: 4.55, h: 0.8, fontSize: 15, color: C.background2, valign: "middle", objectName: `col-${ci}-text-${ii}` });
    }
  }
  card(s, 0.6, 5.85, 12.1, 0.85, "principle", C.accent5);
  text(s, [{ text: "Nguyên tắc thiết kế:  ", options: { bold: true, color: C.accent4 } }, { text: "AI chỉ tóm tắt và gợi ý – không chấm điểm, không quyết định tuyển/loại. Con người kiểm duyệt.", options: { color: C.background1 } }],
    { x: 0.95, y: 5.85, w: 11.5, h: 0.85, fontSize: 16, valign: "middle", objectName: "principle-text" });
  s.addNotes("AI mang lại nhiều cơ hội: đọc và tóm tắt CV rất nhanh, gợi ý câu hỏi phỏng vấn, tổng hợp lý do rớt. Nhưng rủi ro cũng lớn: trường hợp Amazon năm 2018 cho thấy AI có thể thiên vị; pháp luật Việt Nam yêu cầu bảo vệ dữ liệu cá nhân và cấm phân biệt đối xử; mô hình ngôn ngữ còn có thể ảo giác. Vì vậy nguyên tắc thiết kế của nhóm là AI chỉ hỗ trợ, con người quyết định.");

  // ================================================================ 3. Luồng AI có kiểm duyệt
  pres.addSection({ title: "Task 4 – NLP/AI" });
  s = pres.addSlide({ masterName: "B_CONTENT", sectionTitle: "Task 4 – NLP/AI" });
  s.addText("Luồng xử lý CV có kiểm duyệt", { placeholder: "title" });
  const STEPS = [["LuFileText", "CV / hồ sơ", "PDF · DOCX · TXT", HEX.accent3], ["LuScanText", "Trích văn bản", "pypdf · python-docx", HEX.accent3], ["LuEyeOff", "Ẩn danh", "bỏ tên, ngày sinh, giới tính…", HEX.accent1],
    ["LuSparkles", "AI engine", "Claude / NLP nội bộ", HEX.accent3], ["LuShieldAlert", "Bias guard", "7 nhóm thuộc tính", HEX.accent1], ["LuHourglass", "Chờ duyệt", "pending_review", HEX.accent3], ["LuUserCheck", "HR duyệt", "duyệt · sửa · từ chối", HEX.accent2]];
  const stepW = 12.1 / STEPS.length;
  s.addShape(pres.shapes.LINE, { x: 0.6 + stepW / 2, y: 2.12, w: stepW * (STEPS.length - 1), h: 0, line: { color: HEX.accent5, width: 2 }, objectName: "flow-line" });
  for (const [i, [ic, t, sub, col]] of STEPS.entries()) {
    const cx = 0.6 + stepW * i + stepW / 2;
    await iconCircle(s, ic, cx - 0.5, 1.62, 1.0, col, `step-${i}`);
    text(s, t, { x: cx - stepW / 2, y: 2.78, w: stepW, h: 0.4, fontSize: 15, bold: true, color: C.background1, align: "center", objectName: `step-title-${i}` });
    text(s, sub, { x: cx - stepW / 2 + 0.05, y: 3.18, w: stepW - 0.1, h: 0.6, fontSize: 12, color: C.accent6, align: "center", objectName: `step-sub-${i}` });
  }
  const ENG = [["LuSparkles", HEX.accent3, "Claude (Anthropic SDK)", "Mô hình mặc định claude-opus-5-5 · đầu ra ràng buộc theo JSON Schema · fallback phía máy chủ khi bị từ chối · chỉ viết phần diễn giải"],
    ["LuDatabase", HEX.accent2, "Engine NLP nội bộ (dự phòng)", "Từ điển 14 nhóm ~100 kỹ năng · TF-IDF cosine CV–JD · luật phân loại 12 nhóm lý do rớt · tự dùng khi không có API key hoặc Claude lỗi"]];
  for (const [i, [ic, col, h, d]] of ENG.entries()) {
    const x = 0.6 + i * 6.15;
    card(s, x, 4.2, 5.95, 2.5, `engine-${i}`);
    await iconCircle(s, ic, x + 0.35, 4.5, 0.8, col, `engine-icon-${i}`);
    text(s, h, { x: x + 1.4, y: 4.5, w: 4.3, h: 0.5, fontSize: 19, bold: true, color: C.background1, fontFace: "Cambria", objectName: `engine-title-${i}` });
    text(s, d, { x: x + 1.4, y: 5.05, w: 4.3, h: 1.5, fontSize: 14, color: C.background2, objectName: `engine-desc-${i}` });
  }
  s.addNotes("CV đi qua 7 bước. Văn bản được trích từ PDF hoặc DOCX, sau đó ẩn danh – bỏ họ tên, ngày sinh, giới tính, tình trạng hôn nhân, địa chỉ – rồi mới gửi cho AI. Kết quả được bộ lọc thiên vị quét và lưu ở trạng thái chờ duyệt cho tới khi HR duyệt. Hệ thống có hai engine: Claude khi có API key và engine NLP nội bộ làm dự phòng, nên sản phẩm luôn hoạt động.");

  // ================================================================ 4. Demo CV mẫu
  s = pres.addSlide({ masterName: "B_CONTENT", sectionTitle: "Task 4 – NLP/AI" });
  s.addText("Demo: xử lý một CV mẫu", { placeholder: "title" });
  card(s, 0.6, 1.45, 7.75, 4.55, "shot-frame", C.background1);
  await fitImage(s, path.join(ASSETS, "b_cv_result.jpg"), { x: 0.72, y: 1.57, w: 7.51, h: 4.31 }, { alt: "Kết quả AI phân tích CV mẫu: tóm tắt, điểm nổi bật, độ phủ kỹ năng JD 100%", name: "cv-shot" });
  text(s, "CV_Ly_Duc_Tri_302.pdf đối chiếu với JD Data Analyst – kết quả lưu ở trạng thái Chờ duyệt", { x: 0.6, y: 6.15, w: 7.75, h: 0.5, fontSize: 12, italic: true, color: C.accent6, objectName: "cv-caption" });
  text(s, "TRƯỚC KHI GỬI AI", { x: 8.7, y: 1.45, w: 4.0, h: 0.35, fontSize: 12, bold: true, color: C.accent1, charSpacing: 2, objectName: "anon-head" });
  card(s, 8.7, 1.85, 4.0, 1.6, "orig-box");
  text(s, ["LÝ ĐỨC TRÍ", "Ngày sinh: 25/05/2000 | Giới tính: Nam", "Điện thoại: 0356 426 820 | Email: …", "Tình trạng hôn nhân: Đã kết hôn"].map((t, i, a) => ({ text: t, options: { breakLine: i < a.length - 1 } })),
    { x: 8.9, y: 1.95, w: 3.7, h: 1.45, fontFace: "Courier New", fontSize: 11, color: C.background2, objectName: "orig-text" });
  s.addShape(pres.shapes.DOWN_ARROW, { x: 10.45, y: 3.5, w: 0.5, h: 0.4, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0 }, objectName: "anon-arrow" });
  card(s, 8.7, 3.95, 4.0, 1.25, "anon-box", C.accent5);
  text(s, ["[ỨNG VIÊN]", "[NGAY_SINH – đã ẩn]", "[LIEN_HE – đã ẩn]  [HON_NHAN – đã ẩn]"].map((t, i, a) => ({ text: t, options: { breakLine: i < a.length - 1 } })),
    { x: 8.9, y: 4.05, w: 3.7, h: 1.1, fontFace: "Courier New", fontSize: 11, color: C.background1, objectName: "anon-text" });
  [["5", "loại thông tin bị ẩn"], ["5/5", "kỹ năng bắt buộc của JD"]].forEach(([n, l], i) => {
    const x = 8.7 + i * 2.05;
    text(s, n, { x, y: 5.4, w: 1.95, h: 0.75, fontSize: 36, bold: true, color: C.accent2, fontFace: "Cambria", objectName: `cv-stat-${i}` });
    text(s, l, { x, y: 6.15, w: 1.95, h: 0.55, fontSize: 13, color: C.background2, objectName: `cv-stat-l-${i}` });
  });
  s.addNotes("Đây là demo của Task 4 – xử lý một CV mẫu. Bên phải là phần ẩn danh: các dòng họ tên, ngày sinh, giới tính, liên hệ, hôn nhân được thay bằng nhãn giữ chỗ trước khi gửi cho AI – tổng cộng 5 loại thông tin bị ẩn. Bên trái là kết quả: tiêu đề, tóm tắt, điểm nổi bật có bằng chứng trong CV và độ phủ kỹ năng bắt buộc của JD – ở đây 5 trên 5 kỹ năng. Độ phủ chỉ là chỉ số tham khảo, không phải điểm xếp hạng ứng viên.");

  // ================================================================ 5. Lý do rớt & câu hỏi PV
  s = pres.addSlide({ masterName: "B_CONTENT", sectionTitle: "Task 4 – NLP/AI" });
  s.addText("Lý do rớt phổ biến và câu hỏi phỏng vấn", { placeholder: "title" });
  const REJ = [["Kinh nghiệm chưa phù hợp", 33.8], ["Thiếu kỹ năng chuyên môn", 29.0], ["Nhận offer nơi khác", 10.0], ["Văn hoá / thái độ", 6.3], ["Kỳ vọng lương", 5.6], ["Giao tiếp / trình bày", 3.7]];
  card(s, 0.6, 1.45, 6.9, 5.3, "rej-card");
  s.addChart(pres.charts.BAR, [{ name: "Tỷ lệ (%)", labels: REJ.map((r) => r[0]), values: REJ.map((r) => r[1]) }], {
    x: 0.8, y: 1.6, w: 6.5, h: 4.5, barDir: "bar", catAxisOrientation: "maxMin", barGapWidthPct: 50,
    chartColors: [HEX.accent1], showValue: true, dataLabelPosition: "outEnd", dataLabelColor: HEX.lt2, dataLabelFontSize: 13,
    dataLabelFormatCode: '0.0"%"', valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    catAxisLabelColor: HEX.lt2, catAxisLabelFontSize: 13, catAxisLineShow: false, showLegend: false,
    showTitle: true, title: "Tỷ lệ trong 269 hồ sơ bị loại / rút", titleColor: HEX.lt1, titleFontSize: 14, ...chartText, objectName: "rejection-chart",
  });
  text(s, "Phân nhóm tự động bằng luật từ khoá tiếng Việt/Anh – 12 nhóm, kèm đề xuất cải tiến cho từng nhóm", { x: 0.85, y: 6.1, w: 6.4, h: 0.55, fontSize: 12, italic: true, color: C.accent6, objectName: "rej-caption" });
  text(s, "BỘ CÂU HỎI CÓ CẤU TRÚC THEO JD", { x: 7.85, y: 1.5, w: 4.9, h: 0.35, fontSize: 12, bold: true, color: C.accent2, charSpacing: 2, objectName: "q-head" });
  const QT = [["LuSearch", "Chuyên môn", "kiểm chứng kỹ năng đã nêu trong CV"], ["LuListChecks", "Làm rõ JD", "kỹ năng JD yêu cầu nhưng CV chưa thể hiện"], ["LuFileText", "Làm rõ CV", "vai trò cá nhân trong thành tích"], ["LuMessagesSquare", "Tình huống & STAR", "giải quyết vấn đề, làm việc nhóm"]];
  for (const [i, [ic, h, d]] of QT.entries()) {
    const y = 2.0 + i * 0.95;
    await iconCircle(s, ic, 7.85, y, 0.6, HEX.accent3, `qt-${i}`);
    text(s, [{ text: h, options: { bold: true, color: C.background1, breakLine: true } }, { text: d, options: { color: C.background2 } }], { x: 8.65, y: y - 0.05, w: 4.1, h: 0.8, fontSize: 14, objectName: `qt-text-${i}` });
  }
  card(s, 7.85, 5.9, 4.85, 0.85, "avoid", C.accent5);
  await iconCircle(s, "LuBan", 8.0, 6.04, 0.57, HEX.accent1, "avoid-icon");
  text(s, "Không hỏi: tuổi, hôn nhân, quê quán, tôn giáo, ngoại hình", { x: 8.7, y: 5.9, w: 3.9, h: 0.85, fontSize: 14, bold: true, color: C.background1, valign: "middle", objectName: "avoid-text" });
  s.addNotes("Với 269 hồ sơ bị loại hoặc tự rút, hệ thống phân nhóm lý do tự động: nhiều nhất là kinh nghiệm chưa phù hợp – 33,8% và thiếu kỹ năng chuyên môn – 29%; đáng chú ý 10% ứng viên rút vì đã nhận offer nơi khác. Bên phải là bộ câu hỏi phỏng vấn có cấu trúc gắn với JD: câu chuyên môn, câu làm rõ kỹ năng còn thiếu, làm rõ CV, tình huống và hành vi theo STAR, kèm danh sách chủ đề không được hỏi.");

  // ================================================================ 6. RBAC
  pres.addSection({ title: "Task 5 – Phân quyền & triển khai" });
  s = pres.addSlide({ masterName: "B_CONTENT", sectionTitle: "Task 5 – Phân quyền & triển khai" });
  s.addText("Phân quyền theo vai trò (RBAC)", { placeholder: "title" });
  const yes = (t = "Có") => ({ text: t, options: { color: C.accent2, bold: true } });
  const no = (t = "Không") => ({ text: t, options: { color: C.accent1, bold: true } });
  const head = (t) => ({ text: t, options: { bold: true, color: C.text1, fill: { color: C.accent3 } } });
  const cell = (t) => ({ text: t, options: { color: C.background1 } });
  const rows = [
    [head("Chức năng / dữ liệu"), head("Admin"), head("HR"), head("Hiring manager")],
    [cell("Phạm vi dữ liệu"), cell("Toàn công ty"), cell("Toàn công ty"), cell("Phòng ban của mình")],
    [cell("Họ tên, email, SĐT, giới tính, ngày sinh"), yes("Đầy đủ"), yes("Đầy đủ"), no("Bị che")],
    [cell("Chạy ETL, chạy AI, giám sát công bằng"), yes(), yes(), no()],
    [cell("Nhận xét AI"), yes("Xem & duyệt"), yes("Xem & duyệt"), cell("Chỉ bản đã duyệt")],
    [cell("Ghi nhận kết quả phỏng vấn"), yes(), yes(), yes("Có (phòng mình)")],
    [cell("Quản lý người dùng, nhật ký"), yes(), no(), no()],
  ];
  s.addTable(rows, { x: 0.6, y: 1.5, w: 8.3, colW: [3.5, 1.4, 1.4, 2.0], fontSize: 14, fontFace: "Calibri", fill: { color: C.text2 }, border: { type: "solid", pt: 1, color: HEX.dk1 }, rowH: 0.62, valign: "middle", margin: 0.08, objectName: "rbac-table" });
  card(s, 9.25, 1.5, 3.45, 5.2, "server-card");
  await iconCircle(s, "LuLock", 9.55, 1.8, 0.75, HEX.accent2, "server-icon");
  text(s, "Thực thi ở máy chủ", { x: 9.55, y: 2.7, w: 3.0, h: 0.5, fontSize: 18, bold: true, color: C.background1, fontFace: "Cambria", objectName: "server-title" });
  text(s, [
    { text: "require(permission) gắn vào từng API", options: { bullet: true, breakLine: true } },
    { text: "Lọc phòng ban ngay trong câu truy vấn", options: { bullet: true, breakLine: true } },
    { text: "Serializer che PII: d***@gmail.com", options: { bullet: true, breakLine: true } },
    { text: "JWT ký HMAC-SHA256, mật khẩu PBKDF2", options: { bullet: true, breakLine: true } },
    { text: "Manager gọi /api/users → 403", options: { bullet: true } },
  ], { x: 9.55, y: 3.25, w: 3.0, h: 3.3, fontSize: 14, color: C.background2, paraSpaceAfter: 6, objectName: "server-list" });
  s.addNotes("Task 5 bắt đầu bằng phân quyền theo vai trò. Có ba vai trò: Admin, HR và hiring manager. Hiring manager chỉ thấy phòng ban của mình, thông tin cá nhân bị che và chỉ thấy nhận xét AI đã được duyệt. Điều quan trọng là quyền được kiểm tra ở máy chủ cho từng API chứ không chỉ ẩn nút trên giao diện – ví dụ manager gọi API quản lý người dùng sẽ nhận lỗi 403.");

  // ================================================================ 7. Hai vai trò
  s = pres.addSlide({ masterName: "B_CONTENT", sectionTitle: "Task 5 – Phân quyền & triển khai" });
  s.addText("Demo: hai vai trò thấy dữ liệu khác nhau", { placeholder: "title" });
  const SIDES = [["HR · hr.lan", "331 hồ sơ toàn công ty, thông tin đầy đủ", HEX.accent2, "b_hr_list.jpg", "Danh sách hồ sơ dưới quyền HR, hiện tên và email đầy đủ"],
    ["Hiring manager · manager.data", "106 hồ sơ khối Dữ liệu & AI, đã che", HEX.accent1, "b_mgr_list.jpg", "Danh sách hồ sơ dưới quyền hiring manager, tên và email đã bị che"]];
  for (const [i, [who, scope, col, file, alt]] of SIDES.entries()) {
    const x = 0.6 + i * 6.15;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.45, w: 3.6, h: 0.5, rectRadius: 0.25, fill: { color: col }, line: { color: col, width: 0 }, objectName: `role-pill-${i}` });
    text(s, who, { x, y: 1.45, w: 3.6, h: 0.5, fontSize: 15, bold: true, color: C.text1, align: "center", valign: "middle", objectName: `role-pill-text-${i}` });
    text(s, scope, { x: x + 3.75, y: 1.45, w: 2.2, h: 0.55, fontSize: 12, color: C.background2, valign: "middle", objectName: `role-scope-${i}` });
    card(s, x, 2.1, 5.95, 3.7, `role-frame-${i}`, C.background1);
    await fitImage(s, path.join(ASSETS, file), { x: x + 0.1, y: 2.2, w: 5.75, h: 3.5 }, { alt, name: `role-shot-${i}` });
  }
  const DIFFS = [["Phan Thị Mỹ Duyên", "UV-00316 · P.T.M.D."], ["duyen.phan01@gmail.com", "d***@gmail.com"], ["Tất cả nhận xét AI", "chỉ bản đã duyệt"]];
  DIFFS.forEach(([a, b2], i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 6.0, 3.9, 0.75, `diff-${i}`);
    text(s, [{ text: a, options: { color: C.accent2 } }, { text: "  →  ", options: { color: C.accent6 } }, { text: b2, options: { color: C.accent1, bold: true } }], { x: x + 0.15, y: 6.0, w: 3.6, h: 0.75, fontSize: 13, valign: "middle", objectName: `diff-text-${i}` });
  });
  s.addNotes("Đây là demo của Task 5: cùng một hệ thống nhưng hai vai trò thấy dữ liệu khác nhau. HR thấy 331 hồ sơ toàn công ty với họ tên, email đầy đủ. Quản lý khối Dữ liệu và AI chỉ thấy 106 hồ sơ của 3 vị trí trong khối, họ tên được thay bằng mã ứng viên và chữ viết tắt, email bị che một phần. Ví dụ cùng một ứng viên Phan Thị Mỹ Duyên, quản lý chỉ thấy UV-00316 và d sao sao sao a còng gmail.");

  // ================================================================ 8. Chống thiên vị & kiểm duyệt
  s = pres.addSlide({ masterName: "B_CONTENT", sectionTitle: "Task 5 – Phân quyền & triển khai" });
  s.addText("Chống thiên vị và kiểm duyệt nhận xét AI", { placeholder: "title" });
  const COL3 = [["LuShieldAlert", HEX.accent1, "Bias guard", "Quét nhận xét của AI và của người phỏng vấn theo 7 nhóm: giới tính, tuổi, hôn nhân/thai sản, vùng miền, tôn giáo/dân tộc, ngoại hình, sức khoẻ."],
    ["LuClipboardCheck", HEX.accent2, "Kiểm duyệt", "Mọi kết quả AI ở trạng thái Chờ duyệt. HR duyệt, sửa hoặc từ chối; nội dung bị gắn cờ phải ghi chú; audit log ghi lại người duyệt."],
    ["LuScale", HEX.accent3, "Giám sát quy tắc 4/5", "Tỷ lệ qua vòng theo giới tính; tỷ lệ tác động < 0,8 là tín hiệu cần rà soát tiêu chí và người phỏng vấn."]];
  for (const [i, [ic, col, h, d]] of COL3.entries()) {
    const x = 0.6 + i * 4.1;
    card(s, x, 1.5, 3.9, 3.45, `c3-${i}`);
    await iconCircle(s, ic, x + 0.35, 1.8, 0.8, col, `c3-icon-${i}`);
    text(s, h, { x: x + 1.3, y: 1.85, w: 2.45, h: 0.7, fontSize: 20, bold: true, color: C.background1, fontFace: "Cambria", valign: "middle", objectName: `c3-title-${i}` });
    text(s, d, { x: x + 0.35, y: 2.85, w: 3.25, h: 2.0, fontSize: 14, color: C.background2, objectName: `c3-desc-${i}` });
  }
  card(s, 0.6, 5.15, 8.0, 1.6, "quote", C.accent5);
  text(s, [{ text: "“Ứng viên nữ, mới kết hôn nên có thể sắp nghỉ thai sản”", options: { italic: true, color: C.background1, breakLine: true } },
    { text: "→ bị chặn lưu, chỉ rõ nhóm vi phạm: Giới tính, Hôn nhân/Thai sản", options: { color: C.accent4, bold: true } }],
    { x: 0.95, y: 5.15, w: 7.4, h: 1.6, fontSize: 16, valign: "middle", objectName: "quote-text" });
  text(s, "0,70", { x: 8.95, y: 5.05, w: 3.75, h: 0.95, fontSize: 48, bold: true, color: C.accent4, fontFace: "Cambria", objectName: "air-stat" });
  text(s, "PV chuyên môn: nam 42,3% – nữ 60,6% → cần xem xét", { x: 8.95, y: 6.0, w: 3.75, h: 0.75, fontSize: 13, color: C.background2, objectName: "air-label" });
  s.addNotes("Ba lớp bảo vệ chống thiên vị. Thứ nhất, bộ lọc thiên vị quét cả nhận xét của AI lẫn của người phỏng vấn – ví dụ nhận xét ứng viên nữ sắp nghỉ thai sản bị chặn lưu. Thứ hai, mọi kết quả AI phải được HR kiểm duyệt; nội dung bị gắn cờ phải ghi chú lý do. Thứ ba, giám sát quy tắc 4/5: ở vòng phỏng vấn chuyên môn tỷ lệ tác động là 0,70, thấp hơn 0,8 nên hệ thống cảnh báo cần rà soát – đây là tín hiệu, chưa phải kết luận.");

  // ================================================================ 9. Báo cáo tuần & triển khai
  s = pres.addSlide({ masterName: "B_CONTENT", sectionTitle: "Task 5 – Phân quyền & triển khai" });
  s.addText("Báo cáo tuần và triển khai online", { placeholder: "title" });
  card(s, 0.6, 1.45, 5.3, 5.3, "report-frame", C.background1);
  await fitImage(s, path.join(ASSETS, "b_report.jpg"), { x: 0.7, y: 1.55, w: 5.1, h: 5.1 }, { alt: "Báo cáo pipeline tuần do hệ thống tạo", name: "report-shot" });
  text(s, "BÁO CÁO TUẦN", { x: 6.3, y: 1.45, w: 6.4, h: 0.35, fontSize: 12, bold: true, color: C.accent2, charSpacing: 2, objectName: "rep-head" });
  text(s, "Tóm tắt, chỉ số tuần này so với tuần trước, điểm nghẽn, hành động đề xuất. Bản nháp → HR duyệt → quản lý mới xem được; tải Markdown/HTML.", { x: 6.3, y: 1.85, w: 6.4, h: 1.0, fontSize: 15, color: C.background2, objectName: "rep-desc" });
  text(s, "TRIỂN KHAI LÊN RENDER", { x: 6.3, y: 3.05, w: 6.4, h: 0.35, fontSize: 12, bold: true, color: C.accent1, charSpacing: 2, objectName: "dep-head" });
  const DEP = [["LuCloudUpload", "Một Docker image dùng chung", "SERVICE = api | web | all"], ["LuDatabase", "render.yaml: PostgreSQL + API + Web", "tự build mỗi lần đẩy mã lên GitHub"], ["LuRocket", "URL HTTPS công khai", "lần đầu tự tạo bảng, tài khoản demo, dữ liệu mẫu"]];
  for (const [i, [ic, h, d]] of DEP.entries()) {
    const y = 3.5 + i * 1.08;
    await iconCircle(s, ic, 6.3, y, 0.7, HEX.accent1, `dep-${i}`);
    text(s, [{ text: h, options: { bold: true, color: C.background1, breakLine: true } }, { text: d, options: { color: C.background2 } }], { x: 7.2, y: y - 0.02, w: 5.5, h: 0.85, fontSize: 15, objectName: `dep-text-${i}` });
  }
  s.addNotes("Báo cáo pipeline tuần được tạo tự động gồm số liệu tuần này so với tuần trước, điểm nghẽn và hành động đề xuất; phần nhận định do AI hỗ trợ. Báo cáo ở trạng thái bản nháp cho tới khi HR duyệt thì quản lý mới xem được. Về triển khai, sản phẩm đóng gói bằng một Docker image; tệp render.yaml tạo CSDL PostgreSQL, dịch vụ API và dịch vụ giao diện trên Render, cấp URL HTTPS công khai.");

  // ================================================================ 10. Kết luận & tham khảo
  pres.addSection({ title: "Kết luận" });
  s = pres.addSlide({ masterName: "B_CONTENT", sectionTitle: "Kết luận" });
  s.addText("Kết luận và tài liệu tham khảo", { placeholder: "title" });
  const TAKE = [["LuBrain", HEX.accent3, "AI hỗ trợ đọc CV", "tóm tắt, phân nhóm kỹ năng, lý do rớt, câu hỏi PV – với 2 engine"], ["LuShieldCheck", HEX.accent1, "Dữ liệu được bảo vệ", "RBAC 3 vai trò, che PII, ẩn danh trước khi gửi AI"], ["LuUserCheck", HEX.accent2, "Con người quyết định", "kiểm duyệt bắt buộc, bias guard, quy tắc 4/5, audit log"]];
  for (const [i, [ic, col, h, d]] of TAKE.entries()) {
    const y = 1.55 + i * 1.65;
    await iconCircle(s, ic, 0.6, y, 0.85, col, `take-${i}`);
    text(s, [{ text: h, options: { bold: true, fontSize: 19, color: C.background1, breakLine: true } }, { text: d, options: { fontSize: 14, color: C.background2 } }], { x: 1.65, y: y - 0.02, w: 4.9, h: 1.3, objectName: `take-text-${i}` });
  }
  card(s, 7.0, 1.45, 5.7, 5.3, "refs-card");
  text(s, "TÀI LIỆU THAM KHẢO", { x: 7.3, y: 1.7, w: 5.1, h: 0.35, fontSize: 12, bold: true, color: C.accent2, charSpacing: 2, objectName: "refs-head" });
  const refs = [
    "[1] J. Dastin, “Amazon scraps secret AI recruiting tool that showed bias against women,” Reuters, 2018.",
    "[2] M. Raghavan et al., “Mitigating bias in algorithmic hiring,” FAT* 2020.",
    "[3] EEOC, Uniform Guidelines on Employee Selection Procedures (quy tắc 4/5), 1978.",
    "[4] Chính phủ, Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân.",
    "[5] Quốc hội, Bộ luật Lao động 2019 (45/2019/QH14).",
    "[6] R. Sandhu et al., “Role-based access control models,” IEEE Computer, 1996.",
    "[7] G. Salton, C. Buckley, “Term-weighting approaches…,” IP&M, 1988.",
    "[8] Anthropic, Claude API documentation, docs.anthropic.com.",
  ];
  text(s, refs.map((r, i) => ({ text: r, options: { breakLine: i < refs.length - 1 } })), { x: 7.3, y: 2.15, w: 5.15, h: 4.45, fontSize: 12, color: C.background2, paraSpaceAfter: 6, objectName: "refs" });
  s.addNotes("Tóm lại, phần việc của em giúp AI hỗ trợ đọc CV hiệu quả, dữ liệu ứng viên được bảo vệ bằng phân quyền và ẩn danh, và con người luôn là người quyết định nhờ cơ chế kiểm duyệt, bộ lọc thiên vị và giám sát công bằng. Em xin cảm ơn thầy cô và các bạn đã lắng nghe.");

  await pres.writeFile({ fileName: OUT });
  if (APPLY_THEME) {
    const { applyTheme } = require(APPLY_THEME);
    await applyTheme(OUT, THEME);
  }
  console.log("Đã ghi", OUT);
}

build().catch((e) => { console.error(e); process.exit(1); });
