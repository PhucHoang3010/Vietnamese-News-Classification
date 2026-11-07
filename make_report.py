"""Sinh báo cáo Word từ kết quả trong outputs/ và outputs/experiments/:  python make_report.py"""
import json
from pathlib import Path
import pandas as pd
from docx import Document
from docx.shared import Cm, Pt, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH

O = Path(__file__).parent / "outputs"
E = O / "experiments"
m = json.load(open(O / "metrics.json", encoding="utf-8")); bench = pd.read_csv(O / "so_sanh_mo_hinh.csv", encoding="utf-8")
rep = pd.read_csv(O / "bao_cao_phan_loai.csv", index_col=0, encoding="utf-8-sig"); kw = json.load(open(O / "tu_khoa_dac_trung.json", encoding="utf-8"))
err = pd.read_csv(O / "mau_du_doan_sai.csv", encoding="utf-8-sig")


def rcsv(name):
    return pd.read_csv(E / name, encoding="utf-8-sig")


def rjson(name):
    return json.load(open(E / name, encoding="utf-8"))


tun = rcsv("tuning_final.csv"); svmj = rjson("tuning_results_best_svm.json"); sig = rcsv("significance_vs_svm.csv")
stab = rcsv("stability_summary.csv"); sp = rcsv("stability_splits.csv"); ci = rjson("bootstrap_ci.json")["Linear SVM"]; nd = rjson("near_duplicates.json")
abl = rcsv("ablation_results.csv").set_index("bien_the"); lc = rcsv("learning_curve.csv"); cal = rcsv("calibration_results.csv"); rc = rcsv("risk_coverage.csv")
ec = rjson("error_confidence.json"); pairs = rcsv("error_pairs.csv"); bylen = rcsv("error_by_length.csv"); conf_err = rcsv("errors_confident.csv"); e88 = rcsv("errors_88.csv")
fa = rjson("explain_faithfulness.json"); fcsv = rcsv("explain_faithfulness.csv")
qr = rcsv("qa_retrieval.csv"); qc = rcsv("qa_confidence.csv"); qa = rjson("qa_abstain.json"); T_cal = rjson("calibration_T.json")["T"]
cres = rcsv("conformal_results.csv"); crep = rcsv("conformal_repeat.csv"); coof = rcsv("conformal_oof_to_unseen.csv"); cprod = rjson("conformal_prod.json"); cval = rcsv("conformal_val_only.csv")
sem = rcsv("search_semantic.csv"); boolt = rjson("search_bool_tests.json")

import datetime
import importlib.metadata as imd
import re
import sys
import unittest

from docx.enum.style import WD_STYLE_TYPE
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_BREAK, WD_COLOR_INDEX, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import RGBColor

ROOT = Path(__file__).parent
FONT = "Times New Roman"
TEXT_W = 16.5                                            # bề rộng vùng chữ (cm): khổ Letter 21,59 cm trừ lề trái 3 cm và lề phải 2 cm = 16,59 cm
CENTER, LEFT, JUSTIFY = WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.JUSTIFY

d = Document()
_sec = d.sections[0]                                     # khổ giấy và lề theo đúng tệp mẫu của khoa: Letter, lề trên / dưới / phải 2 cm, lề trái 3 cm
_sec.page_width, _sec.page_height = Twips(12240), Twips(15840)
_sec.left_margin, _sec.right_margin, _sec.top_margin, _sec.bottom_margin = Twips(1701), Twips(1134), Twips(1134), Twips(1134)
_sec.header_distance = _sec.footer_distance = Twips(709)
for _cs in d.settings.element.iter(qn("w:compatSetting")):  # chế độ tương thích Word 2013 trở lên như tệp mẫu (không hiện "Compatibility Mode")
    if _cs.get(qn("w:name")) == "compatibilityMode":
        _cs.set(qn("w:val"), "15")
d.core_properties.title = "Báo cáo Học máy: Phân loại tin tức tiếng Việt"
d.core_properties.author = d.core_properties.comments = ""


def _style_font(st, size, bold=None, italic=None, name=FONT):
    f = st.font
    f.name, f.size, f.color.rgb = name, Pt(size), RGBColor(0, 0, 0)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), name)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):   # bỏ phông theo giao diện của mẫu mặc định
        if rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]


def _new_style(name, base="Normal", size=13, bold=None, italic=None, align=LEFT, before=0, after=0, spacing=1.15, keep=False, font=FONT):
    st = d.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    st.base_style = d.styles[base]
    _style_font(st, size, bold, italic, font)
    pf = st.paragraph_format
    pf.alignment, pf.space_before, pf.space_after, pf.line_spacing, pf.keep_with_next = align, Pt(before), Pt(after), spacing, keep
    return st


_z = d.settings.element.find(qn("w:zoom"))                  # mẫu mặc định của python-docx thiếu thuộc tính bắt buộc percent
if _z is not None and _z.get(qn("w:percent")) is None:
    _z.set(qn("w:percent"), "100")
_style_font(d.styles["Normal"], 13)
_pf = d.styles["Normal"].paragraph_format
_pf.alignment, _pf.space_after, _pf.line_spacing = JUSTIFY, Pt(6), 1.3
for _n, _sz, _it, _b, _a in (("Heading 1", 16, False, 18, 8), ("Heading 2", 14, False, 12, 6), ("Heading 3", 13, True, 10, 4)):
    _style_font(d.styles[_n], _sz, True, _it)
    _h = d.styles[_n].paragraph_format
    _h.alignment, _h.space_before, _h.space_after, _h.line_spacing, _h.keep_with_next = LEFT, Pt(_b), Pt(_a), 1.15, True
_new_style("Caption Figure", size=11.5, italic=True, align=CENTER, before=2, after=10, spacing=1.1)
_new_style("Caption Table", size=11.5, bold=True, align=CENTER, before=8, after=4, spacing=1.1, keep=True)
_new_style("Code Block", size=9.5, align=LEFT, after=0, spacing=1.1, font="Courier New")
_t1 = _new_style("TOC 1", size=13, align=LEFT, before=4, after=0, spacing=1.15)
_t2 = _new_style("TOC 2", size=12.5, align=LEFT, after=0, spacing=1.1)
_t2.paragraph_format.left_indent = Cm(0.8)
for _t in (_t1, _t2):
    _t.paragraph_format.tab_stops.add_tab_stop(Cm(TEXT_W), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)


def _fld(par, instr, cached="1"):
    """Chèn trường Word (số trang, mục lục...) vào đoạn par."""
    def mk(t):
        r = par.add_run(); e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), t); r._r.append(e)
    mk("begin")
    r = par.add_run(); it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = instr; r._r.append(it)
    mk("separate"); par.add_run(cached); mk("end")


def vn(x, k=1):
    """Số kiểu Việt Nam: dấu phẩy thập phân."""
    return f"{x:.{k}f}".replace(".", ",")


def pc(x, k=1):
    return vn(100 * x, k) + "%"


def pv(p):
    return "< 0,001" if p < 0.001 else vn(p, 3)


def th(n):
    return f"{int(n):,}".replace(",", ".")


def H(t, l=1): d.add_heading(t, l)
def P(t):
    p = d.add_paragraph(t)
    p.paragraph_format.first_line_indent = Cm(1)         # thụt đầu dòng 1 cm như đoạn văn trong tệp mẫu của khoa
    return p
def B(items): [d.add_paragraph(i, style="List Bullet") for i in items]


def PH(parts, align=None):
    """Đoạn có chỗ cần nhóm điền: parts = [(chữ, True nếu là chỗ trống cần điền)]; chỗ cần điền được tô vàng cho dễ thấy."""
    p = d.add_paragraph()
    for txt, hole in parts:
        r = p.add_run(txt)
        if hole:
            r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    if align is not None:
        p.alignment = align
    return p


def FORMULA(text):
    p = d.add_paragraph(); p.alignment = CENTER
    r = p.add_run(text); r.italic = True
    p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(4), Pt(8)


def CODE(lines):
    for k, ln in enumerate(lines):
        p = d.add_paragraph(ln, style="Code Block")
        p.paragraph_format.left_indent = Cm(0.6)
        p.paragraph_format.keep_with_next = k < len(lines) - 1 and len(lines) <= 10      # khối lệnh ngắn không bị tách giữa hai trang
        sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), "EEF2F6")
        p._p.get_or_add_pPr().insert_element_before(sh, "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap", "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN", "w:bidi",
                                                    "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind", "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc", "w:textDirection",
                                                    "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl", "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange")       # đúng thứ tự phần tử của chuẩn OOXML
    d.add_paragraph().paragraph_format.space_after = Pt(2)


_NT, _NF, FIGN = [0], [0], {}


def CAP(text):
    """Chú thích bảng (đặt phía trên bảng), tự đánh số."""
    _NT[0] += 1
    d.add_paragraph(f"Bảng {_NT[0]}. {text}", style="Caption Table")


def TABLE(df, fmt="{:.3f}", widths=None):
    t = d.add_table(rows=1, cols=len(df.columns)); t.style = "Light Grid Accent 1"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, c in enumerate(df.columns):
        t.rows[0].cells[i].text = str(c)
    for _, r in df.iterrows():
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = fmt.format(v).replace(".", ",") if isinstance(v, float) else str(v)
    for row in t.rows:                                   # chữ trong bảng nhỏ hơn, căn trái, dòng sát nhau
        for c in row.cells:
            for p_ in c.paragraphs:
                p_.alignment = LEFT
                p_.paragraph_format.line_spacing, p_.paragraph_format.space_after = 1.0, Pt(0)
                for run in p_.runs:
                    run.font.size = Pt(10.5)
    if widths is None:                                   # chia 16 cm theo độ dài nội dung của từng cột
        wt = [min(max(len(str(c)) * 0.7, max((len(str(v)) for v in df[c]), default=1)), 44) for c in df.columns]
        widths = [max(1.7, TEXT_W * x / sum(wt)) for x in wt]
        widths = [TEXT_W * x / sum(widths) for x in widths]
    t.autofit = False
    for i, wd in enumerate(widths):
        t.columns[i].width = Cm(wd)
    for row in t.rows:
        for c, wd in zip(row.cells, widths):
            c.width = Cm(wd)
        trpr = row._tr.get_or_add_trPr(); cs = OxmlElement("w:cantSplit"); cs.set(qn("w:val"), "true"); trpr.append(cs)       # không tách một dòng giữa hai trang
    hdr = t.rows[0]._tr.get_or_add_trPr(); hh = OxmlElement("w:tblHeader"); hh.set(qn("w:val"), "true"); hdr.append(hh)     # lặp dòng tiêu đề khi bảng qua trang
    rows_ = list(t.rows)                                 # bảng ngắn (≤ 8 dòng): giữ liền một khối trên cùng một trang;
    glued = rows_[:-1] if len(rows_) <= 8 else rows_[:2] + rows_[-3:-1]   # bảng dài được phép qua trang, nhưng dòng tiêu đề đi kèm 2 dòng đầu và 3 dòng cuối đi liền nhau
    for row in glued:
        for c in row.cells:
            for p_ in c.paragraphs:
                p_.paragraph_format.keep_with_next = True
    sp = d.add_paragraph(); sp.paragraph_format.space_after, sp.paragraph_format.line_spacing = Pt(0), 0.7


def IMG(f, cap, w=14, folder=O, key=None):
    """Chèn ảnh + chú thích 'Hình n. ...' (tự đánh số). key: tên để nhắc tới số hình trong chữ bằng @@FIG:key@@."""
    p = Path(folder) / f
    if not p.exists():
        print("thiếu ảnh, bỏ qua:", p)
        return
    _NF[0] += 1
    if key:
        FIGN[key] = _NF[0]
    d.add_picture(str(p), width=Cm(min(w, TEXT_W)))
    d.paragraphs[-1].alignment = CENTER; d.paragraphs[-1].paragraph_format.keep_with_next = True
    d.add_paragraph(f"Hình {_NF[0]}. {cap}", style="Caption Figure")


def _center(text, size=13, bold=False, italic=False, after=6):
    p = d.add_paragraph(); p.alignment = CENTER
    r = p.add_run(text); r.font.size = Pt(size); r.bold, r.italic = bold, italic
    p.paragraph_format.space_after, p.paragraph_format.line_spacing = Pt(after), 1.15
    return p


def _n_tests(pattern):
    try:
        return unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern=pattern).countTestCases()
    except Exception as e:
        print("không đếm được số bài kiểm tra:", e)
        return 0


N_FEAT, N_CMT = _n_tests("test_features.py"), _n_tests("test_comments.py")
sv0 = stab[stab.model == "Linear SVM"].iloc[0]
c0, c1 = cal.iloc[0], cal.iloc[1]
DATA = pd.read_csv(ROOT / "data" / "news_dataset.csv", encoding="utf-8").fillna("")
_w = DATA.text.str.split().str.len()

# ================================================================== trang bìa theo mẫu của khoa
# Gồm bìa chính, bìa phụ, trang danh sách nhóm kèm ô chữ ký của cán bộ chấm thi (đúng bố cục tệp mẫu của Khoa Công nghệ thông tin).
# Chỗ tô vàng là chỗ nhóm cần tự điền (giống tệp mẫu); điền xong thì bỏ tô vàng: Home -> Text Highlight Color -> No Color.
_NOW = datetime.date.today()
_THANG = f"tháng {_NOW.month:02d}/{_NOW.year}"
_FRAME_W, _FRAME_IND = 10835, -815                       # khung viền kép rộng 19,1 cm, nhô ra ngoài lề trái 1,4 cm như mẫu
_LOGO = O / "bia_logo.jpeg"
_HOLE = WD_COLOR_INDEX.YELLOW
_AFTER_PBDR = ("w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap", "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN", "w:bidi",
               "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind", "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc", "w:textDirection",
               "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl", "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange")


def _el(tag, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn("w:" + k), str(v))
    return e


class _CellText:
    """Viết lần lượt các đoạn vào một ô; định dạng đặt rõ từng đoạn để không phụ thuộc kiểu Normal của báo cáo."""

    def __init__(self, cell):
        self.cell, self.n = cell, 0

    def par(self, parts, size, bold=True, italic=False, align=CENTER, before=0, after=8, line=1.0, left=None):
        p = self.cell.paragraphs[0] if self.n == 0 else self.cell.add_paragraph()
        self.n += 1
        if isinstance(parts, str):
            parts = [(parts, False)]
        p.alignment = align
        f = p.paragraph_format
        f.space_before, f.space_after, f.line_spacing = Pt(before), Pt(after), line
        if left is not None:
            f.left_indent = Cm(left)
        for txt, hole in parts:
            r = p.add_run(txt)
            r.font.size, r.bold, r.italic = Pt(size), bold, italic
            if hole:
                r.font.highlight_color = _HOLE
        return p


