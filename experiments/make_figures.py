"""Vẽ lại biểu đồ ablation cho báo cáo từ kết quả đã lưu (outputs/experiments/ablation_results.csv): python experiments/make_figures.py"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "DejaVu Sans"
r = pd.read_csv(OUT / "ablation_results.csv", encoding="utf-8-sig").set_index("bien_the")
base = float(r.loc["Cấu hình chuẩn", "macro_f1_mean"]) * 100
NAVY, LIGHT = "#0b1b33", "#8fa6c6"
fig, (a, b) = plt.subplots(1, 2, figsize=(12.5, 4.6), gridspec_kw={"width_ratios": [1, 1.25]})
# (a) dùng phần nào của bài báo
rows = [("Chỉ tiêu đề", r.loc["Chỉ tiêu đề", "macro_f1_mean"] * 100), ("Tiêu đề + sapo", r.loc["Tiêu đề + sapo", "macro_f1_mean"] * 100),
        ("Chỉ nội dung", r.loc["Chỉ nội dung", "macro_f1_mean"] * 100), ("Cả ba (chuẩn)", base)]
y = np.arange(len(rows))[::-1]
a.barh(y, [v for _, v in rows], color=[LIGHT, LIGHT, NAVY, NAVY], height=0.62)
for yy, (_, v) in zip(y, rows):
    a.text(v - 1, yy, f"{v:.1f}", va="center", ha="right", color="white", fontsize=11, fontweight="bold")
a.set_yticks(y); a.set_yticklabels([n for n, _ in rows], fontsize=11); a.set_xlim(60, 92); a.set_xlabel("Macro-F1 (%) — 5-fold CV"); a.set_title("Máy đọc phần nào của bài báo?", fontsize=12, fontweight="bold")
# (b) thay đổi kỹ thuật
names = [("Tối đa 5.000 đặc trưng", "Chỉ giữ 5.000 từ"), ("Chỉ từ đơn (1-gram)", "Chỉ từ đơn (bỏ cặp từ)"), ("Bỏ log-tf (sublinear_tf=False)", "Bỏ log-tf"), ("Bỏ IDF (chỉ TF)", "Bỏ IDF"),
         ("Bỏ dấu tiếng Việt", "Bỏ dấu tiếng Việt"), ("1–3 gram", "Thêm bộ ba từ (1–3 gram)"), ("Tách từ (pyvi) + 1–2 gram", "Tách từ pyvi + 1–2 gram"), ("min_df = 5", "Loại từ hiếm hơn (min_df=5)")]
vals = [(lab, float(r.loc[k, "delta_vs_base"]) * 100, float(r.loc[k, "paired_t_p"])) for k, lab in names]
y = np.arange(len(vals))[::-1]
b.barh(y, [v for _, v, _ in vals], color=[NAVY if v >= 0 else LIGHT for _, v, _ in vals], height=0.62)
for yy, (_, v, p) in zip(y, vals):
    b.text(v + (0.04 if v >= 0 else -0.04), yy, f"{v:+.2f}" + (" *" if p < 0.05 else ""), va="center", ha="left" if v >= 0 else "right", fontsize=10.5, fontweight="bold" if p < 0.05 else "normal")
b.axvline(0, color="k", lw=1); b.set_yticks(y); b.set_yticklabels([n for n, _, _ in vals], fontsize=10.5); b.set_xlim(-1.6, 0.9)
b.set_xlabel(f"Thay đổi Macro-F1 so với chuẩn ({base:.2f}%), điểm %"); b.set_title("Đổi một chi tiết kỹ thuật thì sao?", fontsize=12, fontweight="bold")
plt.suptitle("Ablation: mỗi lần chỉ đổi một thành phần (5-fold CV trên train + val, không dùng tập kiểm thử)", fontsize=11, y=0.995)
plt.tight_layout(rect=(0, 0.04, 1, 1)); fig.text(0.99, 0.01, "* khác biệt có ý nghĩa (p < 0,05, kiểm định t ghép cặp trên 5 fold)", ha="right", fontsize=9.5, color="#26354d")
plt.savefig(OUT / "ablation.png", dpi=150); plt.close()
print("đã vẽ ablation.png")
