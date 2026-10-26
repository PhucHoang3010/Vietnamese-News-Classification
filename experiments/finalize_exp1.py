"""Chốt C cho Linear SVM sau thí nghiệm 1/1b.
C = 2 đã được chọn ban đầu bằng GridSearchCV 3-fold (train.py). Lưới mở rộng với 5-fold cho thấy Macro-F1 CV BẰNG PHẲNG khi C tăng:
chênh giữa các C từ 1 trở lên (0,8835–0,8861) nhỏ hơn độ lệch chuẩn giữa các fold (~0,45 điểm), nên KHÔNG đổi mô hình (tránh đổi theo nhiễu). Ghi lại số liệu để báo cáo."""
import sys, math
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
g = sorted(load_json("tuning_grids.json")["Linear SVM"], key=lambda r: r["params"]["C"])
best = max(g, key=lambda r: r["cv_mean"]); se = best["cv_std"] / math.sqrt(5)
cur = next(r for r in g if r["params"]["C"] == 2)
plateau = [r for r in g if r["params"]["C"] >= 1]
out = dict(C=2.0, best_C=best["params"]["C"], best_cv=best["cv_mean"], best_se=se, chosen_cv=cur["cv_mean"], gap_to_best=best["cv_mean"] - cur["cv_mean"],
           plateau_C_range=[plateau[0]["params"]["C"], plateau[-1]["params"]["C"]], plateau_cv_min=min(r["cv_mean"] for r in plateau), plateau_cv_max=max(r["cv_mean"] for r in plateau),
           rule="giữ C=2: C tốt nhất của lưới mở rộng chỉ hơn %.2f điểm Macro-F1, nhỏ hơn độ lệch chuẩn giữa các fold (%.2f điểm) nên không đủ để đổi mô hình" % (100 * (best["cv_mean"] - cur["cv_mean"]), 100 * cur["cv_std"]), grid=g)
save_json(out, "tuning_results_best_svm.json")
print(json.dumps({k: v for k, v in out.items() if k != "grid"}, ensure_ascii=False))
for r in g: print(r["params"], round(r["cv_mean"], 4), "+-", round(r["cv_std"], 4))