def _frame(heights_cm):
    """Khung viền kép của một trang bìa: bảng một cột, mỗi phần tử của heights_cm là chiều cao (tối thiểu) của một hàng."""
    t = d.add_table(rows=len(heights_cm), cols=1)
    pr = t._tbl.tblPr
    for ch in list(pr):
        pr.remove(ch)
    pr.append(_el("w:tblW", w=_FRAME_W, type="dxa"))
    pr.append(_el("w:tblInd", w=_FRAME_IND, type="dxa"))
    bd = _el("w:tblBorders")
    for side in ("top", "left", "bottom", "right"):
        bd.append(_el("w:" + side, val="thinThickSmallGap", sz=24, space=0, color="auto"))
    for side in ("insideH", "insideV"):
        bd.append(_el("w:" + side, val="nil"))
    pr.append(bd)
    pr.append(_el("w:tblLayout", type="fixed"))
    pr.append(_el("w:tblLook", val="0000", firstRow=0, lastRow=0, firstColumn=0, lastColumn=0, noHBand=0, noVBand=0))
    t.columns[0].width = Twips(_FRAME_W)
    for row, h in zip(t.rows, heights_cm):
        row.height, row.height_rule = Cm(h), WD_ROW_HEIGHT_RULE.AT_LEAST
        row._tr.get_or_add_trPr().append(_el("w:cantSplit"))
        row.cells[0].width = Twips(_FRAME_W)
    return t


def _bottom_border():
    b = _el("w:pBdr")
    b.append(_el("w:bottom", val="single", sz=6, space=1, color="auto"))
    return b


def _cover_page(city):
    t = _frame([21.4, 2.0])                               # hàng 1: nội dung; hàng 2: dòng địa điểm, thời gian ở sát đáy khung (tổng 23,4 cm < 23,94 cm vùng chữ)
    c = _CellText(t.rows[0].cells[0])
    c.par("HỌC VIỆN HÀNG KHÔNG VIỆT NAM", 18)
    c.par("KHOA CÔNG NGHỆ THÔNG TIN", 14, after=0)
    ln = c.par("", 3, after=6, line=Pt(5))                # đường kẻ ngắn dưới tên khoa: viền dưới của một đoạn rỗng thụt vào hai bên
    ln.paragraph_format.left_indent = ln.paragraph_format.right_indent = Cm(6.5)
    ln._p.get_or_add_pPr().insert_element_before(_bottom_border(), *_AFTER_PBDR)
    lg = c.par("", 12, before=13, after=0)          # Word và LibreOffice lấy khoảng cách lớn hơn giữa "sau" của đoạn trên và "trước" của đoạn dưới, không cộng dồn
    if _LOGO.exists():
        lg.add_run().add_picture(str(_LOGO), width=Cm(4.55))
    else:
        print("thiếu logo, bỏ qua:", _LOGO)
    c.par("BÁO CÁO", 24, before=14)
    c.par("HỌC MÁY", 20)                                  # tên học phần
    c.par("PHÂN LOẠI TIN TỨC TIẾNG VIỆT", 18, after=0)     # tên đề tài
    info = dict(size=14, align=LEFT, left=1.36, line=2.0)
    c.par([("Giảng viên hướng dẫn:", False), ("…" * 23 + "..", True)], before=79, **info)
    c.par([("Sinh viên/ Nhóm sinh viên thực hiện: Nhóm ", False), ("xx", True), ("…" * 13, False)], **info)
    c.par([("Mã số sinh viên:", False), ("…" * 26 + ".", True)], **info)
    c.par([("Lớp: ", False), ("0101000xxxxx", True), ("…" * 25, False)], **info)
    row2 = t.rows[1].cells[0]
    row2.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    _CellText(row2).par(f"{city}, {_THANG}", 14, after=0)


def _tiny(break_before):
    """Đoạn cao 1 pt đặt giữa hai bảng; page_break_before đẩy bảng phía sau sang trang mới mà không để lại dòng trống."""
    p = d.add_paragraph()
    f = p.paragraph_format
    f.space_before = f.space_after = Pt(0)
    f.line_spacing = Pt(1)
    f.page_break_before = break_before
    return p


def _grid(rows, widths_tw, ind_tw):
    """Bảng có kẻ ô, rộng tổng widths_tw (đơn vị twip), thụt ind_tw so với lề trái như tệp mẫu."""
    t = d.add_table(rows=rows, cols=len(widths_tw))
    t.style = "Table Grid"
    t.autofit = False
    pr = t._tbl.tblPr
    pr.find(qn("w:tblW")).set(qn("w:w"), str(sum(widths_tw)))
    pr.find(qn("w:tblW")).set(qn("w:type"), "dxa")
    pr.insert_element_before(_el("w:tblInd", w=ind_tw, type="dxa"), "w:tblBorders", "w:shd", "w:tblLayout", "w:tblCellMar", "w:tblLook", "w:tblCaption", "w:tblDescription")
    for i, wd in enumerate(widths_tw):
        t.columns[i].width = Twips(wd)
        for row in t.rows:
            row.cells[i].width = Twips(wd)
    for row in t.rows:
        row._tr.get_or_add_trPr().append(_el("w:cantSplit"))
    return t


_cover_page("TP. Hồ Chí Minh")                            # bìa chính
_tiny(True)
_cover_page("Thành phố Hồ Chí Minh")                      # bìa phụ

_ds = d.add_paragraph()                                   # trang 3: danh sách nhóm và ô chữ ký của cán bộ chấm thi
_ds.paragraph_format.page_break_before = True
_ds.paragraph_format.line_spacing, _ds.paragraph_format.space_before, _ds.paragraph_format.space_after = 1.5, Pt(0), Pt(8)
_ds.alignment = LEFT
_dr = _ds.add_run("Danh sách Nhóm:"); _dr.bold = True; _dr.font.size = Pt(14)
_gt = _grid(6, [876, 3104, 1906, 2194, 2410], -714)
for _j, _h in enumerate(["STT", "Họ và tên", "MSSV", "Lớp", "Ghi chú"]):
    _CellText(_gt.rows[0].cells[_j]).par(_h, 14, after=0)
for _i in range(1, 6):
    _gt.rows[_i].height, _gt.rows[_i].height_rule = Twips(567), WD_ROW_HEIGHT_RULE.AT_LEAST
    for _j, (_v, _hole) in enumerate([(str(_i), False), ("…", True), ("…", True), ("…", True), ("Nhóm trưởng" if _i == 1 else "", False)]):
        _gt.rows[_i].cells[_j].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        _CellText(_gt.rows[_i].cells[_j]).par([(_v, _hole)], 14, bold=False, after=0)
_sp = d.add_paragraph(); _sp.paragraph_format.space_after = Pt(6); _sp.paragraph_format.line_spacing = 1.0
_cb = _grid(2, [5329, 5329], -714)
for _i, _row in enumerate(_cb.rows):
    _row.height, _row.height_rule = Twips(3402), WD_ROW_HEIGHT_RULE.AT_LEAST
    for _cell, _who in zip(_row.cells, (["Cán bộ chấm thi 1", "Cán bộ chấm thi 2"], ["Cán bộ chấm thi phúc khảo 1", "Cán bộ chấm thi phúc khảo 2"])[_i]):
        _ct = _CellText(_cell)
        _ct.par(_who, 14, after=0)
        _ct.par("(ký và ghi rõ họ tên)", 14, bold=False, italic=True, after=0)

# phần thân báo cáo: sang trang mới, có đầu trang, số trang đánh lại từ 1 ở trang Tóm tắt; các trang bìa không có đầu / chân trang và không đánh số
_sec2 = d.add_section(WD_SECTION.NEW_PAGE)
_sec2._sectPr.insert_element_before(_el("w:pgNumType", start=1), "w:cols", "w:formProt", "w:vAlign", "w:noEndnote", "w:titlePg", "w:textDirection", "w:bidi", "w:rtlGutter", "w:docGrid", "w:printerSettings")
_sec2.footer.is_linked_to_previous = False
_sec2.header.is_linked_to_previous = False
_fp = _sec2.footer.paragraphs[0]; _fp.alignment = CENTER; _fld(_fp, "PAGE")
_hp = _sec2.header.paragraphs[0]; _hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
_hr = _hp.add_run("Đồ án môn Học máy — Phân loại tin tức tiếng Việt"); _hr.italic = True; _hr.font.size = Pt(10.5)

# ================================================================== tóm tắt
H("Tóm tắt")
P(f"Đề tài xây dựng hệ thống học máy tự động phân loại bài báo tiếng Việt vào {m['n_classes']} chuyên mục, chạy trên CPU, không cần GPU hay mô hình ngôn ngữ lớn. "
  f"Dữ liệu gồm {th(m['n_samples'])} bài báo (mỗi chuyên mục 500 bài), chia phân tầng 70/15/15. Văn bản được biểu diễn bằng TF-IDF (đơn từ và cặp từ, tối đa 200.000 đặc trưng) và phân loại bằng Linear SVM. "
  f"Sau khi chỉnh tham số công bằng cho 6 thuật toán bằng cross-validation 5-fold, mô hình đạt Accuracy {pc(m['test_accuracy'])} và Macro-F1 {vn(m['test_macro_f1'], 3)} trên {m['test_size']} bài kiểm thử chưa từng dùng khi huấn luyện; "
  f"kết quả ổn định khi chia lại dữ liệu ({vn(sv0.split_acc_mean * 100, 1)}% ± {vn(sv0.split_acc_std * 100, 1)} trên 10 lần chia).")
P(f"Ngoài độ chính xác, nhóm hiệu chỉnh độ tự tin của mô hình (sai lệch ECE giảm từ {pc(c0.ECE)} xuống {pc(c1.ECE)}), kiểm chứng rằng lời giải thích dự đoán phản ánh đúng quyết định của mô hình, "
  f"và đề xuất dự đoán có bảo đảm bằng conformal prediction: ở mức 95%, AI nêu trung bình {vn(cprod['0.05']['avg_size'], 2)} chuyên mục mỗi bài và chuyên mục đúng nằm trong danh sách ở {pc(cprod['0.05']['coverage'])} bài kiểm thử. "
  "Mô hình được đóng gói thành website tin tức VnNews gồm phân loại trực tiếp, Hỏi AI có dẫn nguồn, tìm kiếm nâng cao, bộ sưu tập và bình luận của bạn đọc.")
_kp = P("Từ khóa: phân loại văn bản, TF-IDF, SVM tuyến tính, tiếng Việt, hiệu chỉnh độ tin cậy, conformal prediction.")
_kp.runs[0].italic = True
d.add_page_break()

# ================================================================== mục lục (điền ở cuối tệp, sau khi biết hết các đề mục)
_mt = _center("MỤC LỤC", 16, True, after=12)
_TOC = d.add_paragraph("@@TOC@@")
d.add_page_break()

# ================================================================== 1
H("1. Giới thiệu")
H("1.1 Bối cảnh và bài toán", 2)
P("Mỗi ngày các trang báo điện tử đăng hàng nghìn bài viết. Việc gán chủ đề (giáo dục, sức khỏe, thể thao, pháp luật...) thủ công tốn nhiều thời gian. "
  "Đề tài xây dựng hệ thống học máy tự động phân loại bài báo tiếng Việt vào 11 chủ đề dựa trên nội dung văn bản.")
P("Bài toán được phát biểu như sau: cho văn bản của một bài báo (tiêu đề, sapo và nội dung), dự đoán chuyên mục của bài trong tập 11 chuyên mục gồm Thời sự, Thế giới, Kinh doanh, Pháp luật, Giáo dục, Sức khỏe, Khoa học, Đời sống, Giải trí, Thể thao và Xe. "
  "Đây là bài toán phân loại văn bản đa lớp (mỗi bài đúng một nhãn) theo hướng học có giám sát.")
H("1.2 Mục tiêu", 2)
P("Mục tiêu: (1) xây dựng pipeline tiền xử lý – trích xuất đặc trưng – huấn luyện; (2) so sánh công bằng một số thuật toán học máy cổ điển (mỗi mô hình đều được chỉnh tham số bằng cùng một quy trình); "
  "(3) đánh giá bằng Accuracy, Precision, Recall, F1 kèm khoảng tin cậy, kiểm định thống kê, độ ổn định khi chia lại dữ liệu và ablation; (4) giải thích được vì sao mô hình chọn chủ đề, biết độ tin cậy của dự đoán và nêu được tập chuyên mục có bảo đảm thống kê khi bài mơ hồ; "
  "(5) cung cấp chương trình chạy được trên máy cấu hình thấp (CPU, không cần GPU hay mô hình ngôn ngữ lớn) và đóng gói thành website tin tức.")
H("1.3 Các nghiên cứu liên quan", 2)
P("Biểu diễn văn bản bằng TF-IDF (Salton và Buckley, 1988) kết hợp máy vector hỗ trợ tuyến tính (Cortes và Vapnik, 1995; Joachims, 1998) là đường cơ sở mạnh và phổ biến cho phân loại văn bản thưa, nhiều chiều. "
  "Với tiếng Việt, Hoàng và cộng sự (2007) so sánh nhiều phương pháp phân loại trên bộ dữ liệu tin tức VNTC. Các mô hình ngôn ngữ tiền huấn luyện cho tiếng Việt như PhoBERT (Nguyen và Nguyen, 2020) thường được báo cáo cho kết quả tốt trên nhiều tác vụ nhưng cần nhiều tài nguyên tính toán hơn (thường là GPU), "
  "còn việc tách từ tiếng Việt có thể dùng VnCoreNLP (Vu và cs., 2018) hoặc pyvi. Đề tài chọn hướng nhẹ hơn: TF-IDF + SVM chạy trên CPU, và dành công sức cho việc đánh giá nghiêm túc cùng các chức năng làm cho kết quả dùng được trong thực tế "
  "(độ tin cậy, giải thích, bảo đảm thống kê, website).")
H("1.4 Đóng góp của đề tài", 2)
B(["So sánh công bằng 6 thuật toán (mỗi thuật toán được chỉnh tham số bằng cùng một quy trình), kèm kiểm định thống kê, khoảng tin cậy, độ ổn định khi chia lại dữ liệu, ablation và đường cong học (mục 4).",
   "Hiệu chỉnh độ tự tin của mô hình và dự đoán có chọn lọc (mục 4.6).",
   "Dự đoán có bảo đảm bằng conformal prediction: AI nêu tập chuyên mục có độ phủ thống kê khi bài mơ hồ (mục 4.7).",
   "Phân tích lỗi định lượng và định tính (mục 5).",
   "Giải thích dự đoán bằng phân rã mô hình tuyến tính và kiểm chứng độ trung thực của lời giải thích (mục 6.4).",
   "Website tin tức VnNews: phân loại trực tiếp, Hỏi AI có dẫn nguồn, tìm kiếm nâng cao, bộ sưu tập, bình luận (mục 6).",
   f"Mã nguồn có kiểm thử tự động ({N_FEAT + N_CMT} bài kiểm tra) và mọi thí nghiệm đều chạy lại được (phụ lục C)."])
