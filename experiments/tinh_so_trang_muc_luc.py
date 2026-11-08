"""Tính số trang của các đề mục để điền vào MỤC LỤC của báo cáo Word.

Mục lục trong BAO_CAO_DO_AN.docx là trường Word thật (Word cập nhật được bằng cách bấm chuột phải vào mục lục → Cập nhật trường),
nhưng khi chưa cập nhật nó hiện các số trang lấy từ outputs/toc_pages.json do tập lệnh này tạo ra.

Cách dùng (cần pdftotext của poppler):
  1) python make_report.py                         sinh BAO_CAO_DO_AN.docx
  2) xuất BAO_CAO_DO_AN.docx ra PDF (Word: Lưu thành PDF; hoặc LibreOffice)
  3) python experiments/tinh_so_trang_muc_luc.py BAO_CAO_DO_AN.pdf
  4) python make_report.py                         sinh lại, lần này mục lục đã có số trang
Các trang bìa (bìa chính, bìa phụ, danh sách nhóm) không đánh số; số trang bắt đầu từ 1 ở đề mục đầu tiên (Danh mục các ký hiệu, chữ viết tắt), nên số trang
ghi vào mục lục là số in ở chân trang chứ không phải thứ tự trang trong tệp PDF. Tập lệnh cũng tính số trang của từng bảng và hình
(khóa "Bảng n", "Hình n") cho Danh mục bảng, hình vẽ.
Số trang tính theo PDF, có thể lệch vài trang so với Word nếu phông chữ khác nhau; khi đó hãy cập nhật trường trong Word.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parent.parent
pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "BAO_CAO_DO_AN.pdf"
docx = ROOT / "BAO_CAO_DO_AN.docx"

_doc = Document(docx)
heads = [p.text for p in _doc.paragraphs if p.style.name in ("Heading 1", "Heading 2")]
tabs = [p.text.split(".")[0] for p in _doc.paragraphs if p.style.name == "Caption Table"]     # "Bảng 5"
figs = [p.text.split(".")[0] for p in _doc.paragraphs if p.style.name == "Caption Figure"]    # "Hình 3"
text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
pages = [[re.sub(r"\s+", " ", ln).strip() for ln in pg.split("\n")] for pg in text.split("\f")]
if pages and not any(pages[-1]):
    pages.pop()


def is_toc_line(ln):
    return "....." in ln


out, cur, first = {}, 0, None
for h in heads:
    key = re.sub(r"\s+", " ", h).strip()
    found = None
    for i in range(cur, len(pages)):
        if any(ln.startswith(key[:38]) and not is_toc_line(ln) for ln in pages[i]):
            found = i
            break
    if found is None:
        print("không tìm thấy đề mục:", h)
        continue
    if first is None:
        first = found                     # trang của đề mục đầu tiên = trang số 1 (các trang bìa phía trước không có số)
    out[h] = found - first + 1
    cur = found
# chú thích bảng, hình: dòng bắt đầu bằng "Bảng n." / "Hình n." (bỏ qua các dòng của danh mục có dấu chấm dẫn)
for labels in (tabs, figs):
    cur = 0
    for lab in labels:
        for i in range(cur, len(pages)):
            if any(ln.startswith(lab + ".") and not is_toc_line(ln) for ln in pages[i]):
                out[lab] = i - first + 1
                cur = i
                break
        else:
            print("không tìm thấy chú thích:", lab)
(ROOT / "outputs" / "toc_pages.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"đã ghi {len(out)} mục (đề mục {len(heads)}, bảng {len(tabs)}, hình {len(figs)}) vào outputs/toc_pages.json; tổng {len(pages)} trang")
