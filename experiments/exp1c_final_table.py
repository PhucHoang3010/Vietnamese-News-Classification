"""Thí nghiệm 1c — Bảng so sánh cuối: mỗi mô hình dùng cấu hình tốt nhất theo CV (sau khi mở rộng lưới), riêng Linear SVM giữ C=2 (xem finalize_exp1.py).
Tính lại Accuracy/Macro-F1 trên tập kiểm định (và kiểm thử, chỉ để báo cáo) cho các mô hình có tham số thay đổi sau khi mở rộng lưới."""
import sys, time, tempfile
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

plt.rcParams["font.family"] = "DejaVu Sans"
df, i_tr, i_va, i_te = load(); check_split(df, i_tr, i_va, i_te)
X_tr, y_tr, X_va, y_va, X_te, y_te = df.text.iloc[i_tr], df.label.iloc[i_tr], df.text.iloc[i_va], df.label.iloc[i_va], df.text.iloc[i_te], df.label.iloc[i_te]
grids = load_json("tuning_grids.json"); base = pd.read_csv(OUT / "tuning_results.csv"); svm = load_json("tuning_results_best_svm.json")
best = lambda n: max(grids[n], key=lambda r: r["cv_mean"])
cfg = {"Linear SVM": (lambda: LinearSVC(C=2.0), {"C": 2.0}, next(r for r in grids["Linear SVM"] if r["params"]["C"] == 2)),
       "Logistic Regression": (lambda: LogisticRegression(max_iter=3000, C=best("Logistic Regression")["params"]["C"]), best("Logistic Regression")["params"], best("Logistic Regression")),
       "Complement Naive Bayes": (lambda: ComplementNB(alpha=best("Complement Naive Bayes")["params"]["alpha"]), best("Complement Naive Bayes")["params"], best("Complement Naive Bayes"))}
rows = []
for r in base.itertuples():
    if r.model not in cfg:
        rows.append(r._asdict() | {}); continue
    mk, par, g = cfg[r.model]
    p = Pipeline([("tfidf", tfidf()), ("clf", mk())]); t0 = time.time(); p.fit(X_tr, y_tr); fit = time.time() - t0
    t1 = time.time(); pv = p.predict(X_va); pt = p.predict(X_te); lat = (time.time() - t1) / (len(X_va) + len(X_te)) * 1000
    with tempfile.NamedTemporaryFile(suffix=".joblib") as f:
        joblib.dump(p, f.name, compress=3); mb = Path(f.name).stat().st_size / 1e6
    sv, st = scores(y_va, pv), scores(y_te, pt)
    d = r._asdict(); d.update(best_params=str(par), cv_macro_f1_mean=g["cv_mean"], cv_macro_f1_std=g["cv_std"], val_acc=sv["acc"], val_macro_f1=sv["macro_f1"], test_acc=st["acc"], test_macro_f1=st["macro_f1"], fit_sec=fit, ms_per_article=lat, model_mb=mb)
    rows.append(d); print(f"{r.model:28s} {par}  CV={g['cv_mean']:.4f}±{g['cv_std']:.4f} val={sv['macro_f1']:.4f}", flush=True)
res = pd.DataFrame(rows).drop(columns=["Index"], errors="ignore")
res.to_csv(OUT / "tuning_final.csv", index=False, encoding="utf-8-sig")
d = res[~res.model.str.startswith("Đoán")].sort_values("cv_macro_f1_mean")
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.barh(d.model, d.cv_macro_f1_mean, xerr=d.cv_macro_f1_std, color="#0b1b33", capsize=3)
for y, (m, s) in enumerate(zip(d.cv_macro_f1_mean, d.cv_macro_f1_std)): ax.text(m + s + 0.004, y, f"{m:.3f}", va="center", fontsize=9)
ax.set_xlim(0.5, 1); ax.set_xlabel("Macro-F1 (CV 5-fold trên tập huấn luyện, trung bình ± độ lệch chuẩn)"); ax.set_title("So sánh công bằng: mọi mô hình đều đã chỉnh siêu tham số")
plt.tight_layout(); plt.savefig(OUT / "tuning_results.png", dpi=150); plt.close()
print(res[["model", "best_params", "cv_macro_f1_mean", "cv_macro_f1_std", "val_acc", "val_macro_f1", "fit_sec", "model_mb"]].round(4).to_string())