H("1.5 Bố cục báo cáo", 2)
P("Phần 2 mô tả dữ liệu; phần 3 trình bày cơ sở lý thuyết và phương pháp; phần 4 là các kết quả thực nghiệm; phần 5 phân tích lỗi; phần 6 giới thiệu website và các chức năng mở rộng; phần 7 nêu hạn chế và hướng phát triển; "
  "phần 8 hướng dẫn chạy; phần 9 là kết luận; phần 10 là phân công công việc của nhóm. Cuối báo cáo có tài liệu tham khảo và các phụ lục.")
IMG("he_thong.png", "Sơ đồ tổng thể của hệ thống. Mô hình chọn bằng cross-validation 5-fold trên 3.850 bài huấn luyện; kết quả cuối đo trên 825 bài kiểm thử chưa từng dùng.", 13.8, O, key="he_thong")

# ================================================================== 2
H("2. Dữ liệu")
H("2.1 Nguồn và mô tả dữ liệu", 2)
PH([("Nguồn dữ liệu: ", False), ("[nhóm điền: tên trang báo hoặc bộ dữ liệu, thời gian và cách thu thập, giấy phép sử dụng]", True),
    (f". Bộ dữ liệu gồm {th(m['n_samples'])} bài báo tiếng Việt, {m['n_classes']} chủ đề, mỗi chủ đề 500 bài (cân bằng). "
     "Mỗi mẫu có tiêu đề, mô tả (sapo), nội dung và nhãn là chuyên mục của bài trên trang báo gốc (riêng chuyên mục “Khoa học công nghệ” của trang gốc được gọi gọn là “Khoa học”). "
     "Văn bản đầu vào của mô hình = tiêu đề + mô tả + nội dung.", False)])
CAP("Thống kê bộ dữ liệu")
TABLE(pd.DataFrame([["Số bài báo", th(m["n_samples"])], ["Số chuyên mục", f"{m['n_classes']} (mỗi chuyên mục 500 bài)"],
                    ["Số từ mỗi bài (tiêu đề + sapo + nội dung)", f"trung bình {th(round(_w.mean()))}; trung vị {th(round(_w.median()))}; nhỏ nhất {th(_w.min())}; lớn nhất {th(_w.max())}"],
                    ["Số từ trung bình của tiêu đề / sapo", f"{vn(DATA.title.str.split().str.len().mean(), 1)} / {vn(DATA.description.str.split().str.len().mean(), 1)}"],
                    ["Chia tập (phân tầng, random_state = 42)", "huấn luyện 3.850 / kiểm định 825 / kiểm thử 825"]], columns=["Mục", "Giá trị"]), widths=[7.5, 8.5])
_ex = DATA[DATA.id == 240151].iloc[0] if (DATA.id == 240151).any() else DATA.iloc[0]
CAP("Ví dụ một mẫu dữ liệu")
TABLE(pd.DataFrame([["id", str(_ex.id)], ["Tiêu đề", _ex.title], ["Sapo", _ex.description[:220] + ("…" if len(_ex.description) > 220 else "")],
                    ["Nội dung", _ex.content[:160].replace("\n", " ") + f"… (khoảng {th(len(_ex.content.split()))} từ)"], ["Nhãn", _ex.ground_truth]], columns=["Trường", "Nội dung"]), widths=[3, 13])
IMG("phan_bo_nhan.png", "Phân bố số bài theo chủ đề", 12)
IMG("do_dai_bai.png", "Phân bố độ dài bài báo", 12)
H("2.2 Chia dữ liệu", 2)
P("Dữ liệu chia phân tầng (stratified) theo tỉ lệ 70% huấn luyện (3.850) / 15% kiểm định (825) / 15% kiểm thử (825), random_state=42. Không có bài trùng hoàn toàn văn bản.")
H("2.3 Kiểm tra rò rỉ do bài gần giống nhau", 2)
P("Với mỗi bài kiểm thử, chúng em tính độ giống cosine (TF-IDF) lớn nhất với các bài huấn luyện. "
  f"Trung vị {vn(nd['median'], 2)}, phân vị 90% là {vn(nd['p90'], 2)}, lớn nhất {vn(nd['max'], 2)}; chỉ {nd['n_ge_0.5']}/{nd['n_test']} bài có độ giống từ 0,5 trở lên (mô hình đoán đúng cả {nd['n_ge_0.5']} bài này) "
  f"và độ chính xác trên các bài còn lại là {pc(nd['acc_lt_0.5'])}. Vì vậy kết quả kiểm thử không bị thổi phồng bởi các bài gần trùng.")

# ================================================================== 3
H("3. Cơ sở lý thuyết và phương pháp")
H("3.1 Tiền xử lý", 2)
B(["Chuẩn hóa Unicode NFC, chuyển chữ thường.", "Loại bỏ URL, email, chữ số và dấu câu; giữ nguyên dấu tiếng Việt.", "Gộp khoảng trắng; loại mẫu quá ngắn và mẫu trùng lặp."])
H("3.2 Biểu diễn văn bản bằng TF-IDF", 2)
P("Máy tính không đọc được chữ nên mỗi bài được chuyển thành một vector số. TF-IDF gán cho mỗi từ (hoặc cặp từ) t trong bài d một trọng số tăng theo số lần t xuất hiện trong d (tf) và giảm theo số bài có chứa t (df):")
FORMULA("tf-idf(t, d) = (1 + ln tf(t, d)) × idf(t),      idf(t) = ln[(1 + n) / (1 + df(t))] + 1")
P("trong đó n là tổng số bài. Dạng 1 + ln tf (tùy chọn sublinear_tf) giúp một từ lặp 20 lần không áp đảo từ lặp 2 lần; idf làm giảm trọng số của những từ có mặt ở hầu hết các bài (“của”, “và”, “những”) "
  "và tăng trọng số của những từ đặc trưng cho ít chủ đề (“cầu thủ”, “bị cáo”, “lãi suất”). Vector của mỗi bài được chuẩn hóa độ dài L2 để bài dài và bài ngắn so sánh được với nhau.")
P("Cấu hình dùng trong đề tài: unigram + bigram (bigram giúp bắt cụm từ tiếng Việt như “học sinh”, “ngân hàng”, “diễn viên”), min_df=2, max_df=0.9, sublinear_tf=True, tối đa 200.000 đặc trưng.")
H("3.3 Linear SVM và các mô hình so sánh", 2)
P("Linear SVM (máy vector hỗ trợ tuyến tính) học, cho mỗi chuyên mục k, một vector trọng số w_k và hệ số b_k sao cho điểm s_k(x) = w_k · x + b_k cao với bài thuộc k và thấp với bài còn lại (chiến lược một-chống-tất-cả). "
  "Với mỗi k, mô hình tìm siêu phẳng có biên rộng nhất, đồng thời phạt các bài nằm sai phía hoặc quá gần siêu phẳng:")
FORMULA("min  ½ · ||w||²  +  C · Σ_i max(0, 1 − y_i · (w · x_i + b))²")
P("Dự đoán là chuyên mục có điểm cao nhất, ŷ = argmax_k s_k(x). Hệ số C cân bằng giữa biên rộng (C nhỏ, chính quy hóa mạnh) và khớp chặt dữ liệu học (C lớn); đề tài chọn C = 2 bằng cross-validation. "
  "Vì điểm của mỗi chuyên mục là tổng tuyến tính (trọng số × TF-IDF) nên có thể tách chính xác đóng góp của từng từ vào quyết định (mục 6.4). Các mô hình được đưa vào so sánh:")
B(["Đường cơ sở: luôn đoán chủ đề phổ biến nhất (chỉ đúng 9,1% vì 11 chủ đề cân bằng).",
   "Complement Naive Bayes – nhanh, phù hợp văn bản.", "k-NN với độ đo cosine.", "Logistic Regression.",
   "Linear SVM (LinearSVC) – thường mạnh nhất với TF-IDF thưa, nhiều chiều.", "Random Forest.",
   "Mạng nơ-ron nhỏ: TF-IDF → giảm chiều SVD 300 → MLP 256 nơ-ron (chạy được trên CPU)."])
H("3.4 Các chỉ số đánh giá", 2)
B(["Accuracy = số bài đoán đúng / tổng số bài.",
   "Precision của chuyên mục k = TP_k / (TP_k + FP_k): trong số bài AI xếp vào k, bao nhiêu bài thật sự thuộc k.",
   "Recall của chuyên mục k = TP_k / (TP_k + FN_k): trong số bài thật sự thuộc k, AI tìm ra được bao nhiêu bài.",
   "F1_k = 2 · P_k · R_k / (P_k + R_k); Macro-F1 là trung bình cộng F1 của 11 chuyên mục (mỗi chuyên mục một trọng số như nhau, nên chuyên mục khó không bị che khuất bởi chuyên mục dễ).",
   "Ma trận nhầm lẫn: ô (i, j) là số bài thật sự thuộc chuyên mục i nhưng bị xếp vào chuyên mục j; đường chéo là các bài đúng.",
   "Cross-validation 5-fold: chia tập huấn luyện thành 5 phần, lần lượt dùng mỗi phần để kiểm tra mô hình huấn luyện trên 4 phần còn lại; dùng để chọn mô hình và tham số mà không đụng đến tập kiểm thử.",
   "Kiểm định McNemar và bootstrap: so sánh hai mô hình trên cùng tập kiểm thử (chỉ xét các bài hai mô hình trả lời khác nhau) và ước lượng khoảng tin cậy 95% bằng lấy mẫu lại.",
   "ECE (sai lệch hiệu chỉnh) = Σ_b (n_b / n) · |độ chính xác_b − độ tự tin_b|, tính trên 10 nhóm độ tự tin: càng nhỏ thì phần trăm AI hiển thị càng sát tỉ lệ đúng thật."])
H("3.5 Quy trình đánh giá và chống rò rỉ", 2)
B(["Tập kiểm thử (825 bài) chỉ dùng để báo cáo kết quả cuối; mọi việc chọn mô hình và tham số chỉ dùng cross-validation 5-fold trên tập huấn luyện (3.850 bài).",
   "TF-IDF được học lại trong từng fold bằng Pipeline nên không rò rỉ thông tin từ fold kiểm tra.",
   "Ablation dùng 5-fold CV trên huấn luyện + kiểm định (4.675 bài), không dùng tập kiểm thử.",
   "Mọi thí nghiệm nằm trong thư mục experiments/ và chạy lại được; kết quả lưu ở outputs/experiments/."])


# ------------------------------------------------------------------ 4
H("4. Kết quả thực nghiệm")
H("4.1 So sánh mô hình công bằng", 2)
P("Lần so sánh nhanh đầu tiên (train.py) dùng tham số cố định cho cả bốn mô hình và chỉ tinh chỉnh riêng Linear SVM, nên có thể thiên vị mô hình được chọn. "
  "Vì vậy chúng em làm lại: mỗi mô hình đều được chỉnh siêu tham số bằng GridSearchCV 5-fold (Macro-F1) trên tập huấn luyện; khi tham số tốt nhất nằm ở biên lưới thì mở rộng lưới (Logistic Regression: C đến 300; Linear SVM: C từ 0,1 đến 64). "
  "Tập kiểm định và kiểm thử không tham gia chọn tham số.")
tt = tun[~tun.model.str.startswith("Đoán")].sort_values("cv_macro_f1_mean", ascending=False)
tb = pd.DataFrame({"Mô hình": tt.model.str.replace(r" \(TF-IDF.*", "", regex=True), "Macro-F1 CV (5-fold)": [f"{vn(a, 3)} ± {vn(b, 3)}" for a, b in zip(tt.cv_macro_f1_mean, tt.cv_macro_f1_std)],
                   "Macro-F1 kiểm định": [vn(x, 3) for x in tt.val_macro_f1], "Accuracy kiểm thử": [vn(x, 3) for x in tt.test_acc],
                   "Huấn luyện (s)": [vn(x, 0) for x in tt.fit_sec], "Kích thước (MB)": [vn(x, 1) for x in tt.model_mb]})
CAP("So sánh các mô hình sau khi chỉnh tham số công bằng (5-fold CV trên tập huấn luyện; Accuracy đo trên tập kiểm thử)")
TABLE(tb)
base_row = tun[tun.model.str.startswith("Đoán")].iloc[0]
P(f"Đường cơ sở (đoán chủ đề phổ biến nhất) chỉ đạt Accuracy {pc(base_row.test_acc)}. Linear SVM có Macro-F1 CV cao nhất ({vn(float(tt.iloc[0].cv_macro_f1_mean), 4)}) nhưng chỉ nhỉnh Logistic Regression ({vn(float(tt.iloc[1].cv_macro_f1_mean), 4)}); "
  f"so với lần so sánh nhanh ban đầu (SVM hơn Logistic Regression khoảng 1,3 điểm phần trăm trên tập kiểm định) thì khoảng cách gần như biến mất khi Logistic Regression được chỉnh C công bằng. "
  f"Với Linear SVM, Macro-F1 CV gần như phẳng khi C từ 1 đến 64 ({vn(svmj['plateau_cv_min'], 4)} – {vn(svmj['plateau_cv_max'], 4)}); C tốt nhất là {svmj['best_C']} nhưng chỉ hơn C = 2 khoảng {vn((svmj['best_cv'] - svmj['chosen_cv']) * 100, 2)} điểm, "
  "nhỏ hơn độ lệch chuẩn giữa các fold (0,41 điểm) nên giữ C = 2 (đơn giản, chính quy hóa mạnh hơn).")
IMG("tuning_results.png", "Kết quả chỉnh tham số 5-fold CV của các mô hình", 14, E)
H("Kiểm định thống kê giữa các mô hình", 3)
P("Trên cùng 825 bài kiểm thử, chúng em so sánh từng cặp bằng kiểm định McNemar (xét các bài mà hai mô hình trả lời khác nhau) và khoảng tin cậy 95% bootstrap (2.000 lần lấy mẫu lại) cho chênh lệch Accuracy.")
sg = pd.DataFrame({"So Linear SVM với": sig.vs.str.replace(r" \(TF-IDF.*", "", regex=True), "Chỉ SVM đúng": sig.svm_only_right.astype(str), "Chỉ mô hình kia đúng": sig.other_only_right.astype(str),
                   "p (McNemar)": [pv(x) for x in sig.mcnemar_p], "Chênh Accuracy, điểm % [95% CI]": [f"{vn(a * 100, 1)} [{vn(b * 100, 1)}; {vn(c * 100, 1)}]" for a, b, c in zip(sig.acc_diff, sig.diff_lo, sig.diff_hi)]})
