"""Sinh báo cáo Word từ mẫu của Học viện Hàng không Việt Nam (template.docx).

Giữ nguyên bìa, danh sách nhóm, bảng cán bộ chấm thi; điền nội dung từ content.py;
tạo mục lục / danh mục bảng / danh mục hình dạng trường TOC của Word kèm số trang
(tính bằng cách dựng PDF với LibreOffice rồi dò vị trí từng đề mục – 2 lượt).

Chạy: python docs/report/build_report.py
"""
from __future__ import annotations

import copy
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import content  # noqa: E402

TEMPLATE = HERE / "template.docx"
OUTPUT = ROOT / "docs" / "BaoCao_Nhom8_AI9_KhoDuLieuTuyenDung.docx"
TEXT_WIDTH_CM = 16.5
FONT = "Times New Roman"


# --------------------------------------------------------------------------- #
# Tiện ích XML
# --------------------------------------------------------------------------- #
def set_run_font(run, size=None, bold=None, italic=None, name=FONT, color=None):
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(attr), name)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def set_paragraph_text(p, text):
    """Thay nội dung đoạn, giữ định dạng run đầu tiên có chữ, không đụng run chứa hình."""
    runs = [r for r in p.runs if r._element.find(qn("w:drawing")) is None]
    target = next((r for r in runs if r.text.strip()), runs[0] if runs else None)
    for r in runs:
        if r is not target:
            r.text = ""
    target.text = text


def shade(cell, fill):
    tcpr = cell._element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcpr.append(shd)


def add_field_run(paragraph, instr):
    def fld(kind):
        r = OxmlElement("w:r")
        f = OxmlElement("w:fldChar")
        f.set(qn("w:fldCharType"), kind)
        r.append(f)
        return r
    paragraph._p.append(fld("begin"))
    r = OxmlElement("w:r")
    t = OxmlElement("w:instrText")
    t.set(qn("xml:space"), "preserve")
    t.text = f" {instr} "
    r.append(t)
    paragraph._p.append(r)
    paragraph._p.append(fld("separate"))
    run = paragraph.add_run("1")
    paragraph._p.append(fld("end"))
    return run


