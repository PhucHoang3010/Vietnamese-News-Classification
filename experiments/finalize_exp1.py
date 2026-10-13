"""Chọn C cho Linear SVM từ thí nghiệm 1 theo 2 quy tắc và ghi ra file cho các thí nghiệm sau.
 - 'tốt nhất': C có Macro-F1 CV cao nhất
 - 'quy tắc 1 SE': C nhỏ nhất (mô hình đơn giản nhất) có CV >= tốt nhất - 1 sai số chuẩn (độ lệch chuẩn/√5)
Mô hình cuối dùng quy tắc 1 SE (được khuyến nghị khi các cấu hình chênh nhau trong sai số)."""
import sys, math
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
g = load_json("tuning_grids.json")["Linear SVM"]
best = max(g, key=lambda r: r["cv_mean"])
se = best["cv_std"] / math.sqrt(5)
ok = [r for r in g if r["cv_mean"] >= best["cv_mean"] - se]
simple = min(ok, key=lambda r: r["params"]["C"])
out = dict(C=simple["params"]["C"], rule="1-SE", best_C=best["params"]["C"], best_cv=best["cv_mean"], best_se=se, chosen_cv=simple["cv_mean"], grid=g)
save_json(out, "tuning_results_best_svm.json")
print(json.dumps({k: v for k, v in out.items() if k != "grid"}, ensure_ascii=False))
for r in g: print(r["params"], round(r["cv_mean"], 4), "±", round(r["cv_std"], 4))