CAP("Kiểm định McNemar và khoảng tin cậy 95% của chênh lệch Accuracy giữa Linear SVM và các mô hình khác (825 bài kiểm thử)")
TABLE(sg)
P("Kết luận: Linear SVM tốt hơn có ý nghĩa thống kê so với k-NN và Random Forest (p < 0,05), nhưng không tách khỏi Logistic Regression, Complement Naive Bayes và MLP nhỏ (p > 0,1). "
  "Chúng em chọn Linear SVM vì có điểm trung bình cao nhất, huấn luyện nhanh hơn Logistic Regression khoảng 4 lần, file mô hình nhỏ (15,9 MB) và là mô hình tuyến tính nên giải thích được trực tiếp (mục 6.4), "
  "chứ không khẳng định nó vượt trội hơn Logistic Regression.")

H("4.2 Kết quả cuối trên tập kiểm thử", 2)
P(f"Trên {m['test_size']} mẫu kiểm thử (chưa từng dùng khi huấn luyện/chọn mô hình): Accuracy = {vn(m['test_accuracy'], 4)} ({int(round(m['test_accuracy'] * m['test_size']))}/{m['test_size']} bài), Macro-F1 = {vn(m['test_macro_f1'], 4)}. "
  f"Khoảng tin cậy 95% (bootstrap) cho Accuracy là [{pc(ci['acc_lo'])}; {pc(ci['acc_hi'])}] và cho Macro-F1 là [{vn(ci['f1_lo'], 3)}; {vn(ci['f1_hi'], 3)}]. "
  "Ba con số Macro-F1 gần nhau (CV 5-fold 0,884; kiểm định 0,886; kiểm thử 0,893), không thấy dấu hiệu chọn mô hình quá khớp vào tập kiểm định. "
  "Lưu ý: độ chính xác trên tập huấn luyện là 100% (SVM trong không gian 200.000 chiều tách hết dữ liệu học), nên điều đáng tin là kết quả trên dữ liệu chưa thấy.")
r = rep.loc[[i for i in rep.index if i not in ("accuracy", "macro avg", "weighted avg")], ["precision", "recall", "f1-score", "support"]].reset_index()
CAP("Precision, Recall và F1 của từng chủ đề trên tập kiểm thử")
r.columns = ["Chủ đề", "Precision", "Recall", "F1", "Số mẫu"]; r["Số mẫu"] = r["Số mẫu"].astype(int).astype(str); TABLE(r, "{:.3f}")
IMG("ma_tran_nham_lan.png", "Ma trận nhầm lẫn trên tập kiểm thử", 13.5)

H("4.3 Độ ổn định khi chia lại dữ liệu", 2)
P("Kết quả trên một lần chia dữ liệu có thể may rủi. Chúng em lặp lại phép chia 70/15/15 với 10 hạt giống ngẫu nhiên khác nhau (seed 0–9), huấn luyện lại và đo trên tập kiểm thử của mỗi lần chia; "
  "ngoài ra chạy 5-fold CV lặp 3 lần trên toàn bộ 5.500 bài.")
sb = pd.DataFrame({"Mô hình": stab.model, "Accuracy (10 lần chia)": [f"{vn(a * 100, 2)} ± {vn(b * 100, 2)}" for a, b in zip(stab.split_acc_mean, stab.split_acc_std)],
                   "Macro-F1 (10 lần chia)": [f"{vn(a, 4)} ± {vn(b, 4)}" for a, b in zip(stab.split_f1_mean, stab.split_f1_std)],
                   "Nhỏ nhất – lớn nhất": [f"{vn(a, 3)} – {vn(b, 3)}" for a, b in zip(stab.split_f1_min, stab.split_f1_max)],
                   "Macro-F1 (CV 5-fold × 3)": [f"{vn(a, 4)} ± {vn(b, 4)}" for a, b in zip(stab.cv_f1_mean, stab.cv_f1_std)]})
CAP("Độ ổn định khi chia lại dữ liệu (10 lần chia và 5-fold CV lặp 3 lần)")
TABLE(sb)
sv_ = stab[stab.model == "Linear SVM"].iloc[0]
P(f"Linear SVM đạt Accuracy {vn(sv_.split_acc_mean * 100, 2)}% ± {vn(sv_.split_acc_std * 100, 2)} trên 10 lần chia, kết quả chính thức ({pc(m['test_accuracy'], 2)}) nằm trong dải này. "
  f"Trong {int((sp[sp.model == 'Linear SVM'].set_index('seed').macro_f1 > sp[sp.model == 'Logistic Regression'].set_index('seed').macro_f1).sum())}/10 lần chia Linear SVM có Macro-F1 cao hơn Logistic Regression, nhưng chênh lệch nhỏ (cùng cỡ độ lệch chuẩn). "
  "Complement Naive Bayes dao động nhiều hơn hẳn (độ lệch chuẩn gấp đôi).")
IMG("stability.png", "Macro-F1 trên tập kiểm thử của 10 phép chia ngẫu nhiên", 13, E)

H("4.4 Ablation: từng thành phần đóng góp bao nhiêu?", 2)
P("Mỗi lần chỉ đổi một thành phần so với cấu hình chuẩn, đo bằng 5-fold CV trên huấn luyện + kiểm định (không dùng tập kiểm thử); p là kiểm định t ghép cặp trên 5 fold (ít fold nên kiểm định có độ mạnh thấp: “chưa có ý nghĩa” không có nghĩa là “không có tác dụng”).")
sel = [("Cấu hình chuẩn", "Cấu hình chuẩn (TF-IDF 1–2 gram, log-tf, IDF, tiêu đề + sapo + nội dung)"), ("Chỉ tiêu đề", "Chỉ dùng tiêu đề"), ("Tiêu đề + sapo", "Tiêu đề + sapo"), ("Chỉ nội dung", "Chỉ dùng nội dung"),
       ("Chỉ từ đơn (1-gram)", "Chỉ từ đơn (bỏ cặp từ)"), ("1–3 gram", "Thêm bộ ba từ (1–3 gram)"), ("Bỏ log-tf (sublinear_tf=False)", "Bỏ log-tf"), ("Bỏ IDF (chỉ TF)", "Bỏ IDF"),
       ("Tối đa 5.000 đặc trưng", "Chỉ giữ 5.000 từ"), ("Tối đa 20.000 đặc trưng", "Chỉ giữ 20.000 từ"), ("min_df = 5", "Loại từ hiếm hơn (min_df = 5)"), ("Bỏ dấu tiếng Việt", "Bỏ dấu tiếng Việt"),
       ("Tách từ (pyvi) + 1–2 gram", "Tách từ pyvi + 1–2 gram")]
ab = pd.DataFrame({"Biến thể": [b for _, b in sel], "Macro-F1 (%)": [f"{vn(abl.loc[a, 'macro_f1_mean'] * 100, 2)} ± {vn(abl.loc[a, 'macro_f1_std'] * 100, 2)}" for a, _ in sel],
                   "Chênh so với chuẩn (điểm %)": ["—" if a == "Cấu hình chuẩn" else f"{abl.loc[a, 'delta_vs_base'] * 100:+.2f}".replace(".", ",") for a, _ in sel],
                   "p (t ghép cặp)": ["—" if a == "Cấu hình chuẩn" else pv(abl.loc[a, "paired_t_p"]) for a, _ in sel]})
CAP("Kết quả ablation (5-fold CV, không dùng tập kiểm thử)")
TABLE(ab)
IMG("ablation.png", "Ablation (5-fold CV, không dùng tập kiểm thử)", 15, E)
B([f"Nội dung bài báo là phần quan trọng nhất: chỉ dùng tiêu đề chỉ đạt Macro-F1 {vn(abl.loc['Chỉ tiêu đề', 'macro_f1_mean'] * 100, 1)}%, tiêu đề + sapo đạt {vn(abl.loc['Tiêu đề + sapo', 'macro_f1_mean'] * 100, 1)}%, "
   f"trong khi chỉ dùng nội dung ({vn(abl.loc['Chỉ nội dung', 'macro_f1_mean'] * 100, 1)}%) đã ngang cấu hình đầy đủ ({vn(abl.loc['Cấu hình chuẩn', 'macro_f1_mean'] * 100, 1)}%).",
   "Cặp từ (bigram), log-tf và vốn từ đủ lớn đều đóng góp có ý nghĩa thống kê (bỏ đi làm Macro-F1 giảm 0,76 – 1,03 điểm, p < 0,05); từ 20.000 đặc trưng trở lên không còn khác biệt.",
   "Bỏ IDF giảm 0,49 điểm nhưng chưa có ý nghĩa (p = 0,10); bỏ dấu tiếng Việt giảm 0,22 điểm (p = 0,27).",
   "Tách từ bằng pyvi và thêm bộ ba từ chỉ tăng 0,13 – 0,24 điểm, chưa có ý nghĩa (p = 0,24 và 0,33) nên không đưa vào mô hình chính."])

H("4.5 Đường cong học", 2)
P("Huấn luyện Linear SVM trên các phần ngày càng lớn của tập huấn luyện (mỗi mốc lấy mẫu con ngẫu nhiên 5 lần), đo Macro-F1 trên tập kiểm định.")
lt = pd.DataFrame({"Số bài huấn luyện": [f"{int(n):,}".replace(",", ".") for n in lc.n], "Accuracy huấn luyện": [pc(x, 0) for x in lc.train_acc], "Macro-F1 kiểm định": [pc(x, 1) for x in lc.val_f1]})
CAP("Đường cong học của Linear SVM")
TABLE(lt)
IMG("learning_curve.png", "Đường cong học", 12, E)
P(f"Macro-F1 tăng từ {pc(lc.val_f1.iloc[0])} (192 bài) lên {pc(lc.val_f1.iloc[-1])} (3.850 bài) và chưa phẳng hẳn: từ 2.887 lên 3.850 bài vẫn tăng khoảng {vn((lc.val_f1.iloc[-1] - lc.val_f1.iloc[-2]) * 100, 1)} điểm. "
  "Độ chính xác trên tập huấn luyện luôn 100% nên khoảng cách huấn luyện – kiểm định là phương sai (thiếu dữ liệu), gợi ý rằng thêm dữ liệu sẽ còn giúp nhưng lợi ích giảm dần.")

H("4.6 Hiệu chỉnh độ tin cậy và dự đoán có chọn lọc", 2)
P("Website hiển thị “độ tự tin” (%) của AI cho từng chuyên mục, tính bằng softmax(T × điểm SVM). Một độ tin cậy hữu ích khi 90% nghĩa là khoảng 90% những lần như vậy đúng. "
  "Chúng em đo sai lệch hiệu chỉnh ECE (chia 10 nhóm độ tin cậy), Brier và NLL trên tập kiểm thử; hệ số T được chọn trên tập kiểm định (temperature scaling).")
ct = pd.DataFrame({"Cách tính": cal.method, "Độ tin cậy trung bình": [pc(x, 1) for x in cal.mean_conf], "ECE": [pc(x, 1) for x in cal.ECE], "Brier": [vn(x, 3) for x in cal.brier], "NLL": [vn(x, 3) for x in cal.nll]})
CAP("So sánh các cách hiệu chỉnh độ tin cậy trên tập kiểm thử")
TABLE(ct)
c0, c1 = cal.iloc[0], cal.iloc[1]
P(f"Hệ số ban đầu (T = 3) làm AI quá khiêm tốn: độ tin cậy trung bình {pc(c0.mean_conf)} trong khi độ chính xác thật là {pc(c0.acc)} (ECE {pc(c0.ECE)}). "
  f"Chọn T = {vn(T_cal, 1)} trên tập kiểm định đưa ECE xuống {pc(c1.ECE)} và NLL từ {vn(c0.nll, 3)} xuống {vn(c1.nll, 3)}, tốt hơn Platt scaling (ECE {pc(cal.iloc[2].ECE)}) và gần bằng Logistic Regression ({pc(cal.iloc[3].ECE)}). "
  f"Website dùng T = {vn(T_cal, 1)}. Các bài AI đoán đúng có độ tự tin trung bình {vn(ec['pct_correct'], 1)}%, còn bài đoán sai chỉ {vn(ec['pct_wrong'], 1)}%.")
IMG("calibration.png", "Biểu đồ độ tin cậy (chỉ vẽ nhóm có từ 10 bài; kích thước chấm tỉ lệ số bài)", 15, E)
P("Dự đoán có chọn lọc: nếu AI chỉ tự quyết những bài nó chắc chắn nhất và chuyển phần còn lại cho biên tập viên thì độ chính xác trên phần tự quyết tăng như sau (xếp theo chênh lệch giữa hai chuyên mục có xác suất cao nhất).")
rt = pd.DataFrame({"Tỉ lệ bài AI tự quyết": [pc(x, 0) for x in rc.coverage], "Số bài": rc.n.astype(str), "Accuracy trên phần tự quyết": [pc(x, 1) for x in rc.accuracy]})
CAP("Dự đoán có chọn lọc: độ chính xác khi AI chỉ tự quyết những bài chắc chắn nhất")
TABLE(rt)

H("4.7 Dự đoán có bảo đảm: AI nêu tập chuyên mục (conformal prediction)", 2)
P("Mục 5 sẽ cho thấy nhiều lỗi là bài nằm giữa hai chuyên mục. Thay vì ép AI chọn đúng một chuyên mục, chúng em cho AI nêu một TẬP chuyên mục sao cho với bài mới, chuyên mục đúng nằm trong tập với xác suất ít nhất 1 − α "
  "(conformal prediction; Vovk và cs., 2005; Angelopoulos và Bates, 2021). Bài dễ cho tập 1 chuyên mục, bài mơ hồ cho 2–3 chuyên mục. Cách làm:")
B(["Điểm lệch của một bài với đáp án y là khoảng cách giữa điểm SVM cao nhất và điểm SVM của y (bằng 0 nếu AI chọn đúng y).",
   "Ngưỡng tính riêng cho từng chuyên mục (Mondrian conformal) từ phân vị ⌈(n+1)(1−α)⌉/n của điểm lệch trên các bài có đáp án đó, nên chuyên mục khó như Thời sự cũng được bảo đảm.",
   "Tập dự đoán gồm các chuyên mục có điểm SVM cách điểm cao nhất không quá ngưỡng của chuyên mục đó; luôn chứa chuyên mục điểm cao nhất, không cần huấn luyện lại.",
   "Hiệu chỉnh trên 4.675 bài AI chưa từng thấy: 825 bài kiểm định và 3.850 bài huấn luyện chấm bằng dự đoán chéo 5-fold (mỗi bài được chấm bởi mô hình không học bài đó); đo trên 825 bài kiểm thử."])