# --------------------------------------------------------------------------- #
class ReportBuilder:
    def __init__(self, page_numbers: dict[str, int] | None = None):
        self.doc = Document(TEMPLATE)
        self.page_numbers = page_numbers or {}
        self.toc_entries: list[tuple[int, str]] = []
        self.tables: list[str] = []
        self.figures: list[str] = []
        self.fig_no: dict[str, int] = {}
        self.tab_no: dict[str, int] = {}
        self._setup_styles()
        self._setup_numbering()

    # ------------------------------------------------------------ styles
    def _para_style(self, name, size=13, bold=False, italic=False, align=None, before=0, after=6, line=1.5,
                    first=None, left=None, keep_next=False, base="Normal"):
        styles = self.doc.styles
        st = styles[name] if name in [s.name for s in styles] else styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        st.base_style = styles[base]
        st.font.name, st.font.size, st.font.bold, st.font.italic = FONT, Pt(size), bold, italic
        rpr = st.element.get_or_add_rPr()
        fonts = rpr.find(qn("w:rFonts"))
        if fonts is None:
            fonts = OxmlElement("w:rFonts")
            rpr.insert(0, fonts)
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            fonts.set(qn(attr), FONT)
        for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if fonts.get(qn(attr)) is not None:
                del fonts.attrib[qn(attr)]
        st.font.color.rgb = RGBColor(0, 0, 0)
        pf = st.paragraph_format
        pf.alignment = align
        pf.space_before, pf.space_after, pf.line_spacing = Pt(before), Pt(after), line
        pf.first_line_indent = Cm(first) if first is not None else Cm(0)
        pf.left_indent = Cm(left) if left is not None else Cm(0)
        pf.keep_with_next = keep_next
        return st

    def _setup_styles(self):
        J, C, L = WD_ALIGN_PARAGRAPH.JUSTIFY, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT
        self._para_style("Heading 1", 16, True, align=C, before=0, after=18, line=1.15, keep_next=True)
        self._para_style("Heading 2", 14, True, align=L, before=12, after=6, line=1.3, keep_next=True)
        h3 = self._para_style("Heading 3", 13, True, align=L, before=10, after=4, line=1.3, keep_next=True)
        h4 = self._para_style("Heading 4", 13, True, True, align=L, before=6, after=3, line=1.3, keep_next=True)
        for st, lvl in ((h3, 2), (h4, 3)):
            ppr = st.element.get_or_add_pPr()
            if ppr.find(qn("w:outlineLvl")) is None:
                o = OxmlElement("w:outlineLvl")
                o.set(qn("w:val"), str(lvl))
                ppr.append(o)
        self._para_style("NoiDung", 13, align=J, after=6, line=1.5, first=1.0)
        self._para_style("ChamDauDong", 13, align=J, after=3, line=1.5, left=1.25, first=-0.5)
        self._para_style("TieuDeTrang", 16, True, align=C, before=0, after=18, line=1.15)
        self._para_style("Hinh", 13, False, True, align=C, before=4, after=12, line=1.15)
        self._para_style("Bang", 13, True, False, align=C, before=10, after=6, line=1.15, keep_next=True)
        self._para_style("ChuThichAnh", 12, align=C, before=6, after=0, line=1.0, keep_next=True)
        self._para_style("CongThuc", 13, False, True, align=C, before=4, after=8, line=1.3)
        self._para_style("ONho", 11.5, align=L, after=0, line=1.1)
        self._para_style("ThamKhao", 13, align=L, after=6, line=1.4, left=1.0, first=-1.0)
        code = self._para_style("Code", 8.5, align=L, after=0, line=1.0, left=0.2)
        code.font.name = "Courier New"
        fonts = code.element.rPr.find(qn("w:rFonts"))
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            fonts.set(qn(attr), "Courier New")
        for i, (bold, ind) in enumerate([(True, 0), (False, 0.6), (False, 1.2)], start=1):
            st = self._para_style(f"TOC {i}", 13, bold, align=L, before=3 if i == 1 else 0, after=2, line=1.2,
                                  left=ind)
            st.paragraph_format.tab_stops.add_tab_stop(Cm(TEXT_WIDTH_CM), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        st = self._para_style("Table of Figures", 13, align=L, after=2, line=1.2, left=0)
        st.paragraph_format.tab_stops.add_tab_stop(Cm(TEXT_WIDTH_CM), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)

    def _setup_numbering(self):
        numbering = self.doc.part.numbering_part.element
        abstract = OxmlElement("w:abstractNum")
        abstract.set(qn("w:abstractNumId"), "901")
        for lvl, (char, left) in enumerate([("–", 1.25), ("+", 1.9)]):
            l = OxmlElement("w:lvl")
            l.set(qn("w:ilvl"), str(lvl))
            for tag, val in (("w:start", "1"), ("w:numFmt", "bullet"), ("w:lvlText", char), ("w:lvlJc", "left")):
                e = OxmlElement(tag)
                e.set(qn("w:val"), val)
                l.append(e)
            ppr = OxmlElement("w:pPr")
            ind = OxmlElement("w:ind")
            ind.set(qn("w:left"), str(int(left * 567)))
            ind.set(qn("w:hanging"), str(int(0.5 * 567)))
            ppr.append(ind)
            l.append(ppr)
            rpr = OxmlElement("w:rPr")
            f = OxmlElement("w:rFonts")
            f.set(qn("w:ascii"), FONT)
            f.set(qn("w:hAnsi"), FONT)
            rpr.append(f)
            l.append(rpr)
            abstract.append(l)
        first_num = numbering.find(qn("w:num"))
        if first_num is not None:
            first_num.addprevious(abstract)
        else:
            numbering.append(abstract)
        num = OxmlElement("w:num")
        num.set(qn("w:numId"), "901")
        a = OxmlElement("w:abstractNumId")
        a.set(qn("w:val"), "901")
        num.append(a)
        numbering.append(num)

    # ------------------------------------------------------------ front matter
    def fill_front_matter(self):
        d = self.doc
        cover = d.tables[0]
        for row in cover.rows:
            cell = row.cells[0]
            for p in cell.paragraphs:
                t = p.text.strip()
                if t == "TÊN HỌC PHẦN":
                    set_paragraph_text(p, "LẬP TRÌNH PYTHON")
                elif t == "TÊN ĐỀ TÀI":
                    set_paragraph_text(p, "KHO DỮ LIỆU TUYỂN DỤNG CÓ AI PHÂN TÍCH PIPELINE ỨNG VIÊN")
                elif t.startswith("Sinh viên/ Nhóm"):
                    set_paragraph_text(p, "Sinh viên/ Nhóm sinh viên thực hiện: Nhóm 08 (Đề tài AI 9)")
                elif t.startswith("Mã số sinh viên"):
                    set_paragraph_text(p, "Mã số sinh viên: 2431540032, 2431540018, 2431540060, 2431540014")
                elif t.startswith("Lớp:"):
                    set_paragraph_text(p, "Lớp: 24ĐHTT01")
                elif "tháng mm/20yy" in t:
                    set_paragraph_text(p, t.replace("mm/20yy", "11/2026").replace("TP.Hồ", "TP. Hồ"))
            # bỏ bớt 2 dòng trống để tên đề tài dài vẫn vừa một trang
            empties = [p for p in cell.paragraphs[16:21] if not p.text.strip()
                       and p._p.find(".//" + qn("w:drawing")) is None]
            for p in empties[:2]:
                p._p.getparent().remove(p._p)

        for tbl in (d.tables[0], d.tables[1]):
            for hl in list(tbl._tbl.iter(qn("w:highlight"))):
                hl.getparent().remove(hl)
        group = d.tables[1]
        members = content.MEMBERS
        for i, m in enumerate(members, start=1):
            cells = group.rows[i].cells
            for cell, val in zip(cells, [str(i), *m]):
                set_paragraph_text(cell.paragraphs[0], val) if cell.paragraphs[0].runs else \
                    set_run_font(cell.paragraphs[0].add_run(val), 13)
        for row in list(group.rows)[len(members) + 1:]:
            row._tr.getparent().remove(row._tr)

        abbr = d.tables[2 if len(d.tables) == 3 else 3]
        template_row = abbr.rows[1]._tr
        for row in list(abbr.rows)[1:]:
            row._tr.getparent().remove(row._tr)
        for key, full in content.ABBREVIATIONS:
            tr = copy.deepcopy(template_row)
            abbr._tbl.append(tr)
            row = abbr.rows[-1]
            for cell, val in zip(row.cells, (key, full)):
                p = cell.paragraphs[0]
                for r in p.runs:
                    r.text = ""
                run = p.add_run(val)
                set_run_font(run, 13)
                p.paragraph_format.space_after = Pt(2)
                if val == full:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        body = d.element.body
        children = list(body.iterchildren())
        # Ngắt section sau trang chấm thi: phần sau có số trang
        brk = children[6]
        for r in brk.findall(qn("w:r")):
            brk.remove(r)
        final_sect = body.find(qn("w:sectPr"))
        sect = copy.deepcopy(final_sect)
        for ref in sect.findall(qn("w:headerReference")) + sect.findall(qn("w:footerReference")):
            sect.remove(ref)
        ppr = brk.find(qn("w:pPr"))
        if ppr is None:
            ppr = OxmlElement("w:pPr")
            brk.insert(0, ppr)
        ppr.append(sect)
        # Tiêu đề "DANH MỤC CÁC KÝ HIỆU" → Heading 1 (xuất hiện trong mục lục)
        heading = [p for p in d.paragraphs if p.text.strip().startswith("DANH MỤC CÁC KÝ HIỆU")][0]
        heading.style = d.styles["Heading 1"]
        self.toc_entries.append((1, "DANH MỤC CÁC KÝ HIỆU, CHỮ VIẾT TẮT"))
        # Xoá toàn bộ phần hướng dẫn của mẫu từ "MỤC LỤC" trở đi
        start = next(i for i, el in enumerate(children)
                     if el.tag == qn("w:p") and "".join(t.text or "" for t in el.iter(qn("w:t"))).strip() == "MỤC LỤC")
        for el in children[start:]:
            if el.tag != qn("w:sectPr"):
                body.remove(el)
        # Số trang ở chân trang (section 2)
        sec = d.sections[-1]
        sec.footer.is_linked_to_previous = False
        fp = sec.footer.paragraphs[0] if sec.footer.paragraphs else sec.footer.add_paragraph()
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = add_field_run(fp, "PAGE")
        set_run_font(run, 12)
        pg = OxmlElement("w:pgNumType")
        pg.set(qn("w:start"), "1")
        anchor = final_sect.find(qn("w:cols"))
        if anchor is None:
            anchor = final_sect.find(qn("w:docGrid"))
        anchor.addprevious(pg)  # pgNumType phải đứng trước cols/docGrid
        first = d.sections[0]
        first.footer.is_linked_to_previous = False

    # ------------------------------------------------------------ blocks
    def para(self, text, style="NoiDung"):
        p = self.doc.add_paragraph(style=style)
        self._rich(p, text)
        return p

    def _rich(self, p, text):
        """Hỗ trợ **đậm** và *nghiêng* trong chuỗi."""
        for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
            if not part:
                continue
            if part.startswith("**"):
                set_run_font(p.add_run(part[2:-2]), bold=True)
            elif part.startswith("*"):
                set_run_font(p.add_run(part[1:-1]), italic=True)
            else:
                set_run_font(p.add_run(part))

    def bullets(self, items, level=0):
        for item in items:
            if isinstance(item, (list, tuple)):
                self.bullets(item, level + 1)
                continue
            p = self.doc.add_paragraph(style="ChamDauDong")
            ppr = p._p.get_or_add_pPr()
            numpr = OxmlElement("w:numPr")
            il = OxmlElement("w:ilvl")
            il.set(qn("w:val"), str(level))
            ni = OxmlElement("w:numId")
            ni.set(qn("w:val"), "901")
            numpr.append(il)
            numpr.append(ni)
            ppr.append(numpr)
            p.paragraph_format.left_indent = Cm(1.25 + 0.65 * level)
            p.paragraph_format.first_line_indent = Cm(-0.5)
            self._rich(p, item)

    def heading(self, level, text, page_break=False):
        if page_break:
            self.page_break()
        p = self.doc.add_paragraph(style=f"Heading {level}")
        set_run_font(p.add_run(text))
        if level <= 2:
            self.toc_entries.append((level, text))
        return p

    def title(self, text):
        p = self.doc.add_paragraph(style="TieuDeTrang")
        set_run_font(p.add_run(text))

    def page_break(self):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.add_run().add_break(WD_BREAK.PAGE)

    def figure(self, key, path, caption, width_cm=16.0, max_h_cm=10.5):
        chapter = caption_chapter(caption)
        n = len([f for f in self.figures if f.startswith(f"Hình {chapter}.")]) + 1
        label = f"Hình {chapter}.{n}. {caption.split('|', 1)[-1]}"
        self.fig_no[key] = f"{chapter}.{n}"
        with Image.open(path) as im:
            w, h = im.size
        width = min(width_cm, max_h_cm * w / h)
        p = self.doc.add_paragraph(style="ChuThichAnh")
        p.add_run().add_picture(str(path), width=Cm(width))
        self.doc.add_paragraph(label, style="Hinh")
        self.figures.append(label)

    def table(self, key, caption, headers, rows, widths, font_size=11.5, header_fill="D9E2F3"):
        chapter = caption_chapter(caption)
        n = len([t for t in self.tables if t.startswith(f"Bảng {chapter}.")]) + 1
        label = f"Bảng {chapter}.{n}. {caption.split('|', 1)[-1]}"
        self.tab_no[key] = f"{chapter}.{n}"
        self.doc.add_paragraph(label, style="Bang")
        self.tables.append(label)
        t = self.doc.add_table(rows=1 + len(rows), cols=len(headers))
        t.style = self.doc.styles["Table Grid"]
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        total = sum(widths)
        widths = [w * TEXT_WIDTH_CM / total for w in widths]
        for ci, (h, w) in enumerate(zip(headers, widths)):
            cell = t.rows[0].cells[ci]
            cell.width = Cm(w)
            shade(cell, header_fill)
            p = cell.paragraphs[0]
            p.style = self.doc.styles["ONho"]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_run_font(p.add_run(h), font_size, bold=True)
        for ri, row in enumerate(rows, start=1):
            for ci, (val, w) in enumerate(zip(row, widths)):
                cell = t.rows[ri].cells[ci]
                cell.width = Cm(w)
                p = cell.paragraphs[0]
                p.style = self.doc.styles["ONho"]
                self._rich_cell(p, str(val), font_size)
        # độ rộng cột ở cấp lưới bảng (LibreOffice/Word đều đọc tblGrid) + bố cục cố định
        twips = [int(w / 2.54 * 1440) for w in widths]
        for gc, tw in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), twips):
            gc.set(qn("w:w"), str(tw))
        tblpr = t._tbl.tblPr
        tblw = tblpr.find(qn("w:tblW"))
        if tblw is None:
            tblw = OxmlElement("w:tblW")
            tblpr.append(tblw)
        tblw.set(qn("w:w"), str(sum(twips)))
        tblw.set(qn("w:type"), "dxa")
        layout = tblpr.find(qn("w:tblLayout"))  # t.autofit = False đã tạo tblLayout fixed
        if layout is not None:
            tblpr.remove(layout)
        layout = OxmlElement("w:tblLayout")
        layout.set(qn("w:type"), "fixed")
        anchor = tblpr.find(qn("w:tblCellMar"))
        if anchor is None:
            anchor = tblpr.find(qn("w:tblLook"))
        if anchor is not None:
            anchor.addprevious(layout)  # đúng thứ tự phần tử theo schema OOXML
        else:
            tblpr.append(layout)
        for row in t.rows:
            for cell, tw in zip(row.cells, twips):
                tcw = cell._element.get_or_add_tcPr().find(qn("w:tcW"))
                if tcw is not None:
                    tcw.set(qn("w:w"), str(tw))
                    tcw.set(qn("w:type"), "dxa")
        trpr = t.rows[0]._tr.get_or_add_trPr()
        hdr = OxmlElement("w:tblHeader")
        hdr.set(qn("w:val"), "true")
        trpr.append(hdr)
        spacer = self.doc.add_paragraph()
        spacer.paragraph_format.space_after = Pt(4)
        return t

    def _rich_cell(self, p, text, size):
        for k, line in enumerate(text.split("\n")):
            if k:
                p = p._parent.add_paragraph(style="ONho")
            for part in re.split(r"(\*\*[^*]+\*\*)", line):
                if part:
                    bold = part.startswith("**")
                    set_run_font(p.add_run(part[2:-2] if bold else part), size, bold=bold or None)

    def code(self, text):
        lines = text.strip("\n").split("\n")
        for i, line in enumerate(lines):
            p = self.doc.add_paragraph(style="Code")
            ppr = p._p.get_or_add_pPr()
            shd = OxmlElement("w:shd")
            shd.set(qn("w:val"), "clear")
            shd.set(qn("w:color"), "auto")
            shd.set(qn("w:fill"), "F2F2F2")
            ppr.append(shd)
            if i == len(lines) - 1:
                p.paragraph_format.space_after = Pt(8)
            if i == 0:
                p.paragraph_format.space_before = Pt(4)
            run = p.add_run(line if line else " ")
            set_run_font(run, 8.5, name="Courier New")

    def formula(self, text):
        p = self.doc.add_paragraph(style="CongThuc")
        set_run_font(p.add_run(text), italic=True)

    # ------------------------------------------------------------ mục lục
    def _toc_field(self, entries, instr, style_for):
        for i, (level, text) in enumerate(entries):
            p = self.doc.add_paragraph(style=style_for(level))
            if i == 0:
                for kind, val in (("begin", None), ("instr", instr), ("separate", None)):
                    r = OxmlElement("w:r")
                    if kind == "instr":
                        t = OxmlElement("w:instrText")
                        t.set(qn("xml:space"), "preserve")
                        t.text = f" {val} "
                        r.append(t)
                    else:
                        f = OxmlElement("w:fldChar")
                        f.set(qn("w:fldCharType"), kind)
                        r.append(f)
                    p._p.append(r)
            set_run_font(p.add_run(text))
            set_run_font(p.add_run("\t" + str(self.page_numbers.get(text, 0))))
            if i == len(entries) - 1:
                r = OxmlElement("w:r")
                f = OxmlElement("w:fldChar")
                f.set(qn("w:fldCharType"), "end")
                r.append(f)
                p._p.append(r)

    def build(self):
        self.fill_front_matter()
        # Thu thập trước danh sách đề mục / bảng / hình bằng một lượt "khô"
        dry = ReportBuilder.__new__(ReportBuilder)
        dry.__dict__.update({"doc": Document(TEMPLATE), "page_numbers": {}, "toc_entries": [], "tables": [],
                             "figures": [], "fig_no": {}, "tab_no": {}})
        dry._setup_styles()
        dry._setup_numbering()
        content.write(dry)
        toc = [(1, "DANH MỤC CÁC KÝ HIỆU, CHỮ VIẾT TẮT"), (1, "DANH MỤC CÁC BẢNG, HÌNH VẼ, ĐỒ THỊ")] + dry.toc_entries
        self.fig_no, self.tab_no = dry.fig_no, dry.tab_no

        self.title("MỤC LỤC")
        p = self.doc.add_paragraph(style="ONho")
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        set_run_font(p.add_run("Trang"), 13, bold=True)
        self._toc_field(toc, 'TOC \\o "1-2" \\z \\u', lambda lvl: f"TOC {lvl}")
        self.page_break()
        self.heading(1, "DANH MỤC CÁC BẢNG, HÌNH VẼ, ĐỒ THỊ")
        p = self.doc.add_paragraph(style="Heading 4")
        set_run_font(p.add_run("Danh mục bảng"))
        self._toc_field([(1, t) for t in dry.tables], 'TOC \\h \\z \\t "Bang,1"', lambda lvl: "Table of Figures")
        p = self.doc.add_paragraph(style="Heading 4")
        p.paragraph_format.space_before = Pt(14)
        set_run_font(p.add_run("Danh mục hình vẽ, đồ thị"))
        self._toc_field([(1, f) for f in dry.figures], 'TOC \\h \\z \\t "Hinh,1"', lambda lvl: "Table of Figures")
        self.toc_entries = [(1, "DANH MỤC CÁC KÝ HIỆU, CHỮ VIẾT TẮT"), (1, "DANH MỤC CÁC BẢNG, HÌNH VẼ, ĐỒ THỊ")]
        content.write(self)
        return self.doc


