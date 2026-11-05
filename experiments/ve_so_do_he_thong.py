"""Vẽ sơ đồ tổng thể của hệ thống cho báo cáo: outputs/he_thong.png      python experiments/ve_so_do_he_thong.py"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).resolve().parent.parent / "outputs"
plt.rcParams["font.family"] = "DejaVu Sans"
BLUE, TEAL, INK = "#0a74c0", "#0a7f84", "#12263a"

fig, ax = plt.subplots(figsize=(8.4, 5.2))
ax.set_xlim(0, 100); ax.set_ylim(0, 62); ax.axis("off")


def box(x, y, w, h, text, fc, ec, tc=INK, fs=8.8, bold_first=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.6", fc=fc, ec=ec, lw=1.6))
    lines = text.split("\n")
    n = len(lines)
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y + h / 2 + (n / 2 - 0.5 - i) * 3.4, ln, ha="center", va="center", fontsize=fs, color=tc,
                fontweight="bold" if (i == 0 and bold_first) else "normal")


def arrow(x1, y1, x2, y2, color=INK):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6, shrinkA=0, shrinkB=0))


# hàng 1: từ dữ liệu đến mô hình
Y1, H1, W1 = 44, 17, 21.5
xs = [0.5, 26.2, 51.9, 77.6]
steps = ["1. Dữ liệu\n5.500 bài báo\n11 chuyên mục\nchia 70 / 15 / 15", "2. Tiền xử lý\nUnicode NFC,\nchữ thường,\nbỏ URL, số, dấu câu",
         "3. TF-IDF\nđơn từ + cặp từ\n200.000 đặc trưng\n(log-tf, IDF)", "4. Linear SVM\n(C = 2)\nmỗi chuyên mục\nmột vector trọng số"]
for x, t in zip(xs, steps):
    box(x, Y1, W1, H1, t, "#e8f2fd", BLUE)
for a, b in zip(xs, xs[1:]):
    arrow(a + W1 + 0.7, Y1 + H1 / 2, b - 0.7, Y1 + H1 / 2, BLUE)

# hàng 2: ba kết quả từ điểm SVM
Y2, H2, W2 = 21, 14, 30
x2 = [0.5, 35, 69.5]
outs = ["Chuyên mục dự đoán\nkèm độ tự tin (%)\nsoftmax(T × điểm), T = 4,3", "Chuyên mục có thể thuộc\n(dự đoán có bảo đảm)\nconformal, mức 90 / 95 / 99%", "Giải thích dự đoán\nđóng góp của từng từ\nvào điểm chuyên mục"]
for x, t in zip(x2, outs):
    box(x, Y2, W2, H2, t, "#e0f5f4", TEAL)
    arrow(xs[3] + W1 / 2, Y1 - 0.8, x + W2 / 2, Y2 + H2 + 0.8, TEAL)

# hàng 3: website
Y3, H3 = 1, 13
box(0.5, Y3, 99, H3, "Website tin tức VnNews (Flask)\nphân loại trực tiếp · tin theo chuyên mục · Hỏi AI có dẫn nguồn · tìm kiếm nâng cao\nbộ sưu tập · bình luận · tóm tắt · gom sự kiện · gợi ý bài đọc",
    BLUE, BLUE, tc="white", fs=8.8)
for x in x2:
    arrow(x + W2 / 2, Y2 - 0.8, x + W2 / 2, Y3 + H3 + 0.8, BLUE)

plt.savefig(OUT / "he_thong.png", dpi=200, bbox_inches="tight", facecolor="white")
print("đã vẽ", OUT / "he_thong.png")