meth = ["Top-1 (không có tập)", "Top-2 cố định", "Top-3 cố định", "LAC xác suất (chung)", "LAC xác suất (theo chuyên mục)", "APS ngẫu nhiên (chung)", "Khoảng cách điểm SVM (chung)", "Khoảng cách điểm SVM (theo chuyên mục)"]
t5 = cres[cres.alpha.round(2) == 0.05].set_index("method").loc[meth].reset_index()
P("So sánh các cách tạo tập ở mức bảo đảm 95% (độ phủ mục tiêu 0,95), trên 825 bài kiểm thử:")
CAP("So sánh các cách tạo tập chuyên mục ở mức bảo đảm 95% (825 bài kiểm thử)")
TABLE(pd.DataFrame({"Phương pháp": t5.method, "Độ phủ": [pc(x) for x in t5.coverage], "Chuyên mục/bài": [vn(x, 2) for x in t5.avg_size], "Bài chỉ 1 mục": [pc(x, 0) for x in t5.singleton_share],
                    "AI đúng khi chỉ 1 mục": [pc(x) if x == x else "—" for x in t5.singleton_acc], "Chuyên mục kém nhất": [pc(x) for x in t5.worst_class_coverage]}))
ccur = rcsv("conformal_curve.csv"); ccur = ccur[ccur.method == "Khoảng cách điểm SVM (theo chuyên mục)"]
def _size_at(cov):
    return float(ccur[ccur.coverage >= cov].avg_size.min())
P(f"Hai cách top-2 và top-3 cố định đạt độ phủ {pc(t5.set_index('method').loc['Top-2 cố định', 'coverage'])} và {pc(t5.set_index('method').loc['Top-3 cố định', 'coverage'])} nhưng luôn nêu 2 hoặc 3 chuyên mục. Các phương pháp conformal điều chỉnh kích thước tập theo từng bài (đa số chỉ 1 chuyên mục): "
  f"đạt cùng độ phủ thì tập trung bình chỉ {vn(_size_at(t5.set_index('method').loc['Top-2 cố định', 'coverage']), 2)} chuyên mục (so với 2,00) và {vn(_size_at(t5.set_index('method').loc['Top-3 cố định', 'coverage']), 2)} chuyên mục (so với 3,00; Hình @@FIG:conformal@@, ô phải trên). "
  "APS ngẫu nhiên cho tập lớn hơn (độ phủ 97,3%, trung bình 1,96 chuyên mục) vì phụ thuộc xác suất softmax. Điểm lệch bằng khoảng cách điểm SVM cho kết quả tương đương LAC trên xác suất nhưng không cần chọn hệ số nhiệt độ, nên được chọn. "
  "Ngưỡng riêng cho từng chuyên mục cần thêm khoảng 0,15 chuyên mục mỗi bài so với ngưỡng chung nhưng nâng độ phủ của chuyên mục kém nhất rõ rệt (xem dưới).")
pr_ = cprod
rows7 = []
for a, lab in (("0.1", "90%"), ("0.05", "95%"), ("0.01", "99%")):
    c = pr_[a]; rows7.append([lab, pc(c["coverage"]), vn(c["avg_size"], 2), pc(c["singleton_share"], 0), pc(c["singleton_acc"]), f"{c['wrong_rescued']}/{c['n_top1_wrong']}"])
P("Kết quả của phương pháp được dùng trên website (ngưỡng riêng từng chuyên mục) ở ba mức bảo đảm:")
CAP("Dự đoán có bảo đảm ở ba mức (ngưỡng riêng từng chuyên mục)")
TABLE(pd.DataFrame(rows7, columns=["Mức bảo đảm", "Độ phủ thực tế", "Chuyên mục/bài", "Bài chỉ 1 mục", "AI đúng khi chỉ 1 mục", "Bài AI đoán sai được cứu"]))
c95 = pr_["0.05"]; a95 = crep[(crep.alpha.round(2) == 0.05)].set_index("method")
mg, mo = a95.loc["Khoảng cách điểm SVM (chung)"], a95.loc["Khoảng cách điểm SVM (theo chuyên mục)"]
P(f"Ở mức 95%, độ phủ thực tế là {pc(c95['coverage'])}; {pc(c95['singleton_share'], 0)} số bài chỉ cần 1 chuyên mục và khi đó AI đúng {pc(c95['singleton_acc'])} (so với {pc(m['test_accuracy'])} khi buộc chọn 1 cho mọi bài); "
  f"{pc(c95['multi_share'], 0)} số bài mơ hồ được nêu từ 2 chuyên mục, trong đó chuyên mục AI chọn đầu tiên chỉ đúng {pc(c95['multi_acc_top1'], 0)} nhưng cả tập chứa đáp án đúng ở {pc(c95['multi_covered'], 0)} bài. "
  f"Tập 95% “cứu” được {c95['wrong_rescued']} trong {c95['n_top1_wrong']} bài mà AI chọn sai. Mức 90% gần như trùng với độ chính xác của top-1 ({pc(m['test_accuracy'])}) nên chỉ cần thêm rất ít chuyên mục; giá trị rõ nhất ở mức 95% và 99%.")
P("Độ phủ có thật sự đạt mục tiêu không? Chúng em lặp 300 lần chia ngẫu nhiên 50/50 trên toàn bộ 5.500 điểm chưa từng thấy (hiệu chỉnh trên một nửa, đo trên nửa còn lại):")
rr = crep[crep.method.isin(["Khoảng cách điểm SVM (chung)", "Khoảng cách điểm SVM (theo chuyên mục)"])].sort_values(["alpha", "method"], ascending=[False, True])
CAP("Độ phủ khi lặp 300 lần chia ngẫu nhiên 50/50")
TABLE(pd.DataFrame({"Mức bảo đảm": [f"{round((1 - a) * 100)}%" for a in rr.alpha], "Cách đặt ngưỡng": ["chung" if "chung" in x else "riêng từng chuyên mục" for x in rr.method],
                    "Độ phủ trung bình ± độ lệch chuẩn": [f"{pc(a, 1)} ± {vn(b * 100, 1)}" for a, b in zip(rr.cov_mean, rr.cov_std)], "Chuyên mục/bài": [vn(x, 2) for x in rr.size_mean],
                    "Chuyên mục kém nhất (trung bình)": [pc(x) for x in rr.worst_class_mean]}))
P(f"Độ phủ trung bình bám sát mục tiêu (95% → {pc(mg.cov_mean)} với ngưỡng chung, {pc(mo.cov_mean)} với ngưỡng riêng). Điểm đáng chú ý: với ngưỡng chung, chuyên mục kém nhất chỉ được phủ {pc(mg.worst_class_mean)}; ngưỡng riêng nâng lên {pc(mo.worst_class_mean)}. "
  "Phép thử thứ hai kiểm tra việc trộn hai nguồn điểm khi hiệu chỉnh: nếu chỉ dùng dự đoán chéo của 3.850 bài huấn luyện để hiệu chỉnh rồi đo trên 1.650 bài kiểm định + kiểm thử, độ phủ vẫn là "
  + ", ".join(f"{pc(coof[(coof.alpha.round(2) == a) & (coof.method == 'Khoảng cách điểm SVM (theo chuyên mục)')].coverage.iloc[0])} (mục tiêu {round((1 - a) * 100)}%)" for a in (0.1, 0.05, 0.01))
  + ". Nếu chỉ hiệu chỉnh bằng 825 bài kiểm định thì mức 99% không làm được (mỗi chuyên mục chỉ có khoảng 75 bài nên ngưỡng buộc phải nêu cả 11 chuyên mục), đó là lý do chúng em dùng thêm dự đoán chéo.")
IMG("conformal.png", "Dự đoán có bảo đảm (hiệu chỉnh trên 4.675 bài chưa từng thấy, đo trên 825 bài kiểm thử)", 14, E, key="conformal")
P("Lưu ý khi diễn giải: (1) bảo đảm là trung bình trên nhiều bài mới và giả định bài mới cùng phân phối với dữ liệu hiệu chỉnh, không bảo đảm cho từng bài và không bảo đảm với bài của báo khác; "
  "(2) bài thuộc tập huấn luyện được chấm bằng dự đoán chéo nên tập chuyên mục của chúng phản ánh sự mơ hồ thật chứ không phải việc mô hình đã học thuộc; (3) ngưỡng riêng cho chuyên mục khó (Thời sự) khiến chuyên mục này xuất hiện trong tập của nhiều bài thuộc mục khác.")

# ------------------------------------------------------------------ 5
H("5. Phân tích lỗi")
n_ts = int(((e88.truth == "Thời sự") | (e88.pred == "Thời sự")).sum())
P(f"Mô hình sai {len(err)}/{m['test_size']} bài ({pc(len(err) / m['test_size'])}). Chủ đề đặc trưng rõ như Thể thao, Sức khỏe, Xe, Giải trí, Pháp luật đạt F1 > 0,92; “Thời sự”, “Đời sống”, “Kinh doanh”, “Thế giới” thấp hơn. "
  f"Chuyên mục Thời sự có mặt trong {n_ts}/{len(err)} bài sai (là nhãn thật hoặc nhãn dự đoán). Các cặp nhầm nhiều nhất:")
CAP("Các cặp chủ đề bị nhầm nhiều nhất trên tập kiểm thử")
pp = pairs.head(6).copy(); pp.columns = ["Nhãn thật", "AI dự đoán", "Số bài"]; pp["Số bài"] = pp["Số bài"].astype(str); TABLE(pp)
P(f"Trong {ec['n_wrong']} bài sai, chuyên mục đúng đứng thứ hai trong bảng xếp hạng của AI ở {ec['truth_rank2']} bài ({pc(ec['truth_rank2'] / ec['n_wrong'], 0)}) và từ thứ ba trở đi ở {ec['truth_rank3plus']} bài: phần lớn lỗi là “suýt đúng”. "
  f"Không thấy xu hướng rõ theo độ dài bài: Accuracy của bốn nhóm độ dài (từ ngắn đến dài, mỗi nhóm khoảng 205 bài) lần lượt là " + ", ".join(pc(x, 1) for x in bylen.acc) + ".")
P(f"Có {ec['n_wrong_pct_ge_90']} bài AI sai nhưng rất tự tin (độ tự tin từ 90% trở lên), trong tổng số {ec['n_all_pct_ge_90']} bài AI tự tin từ 90% trở lên. Danh sách đầy đủ (để đọc và kiểm tra) trong outputs/experiments/errors_confident.csv; một số bài tiêu biểu:")
ce = conf_err.head(8).copy(); ce = pd.DataFrame({"Nhãn thật → AI": ce.truth + " → " + ce.pred, "Độ tự tin": [vn(x, 1) + "%" for x in ce.pct], "Tiêu đề": ce.title})
CAP("Một số bài AI xếp sai nhưng rất tự tin")
TABLE(ce)
P("Đọc tiêu đề của các bài này cho thấy nhiều bài có thể xếp hợp lý vào cả chuyên mục gốc lẫn chuyên mục AI chọn: tin vụ án đăng ở mục Thời sự nhưng nội dung là Pháp luật, tin sinh viên giành huy chương thể thao đăng ở mục Giáo dục, tin tài chính ngân hàng có yếu tố pháp lý. "
  "Như vậy một phần “lỗi” là do ranh giới nhãn mờ chứ không hoàn toàn do mô hình, nhưng cũng có lỗi thật (ví dụ bản tin dự báo thời tiết bị xếp vào Kinh doanh với 91,4%). "
  "Chúng em chưa gán lại nhãn cho từng bài nên chưa thể định lượng tỉ lệ nhãn sai.")
P("Từ khóa đặc trưng nhất của từng chủ đề (trọng số lớn nhất của Linear SVM), giúp giải thích mô hình:")
CAP("Từ khóa đặc trưng nhất của từng chủ đề")
TABLE(pd.DataFrame({"Chủ đề": list(kw), "Top từ khóa": [", ".join(v[:6]) for v in kw.values()]}))
P("Danh sách đầy đủ các bài dự đoán sai: outputs/mau_du_doan_sai.csv và outputs/experiments/errors_88.csv (kèm từ khóa ủng hộ nhãn thật và nhãn dự đoán).")

# ------------------------------------------------------------------ 6
H("6. Hệ thống web và các chức năng mở rộng")
P("Ngoài bài toán chính (phân loại), mô hình được đóng gói thành website tin tức VnNews (Flask) với các chức năng dùng những kỹ thuật học máy / xử lý ngôn ngữ khác nhau. "
  "Toàn bộ 5.500 bài được mô hình tự động gán chuyên mục; trang chủ có ô phân loại trực tiếp và mỗi bài có kết quả “AI xếp bài này vào…” kèm độ tự tin, các chuyên mục AI cân nhắc và các từ khóa quyết định. "
  "Chỉ số độ chính xác chỉ tính trên tập kiểm thử; với bài thuộc tập huấn luyện/kiểm định, website ghi rõ AI đã được học bài đó. Phần bắt buộc của đề tài là phân loại (mục 3–5); các chức năng dưới đây là phần làm thêm.")
CAP("Tổng quan các chức năng của website")
TABLE(pd.DataFrame([["Phân loại chuyên mục (bài toán chính)", "TF-IDF + Linear SVM", "trang chủ, /phan-loai, mỗi bài", "3–5"],
                    ["Độ tự tin của AI", "softmax(T × điểm SVM), T = 4,3", "mọi nơi hiện phần trăm", "4.6"],
                    ["Chuyên mục có thể thuộc (có bảo đảm)", "Conformal prediction", "trang bài, trang chủ, /thong-ke", "4.7"],
                    ["AI giải thích vì sao", "Phân rã trọng số mô hình tuyến tính", "/giai-thich", "6.4"],
                    ["Hỏi AI về tin tức", "TF-IDF + chọn câu có dẫn nguồn", "/hoi-ai, mỗi bài", "6.5"],
                    ["Tìm kiếm nâng cao, tìm theo nghĩa", "Chỉ mục Boolean theo trường + LSA", "/tim-kiem", "6.6"],
                    ["Bộ sưu tập cá nhân", "localStorage + gợi ý theo nội dung", "/bo-suu-tap", "6.7"],
                    ["Bình luận của bạn đọc", "SQLite, giới hạn tốc độ", "cuối mỗi bài", "6.9"],
                    ["Tóm tắt tự động", "TextRank", "/tom-tat, mỗi bài", "6.1"],
                    ["Gom sự kiện, chủ đề con", "TruncatedSVD + KMeans", "/su-kien", "6.2"],
                    ["Gợi ý bài đọc, bản tin 60 giây", "Content-based, tóm tắt hàng loạt", "trang chủ, /ban-tin", "6.3"]],
                   columns=["Chức năng", "Kỹ thuật", "Trang", "Mục"]), widths=[5.2, 5.0, 4.4, 1.4])