def caption_chapter(caption: str) -> str:
    return caption.split("|", 1)[0] if "|" in caption else "3"


# --------------------------------------------------------------------------- #
# Tính số trang bằng LibreOffice
# --------------------------------------------------------------------------- #
SOFFICE_HELPER = Path("/root/.claude/skills/synced/7b1c8360-20f0-47b6-be65-66c6cc07bda2_a4d62bfc-0df2-4a21-9f1a-"
                      "4213ef2aef9d/docx/scripts")


def to_pdf(docx_path: Path, out_dir: Path) -> Path:
    sys.path.insert(0, str(SOFFICE_HELPER))
    from office.soffice import run_soffice

    run_soffice(["--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(docx_path)], check=True,
                capture_output=True)
    return out_dir / (docx_path.stem + ".pdf")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def locate_pages(pdf: Path, doc_builder: ReportBuilder) -> dict[str, int]:
    out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    pages = [norm(p) for p in out.split("\f")]
    start = next(i for i, p in enumerate(pages) if "danh mục các ký hiệu, chữ viết tắt" in p)
    # trang chứa phần nội dung chính bắt đầu sau các trang mục lục/danh mục
    body_start = next(i for i, p in enumerate(pages) if i > start and p.startswith("mở đầu"))
    numbers = {"DANH MỤC CÁC KÝ HIỆU, CHỮ VIẾT TẮT": 1}
    dm = next(i for i, p in enumerate(pages) if i > start and p.startswith("danh mục các bảng, hình vẽ"))
    numbers["DANH MỤC CÁC BẢNG, HÌNH VẼ, ĐỒ THỊ"] = dm - start + 1
    cursor = body_start
    items = [t for _, t in doc_builder.toc_entries[2:]]
    ordered = []
    for el in doc_builder.doc.element.body.iterchildren():
        txt = "".join(t.text or "" for t in el.iter(qn("w:t"))).strip()
        if txt in items or txt in doc_builder.tables or txt in doc_builder.figures:
            ordered.append(txt)
    for txt in ordered:
        key = norm(txt)[:60]
        for i in range(cursor, len(pages)):
            if key in pages[i]:
                numbers[txt] = i - start + 1
                cursor = i
                break
        else:
            print("  ! không tìm thấy:", txt)
    return numbers


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="report_"))
    first = ReportBuilder()
    first.build()
    draft = tmp / "draft.docx"
    first.doc.save(draft)
    numbers = locate_pages(to_pdf(draft, tmp), first)
    final = ReportBuilder(numbers)
    final.build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    final.doc.save(OUTPUT)
    subprocess.run(["zip", "-dq", str(OUTPUT), "*/"], capture_output=True)
    pdf = to_pdf(OUTPUT, OUTPUT.parent)
    pages = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    print("Đã ghi", OUTPUT, "|", re.search(r"Pages:\s+\d+", pages).group(0))


if __name__ == "__main__":
    main()