ev = json.load(open(O / "summary_eval.json", encoding="utf-8")) if (O / "summary_eval.json").exists() else {}
cl = json.load(open(O.parent / "data" / "clusters.json", encoding="utf-8")) if (O.parent / "data" / "clusters.json").exists() else {}
H("6.1 Tóm tắt tự động (TextRank)", 2)
P("Bài báo được tách thành câu (loại bỏ chú thích ảnh, dòng nguồn), mỗi câu được biểu diễn bằng vector TF-IDF. Đồ thị câu có cạnh là độ tương đồng cosine; chạy PageRank để tìm câu quan trọng nhất, "
  "cộng thêm điểm cho câu đầu bài và câu gần tiêu đề (Mihalcea & Tarau, 2004). Đây là tóm tắt trích rút nên không bịa thêm nội dung.")
if ev:
    CAP("Đánh giá tóm tắt bằng ROUGE")
    TABLE(pd.DataFrame([[k, vn(v['rouge1'], 3), vn(v['rouge2'], 3), str(v['n'])] for k, v in ev.items()], columns=["Phương pháp", "ROUGE-1 F1", "ROUGE-2 F1", "Số bài"]))
    P("Đánh giá trên khoảng 400 bài, lấy phần sapo do biên tập viên viết làm bản tham chiếu (2 câu). TextRank cao hơn hai phương pháp cơ sở là Lead-2 (hai câu đầu) và chọn ngẫu nhiên, nhưng chênh lệch so với Lead-2 nhỏ.")
H("6.2 Gom cụm sự kiện / chủ đề con (học không giám sát)", 2)
sil = sum(c["sil"] for c in cl.values()) / len(cl) if cl else 0
P("Với mỗi chuyên mục, tiêu đề và sapo được biểu diễn bằng TF-IDF, giảm chiều bằng TruncatedSVD (LSA, 60 chiều) rồi phân cụm KMeans (k bằng số bài chia 26, khoảng 19 cụm mỗi chuyên mục). "
  "Tên cụm là các cụm từ đặc trưng nhất của cụm so với phần còn lại của chuyên mục; bài tiêu biểu là bài gần tâm cụm nhất. Phương pháp không dùng nhãn nên bổ sung cho bài toán phân loại có giám sát. "
  f"Độ gắn kết trung bình (silhouette) là {vn(sil, 3)}; giá trị thấp là bình thường với dữ liệu văn bản vì từ vựng giữa các câu chuyện giao thoa nhiều, nhưng nhãn cụm vẫn dễ hiểu (ví dụ “ung thư”, “bóng chuyền”, “ngân hàng”).")
H("6.3 Gợi ý bài đọc và bản tin nhanh", 2)
B(["Gợi ý “Dành cho bạn”: hệ gợi ý dựa trên nội dung (content-based). Vector sở thích là trung bình TF-IDF của các bài người dùng đã đọc (lưu trên trình duyệt); bài được gợi ý là các bài có cosine cao nhất chưa đọc.",
   "Bản tin nhanh 60 giây: tóm tắt hàng loạt, mỗi chuyên mục một tin nổi bật còn 2 câu, hiển thị mức rút gọn nội dung.",
   "Tìm kiếm: xếp hạng bài theo cosine TF-IDF giữa truy vấn và tiêu đề + sapo."])
H("6.4 AI Lab – giải thích dự đoán (Explainable AI)", 2)
P("Vì Linear SVM là mô hình tuyến tính nên điểm của mỗi chủ đề bằng tổng (trọng số × giá trị TF-IDF); có thể tách chính xác đóng góp của từng từ mà không cần xấp xỉ như LIME/SHAP: "
  "đóng góp(từ) = (w của chủ đề dự đoán − w trung bình các chủ đề khác) × TF-IDF(từ), cụm hai từ chia đều cho hai từ. "
  "Trang AI Lab tô đậm từng từ theo mức ủng hộ chủ đề dự đoán, cho phép bỏ từ để thử What-if, và phát hiện bài đa chủ đề bằng cách phân loại riêng từng đoạn.")
IMG("man-hinh-ai-lab.png", "Trang AI Lab: từ được tô đậm theo mức ủng hộ chuyên mục AI dự đoán (ảnh chụp website)", 12.5, O / "man_hinh")
P("Kiểm chứng độ trung thực của lời giải thích (experiments/exp7_explain.py): với cả 825 bài kiểm thử, chúng em (a) xóa m từ mà AI cho là đóng góp nhiều nhất cho chủ đề dự đoán rồi dự đoán lại, "
  "(b) chỉ giữ lại m từ đó. Đối chứng gồm: m từ ngẫu nhiên theo loại từ, m từ ngẫu nhiên theo vị trí (từ hay gặp dễ trúng hơn) và m từ có TF-IDF lớn nhất. Đây là hai phép đo “comprehensiveness” và “sufficiency” thường dùng khi đánh giá giải thích (DeYoung và cs., 2020).")


def fcell(mode, mm, name):
    x = fa[f"{mode}_{mm}_{name}"]; return f"{vn(x['rate'] * 100, 1)}%"


names = ["AI chọn (đóng góp lớn nhất)", "TF-IDF lớn nhất", "Ngẫu nhiên (theo vị trí)", "Ngẫu nhiên (theo loại từ)"]
rows_ = []
for mm in (3, 5, 10):
    rows_.append([f"Xóa {mm} từ → bài đổi chuyên mục"] + [fcell("xoa", mm, n) for n in names])
for mm in (3, 5, 10):
    rows_.append([f"Chỉ giữ {mm} từ → bài GIỮ NGUYÊN chuyên mục"] + [f"{vn((1 - fa[f'giu_{mm}_{n}']['rate']) * 100, 1)}%" for n in names])
CAP("Độ trung thực của lời giải thích (825 bài kiểm thử)")
TABLE(pd.DataFrame(rows_, columns=["Phép thử"] + names))
x5 = fa["xoa_5_AI chọn (đóng góp lớn nhất)"]; g5 = fa["giu_5_AI chọn (đóng góp lớn nhất)"]
P(f"Kết quả: chỉ giữ 5 từ mà AI chỉ ra (khoảng {vn(g5['token_share'] * 100, 0)}% số từ của bài) thì {vn((1 - g5['rate']) * 100, 1)}% bài vẫn được xếp vào đúng chuyên mục cũ, trong khi 5 từ ngẫu nhiên chỉ giữ được {vn((1 - fa['giu_5_Ngẫu nhiên (theo loại từ)']['rate']) * 100, 0)}–{vn((1 - fa['giu_5_Ngẫu nhiên (theo vị trí)']['rate']) * 100, 0)}% và 5 từ có TF-IDF lớn nhất giữ được {vn((1 - fa['giu_5_TF-IDF lớn nhất']['rate']) * 100, 0)}%. "
  f"Ngược lại, xóa đúng 5 từ đó làm {vn(x5['rate'] * 100, 1)}% bài đổi chuyên mục (khoảng tin cậy 95%: {vn(x5['lo'] * 100, 1)}–{vn(x5['hi'] * 100, 1)}%), so với {fcell('xoa', 5, 'Ngẫu nhiên (theo loại từ)')}–{fcell('xoa', 5, 'TF-IDF lớn nhất')} khi xóa 5 từ chọn theo cách khác. "
  "Như vậy các từ được tô đậm thật sự mang quyết định của mô hình. Tuy nhiên quyết định dựa vào nhiều từ chứ không vài từ “then chốt”: phải xóa 20 từ mới làm gần một nửa số bài đổi chuyên mục "
  f"({vn(fa['ms'] and fcsv[(fcsv.che_do == 'xoa') & (fcsv.m == 20) & (fcsv.phuong_phap == names[0])].ty_le_doi_du_doan.iloc[0] * 100, 1)}%). Đây là kết quả trên 825 bài kiểm thử, không phải một ví dụ minh họa.")
IMG("explain_faithfulness.png", "Độ trung thực của lời giải thích (825 bài kiểm thử)", 15, E)
H("6.5 Hỏi AI về tin tức (hỏi đáp có dẫn nguồn)", 2)
P("Chức năng cho người đọc gõ một câu hỏi và nhận câu trả lời trích từ các bài báo, luôn kèm bài gốc và chuyên mục do AI phân loại; ô “Hỏi AI về bài này” trên từng bài chỉ tìm trong bài đó. "
  "Hệ thống không dùng mô hình sinh văn bản nên không tự bịa nội dung; hạn chế là chỉ trả lời được điều có sẵn trong kho 5.500 bài. Cách làm:")
B(["Truy hồi bài: điểm bài = 0,7 × cosine TF-IDF trên toàn văn (tiêu đề + sapo + nội dung, dùng chính TF-IDF của bộ phân loại) + 0,3 × cosine TF-IDF trên tiêu đề + sapo (chỉ mục của chức năng tìm kiếm); lấy 8 bài cao nhất.",
   "Chọn câu: tách các bài thành câu, xếp hạng câu theo cosine với câu hỏi (có thưởng nhẹ cho câu đầu bài), trả về tối đa 3 câu, mỗi bài không quá 2 câu.",
   "Độ chắc chắn dựa trên điểm của bài cao nhất: từ 0,30 là cao, từ 0,20 là trung bình, từ 0,10 là thấp; dưới 0,10 hệ thống trả lời “chưa tìm thấy thông tin phù hợp” thay vì đoán.",
   "Chủ đề của câu hỏi được suy ra bằng cách bỏ phiếu theo chuyên mục AI đã xếp cho các bài tìm được (phân loại trực tiếp câu hỏi ngắn không đủ tin cậy)."])
IMG("man-hinh-hoi-ai.png", "Trang Hỏi AI: câu trả lời trích nguyên văn từ bài, kèm nguồn và chuyên mục do AI xếp (ảnh chụp website)", 12.5, O / "man_hinh")
P("Đánh giá (experiments/exp8_qa.py): phép thử “tìm đúng bài” — dùng tiêu đề của mỗi bài làm câu hỏi, chỉ mục không chứa chính tiêu đề đó (tránh rò rỉ), xem bài đúng đứng thứ mấy trong kết quả trên 5.500 truy vấn.")
want = ["Chỉ sapo (TF-IDF tìm kiếm)", "Chỉ nội dung (TF-IDF của bộ phân loại)", "Kết hợp: nội dung 0.5 + sapo 0.5", "Kết hợp: nội dung 0.7 + sapo 0.3", "+ định tuyến chuyên mục (λ=0.5)"]
qq = qr.set_index("bien_the").loc[want].reset_index()
CAP("Đánh giá tìm lại bài của chức năng Hỏi AI (5.500 truy vấn)")
TABLE(pd.DataFrame({"Chỉ mục / cách chấm": [w.replace("0.", "0,").replace("λ=0,5", "λ = 0,5") for w in qq.bien_the], "Đúng bài ở vị trí 1": [pc(x, 1) for x in qq.recall_at_1], "Trong 5 kết quả đầu": [pc(x, 1) for x in qq.recall_at_5],
                    "Trong 10 kết quả đầu": [pc(x, 1) for x in qq.recall_at_10], "MRR": [vn(x, 3) for x in qq.mrr]}))
b7 = qr.set_index("bien_the").loc["Kết hợp: nội dung 0.7 + sapo 0.3"]
P(f"Kết hợp toàn văn và sapo với trọng số 0,7/0,3 cho bài đúng ở vị trí 1 trong {pc(b7.recall_at_1)} trường hợp và trong 5 kết quả đầu trong {pc(b7.recall_at_5)} (MRR {vn(b7.mrr, 3)}), cao hơn dùng riêng sapo hoặc riêng toàn văn. "
  "Định tuyến theo chuyên mục (chỉ ưu tiên bài thuộc chuyên mục mà bộ phân loại dự đoán cho câu hỏi) không cải thiện (vị trí 1: 86,3–86,6% so với 86,5% khi không định tuyến), nên không dùng; đây là một ví dụ cho thấy bộ phân loại không phải lúc nào cũng giúp các chức năng khác.")
P("Điểm của bài cao nhất có phản ánh độ đúng: tỉ lệ tìm đúng bài tăng đều theo khoảng điểm, nhờ đó đặt được nhãn “độ chắc chắn”:")
CAP("Độ chắc chắn theo khoảng điểm của bài cao nhất")
TABLE(pd.DataFrame({"Khoảng điểm của bài cao nhất": [k.replace(".", ",") for k in qc.khoang], "Số câu hỏi": [th(n) for n in qc.n], "Tìm đúng bài": [pc(x, 1) for x in qc.ty_le_dung_bai]}))
th10 = [x for x in qa["thresholds"] if abs(x["nguong"] - 0.10) < 1e-9][0]
P(f"Khả năng từ chối: đối chiếu 5.500 truy vấn thật với 5.500 truy vấn ngẫu nhiên (5 từ bất kỳ trong vốn từ), điểm của bài cao nhất tách hai nhóm với AUC = {vn(qa['auc_thuc_vs_ngau_nhien'], 3)}. "
  f"Với ngưỡng 0,10 đang dùng, hệ thống từ chối nhầm {pc(th10['tu_choi_nham_truy_van_that'])} truy vấn thật và vẫn trả lời nhầm {pc(th10['tra_loi_nham_truy_van_ngau_nhien'])} truy vấn ngẫu nhiên. "
  "Lưu ý: đây là phép thử tìm lại bài bằng tiêu đề, chưa phải đánh giá chất lượng câu trả lời với câu hỏi thật của người dùng; câu được trích có thể chưa đúng ý, vì vậy giao diện luôn dẫn nguồn để người đọc kiểm tra.")
H("6.6 Tìm kiếm nâng cao và tìm theo nghĩa", 2)
P("Trang tìm kiếm có ba chế độ: (1) theo từ khóa (TF-IDF); (2) nâng cao, tự bật khi truy vấn có toán tử Boolean AND / OR / NOT, cụm từ trong ngoặc kép, ký tự đại diện (bóng*), ngoặc đơn hoặc trường (tieude:, sapo:, noidung:, chuyenmuc:); "
  "(3) theo nghĩa (LSA). Mọi so khớp không phân biệt dấu tiếng Việt. Giao diện hiển thị cách hiểu truy vấn (ví dụ “giá VÀ vàng VÀ (tăng HOẶC giảm) VÀ KHÔNG bitcoin”), tô sáng từ khóa trong câu trích và có bộ lọc (chuyên mục, AI tự tin ≥ 95%, bài có thể thuộc nhiều mục, đọc ≤ 3 phút).")
IMG("man-hinh-tim-kiem.png", "Tìm kiếm nâng cao: website hiển thị cách hiểu truy vấn và số bài khớp (ảnh chụp website)", 12.5, O / "man_hinh")
P(f"Bộ tìm Boolean dùng chỉ mục ngược nhị phân theo từng trường. Để kiểm tra tính đúng, chúng em sinh truy vấn ngẫu nhiên (AND/OR/NOT, cụm từ, tiền tố, trường) và so với một cách duyệt tuần tự độc lập: {boolt['n_match']}/{boolt['n_queries_checked']} truy vấn cho đúng cùng tập bài; "
  f"thời gian trả lời trung bình {vn(boolt['ms_mean'], 1)} ms (phân vị 95%: {vn(boolt['ms_p95'], 0)} ms) trên 5.500 bài. Kiểm thử đơn vị nằm ở tests/test_features.py.")
P("Tìm theo nghĩa dùng LSA: TF-IDF (từ đơn, 30.000 đặc trưng) rồi TruncatedSVD 300 chiều. Chúng em so với TF-IDF thường trên ba phép thử (tham số chọn trên một nửa số bài, báo cáo trên nửa còn lại): tìm lại bài từ tiêu đề, tìm lại bài từ sapo, và độ thuần chủ đề "
  "(lấy tiêu đề làm truy vấn, 10 bài gần nhất có cùng chuyên mục thật không).")
sm = sem.set_index("method").loc[["TF-IDF", "LSA k=300", "Trộn k=300, 70% TF-IDF"]]
CAP("Tìm theo nghĩa (LSA) so với TF-IDF thường")
TABLE(pd.DataFrame({"Cách xếp hạng": ["TF-IDF thường", "LSA 300 chiều", "Trộn 70% TF-IDF + 30% LSA"], "Tiêu đề → bài: đúng ở vị trí 1": [pc(x) for x in sm["tiêu đề → bài | eval | R@1"]],
                    "Tiêu đề → bài: MRR": [vn(x, 3) for x in sm["tiêu đề → bài | eval | MRR"]], "Sapo → bài: đúng ở vị trí 1": [pc(x) for x in sm["sapo → bài | eval | R@1"]],
                    "Độ thuần chủ đề P@10": [pc(x) for x in sm["độ thuần chủ đề P@10 | eval"]]}))
dP = (sm.loc["Trộn k=300, 70% TF-IDF", "độ thuần chủ đề P@10 | eval"] - sm.loc["TF-IDF", "độ thuần chủ đề P@10 | eval"]) * 100
dR = (sm.loc["Trộn k=300, 70% TF-IDF", "tiêu đề → bài | eval | R@1"] - sm.loc["TF-IDF", "tiêu đề → bài | eval | R@1"]) * 100
P(f"LSA một mình kém hẳn TF-IDF khi cần tìm đúng một bài cụ thể (khớp từ khóa chính xác quan trọng hơn) nhưng cho các bài lân cận cùng chủ đề hơn. Bản trộn 70/30 giữ nguyên khả năng tìm đúng bài (vị trí 1 thay đổi {vn(dR, 1)} điểm, không đáng kể) và tăng độ thuần chủ đề {vn(dP, 1)} điểm; "
  "vì vậy website cung cấp “Theo nghĩa” như một lựa chọn bên cạnh tìm theo từ khóa chứ không thay thế. Đây là phép đo gián tiếp (chưa có người dùng đánh giá độ liên quan).")
H("6.7 Bộ sưu tập cá nhân", 2)
P("Người đọc lưu bài, gắn thẻ riêng, xem thành phần chuyên mục của những bài đã lưu, xuất danh sách ra JSON/CSV và hỏi AI chỉ trong các bài đã lưu (chức năng Hỏi AI giới hạn trên danh sách bài). Danh sách lưu trong trình duyệt (localStorage), không lưu trên máy chủ; "
  "trang cũng gợi ý thêm bài giống với bộ sưu tập bằng hệ gợi ý dựa trên nội dung ở mục 6.3.")
H("6.8 Phân loại thời gian thực và chạy cục bộ", 2)
B(["Phân loại khi gõ: kết quả cập nhật theo thời gian thực sau mỗi lần ngừng gõ, không cần nhấn nút; trang chủ có ô dán văn bản và xem ngay chuyên mục AI chọn.",
   "Toàn bộ chức năng chạy cục bộ, không cần Internet hay thiết bị ngoại vi, nên ổn định khi trình bày; thêm tùy chọn python app.py --lan để máy khác cùng WiFi mở được."])

H("6.9 Bình luận của bạn đọc", 2)
P("Mỗi bài báo có khu bình luận quen thuộc ở các trang tin: đăng bình luận, trả lời (một cấp), bấm Thích, sắp xếp theo mới nhất hoặc nhiều lượt thích, xóa bình luận do chính mình viết; số bình luận hiện trên thẻ bài và khối “Ý kiến bạn đọc” ở thanh bên. "
  "Bình luận lưu trong SQLite (data/comments.db) và không cần tài khoản: mỗi trình duyệt tự sinh một mã ngẫu nhiên, máy chủ chỉ giữ bản băm SHA-256 của mã đó để biết bình luận nào là của mình và ai đã thích. "
  "Hệ thống giới hạn độ dài (1.000 ký tự), tốc độ (cách nhau 5 giây; tối đa 20 bình luận mỗi giờ cho mỗi trình duyệt và 60 cho mỗi địa chỉ IP), từ chối bình luận trùng, và luôn thoát ký tự HTML khi hiển thị nên nội dung người dùng không chèn được mã. "
  f"Phần này được kiểm thử bằng {N_CMT} bài kiểm tra đơn vị (tests/test_comments.py) và một kịch bản trình duyệt tự động (tests/e2e/comments_e2e.js: đăng, trả lời, thích, xóa, tải lại trang, trình duyệt thứ hai, chuỗi chứa HTML).")
IMG("man-hinh-binh-luan.png", "Khu bình luận dưới mỗi bài (nội dung bình luận trong ảnh là ví dụ minh họa do nhóm nhập)", 9.5, O / "man_hinh")
H("6.10 Giao diện", 2)
P("Giao diện theo bố cục báo điện tử hiện đại: đầu trang trắng, thanh menu chuyển màu xanh ngọc sang xanh dương (Trang chủ, Chuyên mục, Thử phân loại, Độ chính xác, Công cụ AI, ô tìm kiếm và nút menu), nền xanh với cột nội dung trắng ở giữa và cụm tin nổi bật ba cột (tiêu đề, ảnh, danh sách). "
  "Ảnh minh họa được tự vẽ bằng SVG, mỗi chuyên mục một bảng màu. Giao diện có chế độ sáng/tối và dùng được trên điện thoại; toàn bộ phần màu nằm trong static/theme.css (nạp sau style.css).")
P("Vì đề tài là phân loại nên giao diện được làm gọn để người xem hiểu ngay: trang chủ chỉ giữ ba việc (thử phân loại theo ba bước, giải thích ba bước AI làm việc, tin theo chuyên mục); thẻ tin chỉ có một nhãn “AI xếp” (kèm cảnh báo nếu AI xếp khác báo gốc); "
  "trang bài báo cho thấy ngay chuyên mục AI chọn, độ tự tin và AI có khớp báo gốc không, còn các chi tiết (các chuyên mục AI cân nhắc, từ khóa, mức bảo đảm) thu vào mục “Xem AI phân tích chi tiết”; các công cụ phụ gom vào mục “Công cụ AI”. "
  "Một số thuật ngữ được đổi sang từ dễ hiểu: “mức nghiêng” thành “độ tự tin”, “bài giao thoa” thành “bài có thể thuộc nhiều mục”.")
IMG("man-hinh-trang-chu.png", "Trang chủ: dán đoạn văn, bấm Phân loại và xem AI xếp vào chuyên mục nào (ảnh chụp website)", 12.5, O / "man_hinh")
IMG("man-hinh-trang-bai.png", "Trang bài báo: kết quả AI gọn ở đầu, chi tiết mở ra khi cần (ảnh chụp website)", 10, O / "man_hinh")
H("6.11 Kiểm thử phần mềm", 2)
P(f"Mã nguồn có {N_FEAT + N_CMT} bài kiểm tra đơn vị (python -m unittest discover -s tests): {N_FEAT} bài cho dự đoán có bảo đảm và tìm kiếm Boolean (độ phủ conformal, các trường hợp biên, toán tử AND/OR/NOT, cụm từ, ký tự đại diện, trường, không phân biệt dấu, báo lỗi cú pháp) "
  f"và {N_CMT} bài cho bình luận (đăng, trả lời, thích, xóa, sắp xếp, phân trang, kiểm tra đầu vào, giới hạn tốc độ, API, tự phục hồi khi tệp dữ liệu bị xóa lúc đang chạy). "
  "Giao diện được kiểm bằng các kịch bản trình duyệt thật (Playwright, thư mục tests/e2e/): bình luận (gồm kiểm tra nội dung chứa mã HTML không bị chạy), menu trên máy tính và điện thoại, và chụp ảnh màn hình đưa vào báo cáo.")

# ------------------------------------------------------------------ 7
H("7. Hạn chế và hướng phát triển")
B([f"Tách từ tiếng Việt: đã thử pyvi, Macro-F1 chỉ tăng {vn(abl.loc['Tách từ (pyvi) + 1–2 gram', 'delta_vs_base'] * 100, 2)} điểm (p = {vn(abl.loc['Tách từ (pyvi) + 1–2 gram', 'paired_t_p'], 2)}, chưa có ý nghĩa) nên không dùng; chưa thử underthesea/VnCoreNLP.",
   "Chưa thử mô hình ngôn ngữ lớn/PhoBERT vì mục tiêu chạy trên CPU; k-NN và MLP nhỏ đã thử nhưng không vượt Linear SVM.",
   "Dữ liệu chỉ 5.500 bài: đường cong học chưa phẳng nên thêm dữ liệu sẽ giúp; ranh giới nhãn mờ (mục 5) khiến khó vượt xa mức hiện tại nếu không làm sạch nhãn. Nhãn lấy từ chuyên mục của trang báo gốc, nhóm chưa kiểm duyệt thủ công.",
   f"Phần trăm hiển thị (độ tự tin) đã hiệu chỉnh nhiệt độ (ECE {pc(c1.ECE)}) nhưng chưa phải xác suất tuyệt đối; chưa kiểm tra trên tin từ nguồn báo khác (ngoài miền dữ liệu).",
   "Bảo đảm của tập chuyên mục là trung bình và chỉ áp dụng cho bài cùng phân phối với dữ liệu hiệu chỉnh (cùng nguồn báo); ngưỡng riêng cho Thời sự rộng nên chuyên mục này xuất hiện trong tập của nhiều bài thuộc mục khác.",
   "Tìm theo nghĩa (LSA) chưa được người dùng đánh giá, chỉ đo gián tiếp; bộ sưu tập cá nhân lưu trong trình duyệt nên không đồng bộ giữa các thiết bị.",
   "Bình luận không có tài khoản và không kiểm duyệt nội dung (chỉ giới hạn độ dài, tốc độ, chống trùng; người dùng chỉ xóa được bình luận của chính mình trên trình duyệt đó): phù hợp để trình diễn cục bộ, chưa đủ cho một website công khai.",
   "Hỏi AI chỉ trích câu có sẵn, không tổng hợp nhiều nguồn và chưa được đánh giá bằng câu hỏi của người dùng thật; chỉ trả lời được nội dung trong kho 5.500 bài (tĩnh, không cập nhật tin mới).",
   "Giao diện website được làm gọn theo nhận xét của thành viên nhóm (trang chủ ban đầu có quá nhiều khối nên khó hiểu); chưa khảo sát người dùng bên ngoài nhóm.",
   "Hướng phát triển: thu tin mới qua RSS để kiểm tra ngoài dữ liệu hiện có; gán lại nhãn cho các bài nghi sai; thử PhoBERT khi có GPU; thêm chấm điểm câu trả lời bằng người đọc."])

# ------------------------------------------------------------------ 8
H("8. Hướng dẫn chạy")
H("8.1 Môi trường", 2)
P("Chương trình chạy trên CPU, không cần GPU hay Internet (phông chữ lấy từ Google Fonts nếu có mạng, nếu không website dùng phông dự phòng). Phiên bản đã chạy thử:")


def _ver(pkg):
    try:
        return imd.version(pkg)
    except Exception:
        return "—"


CAP("Môi trường đã chạy thử")
TABLE(pd.DataFrame([["Python", sys.version.split()[0]], ["scikit-learn", _ver("scikit-learn")], ["pandas", _ver("pandas")], ["numpy", _ver("numpy")], ["Flask", _ver("flask")],
                    ["matplotlib", _ver("matplotlib")], ["python-docx", _ver("python-docx")]], columns=["Thành phần", "Phiên bản"]), widths=[6, 10])
H("8.2 Cài đặt và chạy website", 2)
P("Windows: giải nén toàn bộ thư mục rồi bấm đúp CHAY.bat (tự tạo môi trường .venv, cài thư viện và chạy website). Hoặc gõ tay (cần Python 3.10 trở lên):")
CODE(["python -m venv .venv", ".venv\\Scripts\\activate          (Linux/macOS: source .venv/bin/activate)", "pip install -r requirements.txt", "python app.py"])
P("Lần đầu mất 1–3 phút để nạp mô hình và dựng chỉ mục tìm kiếm; chờ đến khi cửa sổ hiện dòng “Mở trình duyệt tại http://127.0.0.1:5000” rồi mở địa chỉ đó (đừng bấm Ctrl+C khi chưa thấy dòng này). "
  "Câu hỏi đầu tiên ở Hỏi AI và lần tìm “Theo nghĩa” đầu tiên có thể chờ thêm vài chục giây vì chỉ mục được dựng ở luồng nền. Thêm tùy chọn --lan (python app.py --lan) để máy khác cùng WiFi mở được. "
  "Bình luận lưu ở data/comments.db, tạo tự động khi chạy; xóa tệp này nếu muốn xóa hết bình luận.")
H("8.3 Huấn luyện lại, thí nghiệm, báo cáo và kiểm thử", 2)
CODE(["python train.py                        # huấn luyện mô hình", "python build_cache.py                  # dự đoán sẵn + hiệu chỉnh conformal",
      "python predict.py \"nội dung bài báo\"   # phân loại một đoạn văn", "python experiments/exp2_ablation.py    # chạy một thí nghiệm (exp1 … exp10)",
      "python make_report.py                  # sinh lại báo cáo này", f"python -m unittest discover -s tests -v   # {N_FEAT + N_CMT} bài kiểm tra tự động"])
P("Thí nghiệm tách từ cần cài thêm pyvi (pip install pyvi). Nếu gặp lỗi khi chạy, chạy python kiem_tra_moi_truong.py để xem phiên bản Python, thời gian nạp từng thư viện và thử nạp mô hình. "
  "Kiểm thử giao diện bằng trình duyệt thật (Playwright) nằm trong tests/e2e/ và cần Node.js; cách chạy ghi ở đầu mỗi tệp.")

# ------------------------------------------------------------------ 9
H("9. Kết luận")
P(f"Hệ thống TF-IDF + Linear SVM đạt Accuracy {pc(m['test_accuracy'])} và Macro-F1 {pc(m['test_macro_f1'])} trên 11 chủ đề (khoảng tin cậy 95% của Accuracy: {pc(ci['acc_lo'])}–{pc(ci['acc_hi'])}), "
  f"ổn định khi chia lại dữ liệu ({vn(sv_.split_acc_mean * 100, 1)}% ± {vn(sv_.split_acc_std * 100, 1)}), huấn luyện khoảng 10 giây trên CPU. "
  "Khi chỉnh tham số công bằng cho mọi mô hình, Linear SVM và Logistic Regression ngang nhau về mặt thống kê; ablation cho thấy nội dung bài báo, cặp từ và log-tf là các yếu tố quan trọng còn tách từ không cải thiện đáng kể. "
  f"Chúng em còn hiệu chỉnh độ tin cậy (ECE từ {pc(c0.ECE)} xuống {pc(c1.ECE)}), kiểm chứng rằng lời giải thích của AI Lab phản ánh đúng quyết định của mô hình trên 825 bài, "
  f"và bổ sung chức năng Hỏi AI trả lời có dẫn nguồn. Điểm đột phá là dự đoán có bảo đảm: với mức 95%, AI nêu trung bình {vn(cprod['0.05']['avg_size'], 2)} chuyên mục mỗi bài và đáp án đúng nằm trong tập ở {pc(cprod['0.05']['coverage'])} bài kiểm thử (so với {pc(m['test_accuracy'])} khi chỉ được chọn một), "
  "kèm tìm kiếm nâng cao (Boolean, theo trường, theo nghĩa), bộ sưu tập cá nhân và bình luận của bạn đọc. Toàn bộ chạy trên CPU, không cần tài nguyên tính toán lớn.")
P("Phần bắt buộc của đề tài là phân loại tin tức (mục 2–5) và đã được thực hiện đầy đủ, có đánh giá và kiểm định. Website và các chức năng ở mục 6 là phần làm thêm để mô hình dùng được trong thực tế và dễ trình bày; "
  "chúng không thay đổi kết quả phân loại.")

# ------------------------------------------------------------------ 10
H("10. Phân công công việc")
P("Bảng dưới ghi nhiệm vụ chính của từng thành viên theo cách nhóm chia phần thuyết trình; cột họ và tên do nhóm điền.")
CAP("Phân công công việc của nhóm")
TABLE(pd.DataFrame([["Nhóm trưởng", "", "Điều phối, tổng hợp báo cáo và slide; điểm nhấn: giải thích AI và dự đoán có bảo đảm; hạn chế và kết luận", "1.4, 4.6–4.7, 6.4, 7, 9"],
                    ["Thành viên 1", "", "Xác định đề tài và mục tiêu; thu thập, mô tả dữ liệu; quy trình tổng thể", "1, 2"],
                    ["Thành viên 2", "", "Làm sạch văn bản, trích xuất đặc trưng TF-IDF, huấn luyện Linear SVM", "3.1–3.3"],
                    ["Thành viên 3", "", "Cách đánh giá; so sánh công bằng các thuật toán; kiểm định thống kê; ablation", "3.4–3.5, 4.1, 4.3–4.4"],
                    ["Thành viên 4", "", "Kết quả cuối, F1 từng chuyên mục, phân tích lỗi; xây dựng website", "4.2, 5, 6"]],
                   columns=["Vai trò", "Họ và tên", "Nhiệm vụ chính", "Phần báo cáo"]), widths=[2.6, 3.2, 7.2, 3.0])
PH([("[Nhóm kiểm tra và sửa bảng phân công cho đúng với đóng góp thực tế của từng người trước khi nộp; xóa dòng này sau khi sửa.]", True)])

H("Tài liệu tham khảo")
B(["Pedregosa et al., Scikit-learn: Machine Learning in Python, JMLR 12, 2011.", "Manning, Raghavan, Schütze. Introduction to Information Retrieval, Cambridge UP, 2008.",
   "Salton, G., Buckley, C. Term-weighting approaches in automatic text retrieval, Information Processing & Management 24(5), 1988.",
   "Cortes, C., Vapnik, V. Support-vector networks, Machine Learning 20(3), 1995.",
   "Fan, R.-E., Chang, K.-W., Hsieh, C.-J., Wang, X.-R., Lin, C.-J. LIBLINEAR: A Library for Large Linear Classification, JMLR 9, 2008.",
   "Joachims, T. Text categorization with Support Vector Machines, ECML 1998.",
   "Hoang, V. C. D., Dinh, D., Le Nguyen, N., Ngo, H. Q. A comparative study on Vietnamese text classification methods, IEEE RIVF 2007.",
   "Nguyen, D. Q., Nguyen, A. T. PhoBERT: Pre-trained language models for Vietnamese, Findings of EMNLP 2020.",
   "Vu, T., Nguyen, D. Q., Nguyen, D. Q., Dras, M., Johnson, M. VnCoreNLP: A Vietnamese Natural Language Processing Toolkit, NAACL (Demonstrations) 2018.",
   "McNemar, Q. Note on the sampling error of the difference between correlated proportions or percentages, Psychometrika 12(2), 1947.",
   "Dietterich, T. G. Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms, Neural Computation 10(7), 1998.",
   "Guo, C., Pleiss, G., Sun, Y., Weinberger, K. Q. On Calibration of Modern Neural Networks, ICML 2017.",
   "DeYoung, J. et al. ERASER: A Benchmark to Evaluate Rationalized NLP Models, ACL 2020.",
   "Mihalcea, R., Tarau, P. TextRank: Bringing Order into Texts, EMNLP 2004.",
   "Vovk, V., Gammerman, A., Shafer, G. Algorithmic Learning in a Random World, Springer, 2005.",
   "Angelopoulos, A. N., Bates, S. A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification, 2021.",
   "Romano, Y., Sesia, M., Candès, E. Classification with Valid and Adaptive Coverage, NeurIPS 2020.",
   "Deerwester, S. et al. Indexing by Latent Semantic Analysis, JASIS 41(6), 1990."])

# ------------------------------------------------------------------ phụ lục
H("Phụ lục A. Cấu trúc mã nguồn")
d.paragraphs[-1].paragraph_format.page_break_before = True      # phụ lục bắt đầu ở trang mới
CAP("Các tệp và thư mục chính")
TABLE(pd.DataFrame([["app.py", "Website Flask: các trang, API phân loại, Hỏi AI, tìm kiếm, bộ sưu tập, bình luận"],
                    ["train.py", "Huấn luyện, so sánh nhanh các mô hình, sinh model.joblib và biểu đồ trong outputs/"],
                    ["build_cache.py", "Dự đoán sẵn cho 5.500 bài và hiệu chỉnh conformal (data/predictions.json, data/conformal.json)"],
                    ["conformal.py", "Dự đoán có bảo đảm: ngưỡng theo từng chuyên mục, tập chuyên mục, đo độ phủ"],
                    ["search_tools.py", "Tìm kiếm Boolean theo trường và tìm theo nghĩa (LSA)"],
                    ["comments.py", "Kho bình luận SQLite và các API /api/comments"],
                    ["predict.py, eval_summary.py, kiem_tra_moi_truong.py", "Tiện ích dòng lệnh: phân loại một đoạn văn, đo ROUGE của tóm tắt, kiểm tra môi trường"],
                    ["make_report.py", "Sinh báo cáo Word này từ kết quả thí nghiệm"],
                    ["experiments/", "Các thí nghiệm exp1–exp10, vẽ sơ đồ hệ thống và biểu đồ ablation"],
                    ["templates/, static/", "Giao diện: trang HTML, style.css và theme.css (màu, bố cục), comments.js"],
                    ["tests/", f"{N_FEAT + N_CMT} bài kiểm tra đơn vị; kịch bản trình duyệt tự động trong tests/e2e/"],
                    ["data/", "news_dataset.csv, predictions.json, conformal.json, clusters.json; comments.db được tạo khi chạy"],
                    ["outputs/", "Số liệu, biểu đồ, kết quả thí nghiệm và ảnh màn hình website (man_hinh/)"],
                    ["trinh-bay/", "Slide và kịch bản thuyết trình"],
                    ["CHAY.bat, requirements.txt, HUONG-DAN-CHAY.txt, README.md", "Chạy nhanh trên Windows, danh sách thư viện và hướng dẫn"]], columns=["Tệp / thư mục", "Vai trò"]), widths=[5.2, 10.8])
H("Phụ lục B. Tham số của hệ thống")
CAP("Tham số chính")
TABLE(pd.DataFrame([["TF-IDF", "ngram_range = (1, 2); min_df = 2; max_df = 0.9; sublinear_tf = True; max_features = 200.000"],
                    ["Linear SVM", "LinearSVC, C = 2, chiến lược một-chống-tất-cả"],
                    ["Chia dữ liệu", "70% / 15% / 15%, phân tầng, random_state = 42"],
                    ["Chọn mô hình", "GridSearchCV 5-fold trên tập huấn luyện, tiêu chí Macro-F1"],
                    ["Độ tự tin", f"softmax(T × điểm SVM), T = {vn(T_cal, 1)} (chọn trên tập kiểm định)"],
                    ["Dự đoán có bảo đảm", "mức 90 / 95 / 99% (α = 0,1 / 0,05 / 0,01), ngưỡng riêng từng chuyên mục; hiệu chỉnh trên 4.675 bài chưa từng thấy; website mặc định hiển thị 95%"],
                    ["Hỏi AI", "điểm bài = 0,7 × cosine toàn văn + 0,3 × cosine tiêu đề + sapo; độ chắc chắn: từ 0,30 cao, từ 0,20 trung bình, từ 0,10 thấp, dưới 0,10 từ chối"],
                    ["Tìm theo nghĩa", "TF-IDF 30.000 đặc trưng → TruncatedSVD 300 chiều; trộn 70% TF-IDF + 30% LSA"],
                    ["Tóm tắt", "TextRank (PageRank trên đồ thị câu), mặc định 3 câu"],
                    ["Gom cụm chủ đề con", "TruncatedSVD 60 chiều + KMeans, k = số bài / 26 (tối thiểu 8) cho mỗi chuyên mục"],
                    ["Bình luận", "tối đa 1.000 ký tự; cách nhau 5 giây; 20 bình luận mỗi giờ cho mỗi trình duyệt, 60 cho mỗi địa chỉ IP"]], columns=["Thành phần", "Tham số"]), widths=[4, 12])
H("Phụ lục C. Các thí nghiệm và tệp kết quả")
CAP("Thí nghiệm, mục báo cáo và tệp kết quả (outputs/experiments/)")
TABLE(pd.DataFrame([["exp1 (exp1_tuning, exp1b, finalize_exp1, exp1c)", "Chỉnh tham số công bằng cho các mô hình", "4.1", "tuning_final.csv, tuning_grids.json"],
                    ["exp2_ablation", "Ablation: n-gram, log-tf, IDF, từ vựng, trường văn bản, tách từ", "4.4", "ablation_results.csv, ablation.png"],
                    ["exp3_stability", "Độ ổn định, bootstrap, McNemar, bài gần giống", "4.1, 4.3, 2.3", "stability_*.csv, significance_vs_svm.csv, bootstrap_ci.json, near_duplicates.json"],
                    ["exp4_learning_curve", "Đường cong học", "4.5", "learning_curve.csv"],
                    ["exp5_calibration", "Hiệu chỉnh độ tin cậy, dự đoán có chọn lọc", "4.6", "calibration_results.csv, risk_coverage.csv"],
                    ["exp6_errors", "Phân tích lỗi", "5", "error_pairs.csv, errors_confident.csv, errors_88.csv"],
                    ["exp7_explain", "Độ trung thực của lời giải thích", "6.4", "explain_faithfulness.csv / .json"],
                    ["exp8_qa", "Đánh giá Hỏi AI", "6.5", "qa_retrieval.csv, qa_confidence.csv, qa_abstain.json"],
                    ["exp9_conformal", "Dự đoán có bảo đảm", "4.7", "conformal_*.csv, conformal.png"],
                    ["exp10_search", "Tìm kiếm Boolean và tìm theo nghĩa", "6.6", "search_bool_tests.json, search_semantic.csv"]],
                   columns=["Thí nghiệm", "Nội dung", "Mục", "Tệp kết quả"]), widths=[4.4, 5.2, 1.8, 4.6])

# ------------------------------------------------------------------ mục lục (trường Word có sẵn nội dung) và số hình
TOC_CACHE = json.load(open(O / "toc_pages.json", encoding="utf-8")) if (O / "toc_pages.json").exists() else {}


def _run_el(kind, instr=None):
    r = OxmlElement("w:r")
    if kind == "instr":
        e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = instr
    else:
        e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), kind)
    r.append(e)
    return r


def _build_toc():
    ents = [(1 if p_.style.name == "Heading 1" else 2, p_.text) for p_ in d.paragraphs if p_.style.name in ("Heading 1", "Heading 2")]
    pars = []
    for lvl, txt in ents:
        p_ = d.add_paragraph(style=f"TOC {lvl}")
        p_.add_run(txt + "\t" + str(TOC_CACHE.get(txt, "")))
        pars.append(p_)
    first, last = pars[0]._p, pars[-1]._p
    pos = list(first).index(first.pPr) + 1 if first.pPr is not None else 0
    for k, el in enumerate([_run_el("begin"), _run_el("instr", ' TOC \\o "1-2" \\z \\u '), _run_el("separate")]):
        first.insert(pos + k, el)
    last.append(_run_el("end"))
    for p_ in pars:
        _TOC._p.addprevious(p_._p)
    _TOC._p.getparent().remove(_TOC._p)


def _resolve_tokens():
    pat = re.compile(r"@@FIG:(\w+)@@")
    for p_ in d.paragraphs:
        for r_ in p_.runs:
            if "@@FIG:" in r_.text:
                r_.text = pat.sub(lambda mt: str(FIGN.get(mt.group(1), "?")), r_.text)


_build_toc()
_resolve_tokens()
_lp = d.paragraphs[-1]                                    # đoạn rỗng sau bảng cuối: thu còn 1 pt để không đẩy ra một trang trắng ở cuối báo cáo
if not _lp.text.strip():
    _lp.paragraph_format.space_before = _lp.paragraph_format.space_after = Pt(0)
    _lp.paragraph_format.line_spacing = Pt(1)
d.save(Path(__file__).parent / "BAO_CAO_DO_AN.docx")
print("Đã sinh BAO_CAO_DO_AN.docx")
