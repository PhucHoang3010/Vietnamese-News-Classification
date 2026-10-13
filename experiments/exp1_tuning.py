"""Thí nghiệm 1 — So sánh CÔNG BẰNG: mỗi mô hình đều được chỉnh siêu tham số bằng 5-fold CV trên TẬP HUẤN LUYỆN.
Tập kiểm định/kiểm thử KHÔNG tham gia chọn tham số; chỉ báo cáo sau khi đã chọn xong.
Chạy:  python experiments/exp1_tuning.py [--quick]
"""
import sys, time, tempfile
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import TruncatedSVD
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.naive_bayes import ComplementNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import Normalizer
from sklearn.svm import LinearSVC

QUICK = "--quick" in sys.argv
plt.rcParams["font.family"] = "DejaVu Sans"
df, i_tr, i_va, i_te = load(); check_split(df, i_tr, i_va, i_te)
X_tr, y_tr = df.text.iloc[i_tr], df.label.iloc[i_tr]
X_va, y_va = df.text.iloc[i_va], df.label.iloc[i_va]
X_te, y_te = df.text.iloc[i_te], df.label.iloc[i_te]
if QUICK:
    X_tr, y_tr = X_tr.iloc[:600], y_tr.iloc[:600]


def pipe(clf):
    return Pipeline([("tfidf", tfidf()), ("clf", clf)])


MODELS = {
    "Đoán lớp phổ biến nhất (baseline)": (pipe(DummyClassifier(strategy="most_frequent")), {}),
    "Complement Naive Bayes": (pipe(ComplementNB()), {"clf__alpha": [0.03, 0.1, 0.3, 1.0]}),
    "k-NN (cosine)": (pipe(KNeighborsClassifier(metric="cosine", algorithm="brute", weights="distance")), {"clf__n_neighbors": [5, 11, 21]}),
    "Logistic Regression": (pipe(LogisticRegression(max_iter=2000)), {"clf__C": [3, 10, 30]}),
    "Linear SVM": (pipe(LinearSVC()), {"clf__C": [0.1, 0.3, 1, 2, 4, 8]}),
    "Random Forest": (pipe(RandomForestClassifier(n_estimators=300, random_state=SEED, n_jobs=1)), {"clf__min_samples_leaf": [1, 2], "clf__max_features": ["sqrt", "log2"]}),
    "MLP nhỏ (TF-IDF → SVD 300 → 256 nơ-ron)": (Pipeline([("tfidf", tfidf()), ("svd", TruncatedSVD(300, random_state=SEED)), ("norm", Normalizer()),
                                                       ("clf", MLPClassifier((256,), early_stopping=True, max_iter=200, random_state=SEED))]), {"clf__alpha": [1e-4, 1e-2]}),
}
if QUICK:
    MODELS = {k: v for k, v in MODELS.items() if k in ("Linear SVM", "Complement Naive Bayes")}
cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
rows, preds, grids = [], {"id": df.id.iloc[i_te].astype(int).values, "truth": y_te.values}, {}
for name, (p, grid) in MODELS.items():
    t0 = time.time()
    gs = GridSearchCV(p, grid or [{}], scoring="f1_macro", cv=cv, n_jobs=4, refit=True, return_train_score=True).fit(X_tr, y_tr)
    best = gs.best_estimator_
    r = pd.DataFrame(gs.cv_results_)
    k = gs.best_index_
    t1 = time.time(); pv = best.predict(X_va); pt = best.predict(X_te); lat = (time.time() - t1) / (len(X_va) + len(X_te)) * 1000
    with tempfile.NamedTemporaryFile(suffix=".joblib") as f:
        joblib.dump(best, f.name, compress=3); size = Path(f.name).stat().st_size / 1e6
    sv, st = scores(y_va, pv), scores(y_te, pt)
    rows.append(dict(model=name, best_params=str({a.replace("clf__", ""): b for a, b in gs.best_params_.items()}),
                     cv_macro_f1_mean=r.mean_test_score[k], cv_macro_f1_std=r.std_test_score[k], train_macro_f1_mean=r.mean_train_score[k],
                     val_acc=sv["acc"], val_macro_f1=sv["macro_f1"], test_acc=st["acc"], test_macro_f1=st["macro_f1"],
                     fit_sec=float(gs.refit_time_), ms_per_article=lat, model_mb=size, n_configs=len(r)))
    preds[name] = pt
    grids[name] = [dict(params={a.replace("clf__", ""): b for a, b in pp.items()}, cv_mean=float(m), cv_std=float(s)) for pp, m, s in zip(r.params, r.mean_test_score, r.std_test_score)]
    print(f"{name:45s} CV={r.mean_test_score[k]:.4f}±{r.std_test_score[k]:.4f} val={sv['macro_f1']:.4f} test={st['macro_f1']:.4f}  ({time.time()-t0:.0f}s) {gs.best_params_}", flush=True)
res = pd.DataFrame(rows)
if not QUICK:
    res.to_csv(OUT / "tuning_results.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(preds).to_csv(OUT / "test_predictions.csv", index=False, encoding="utf-8-sig")
    save_json(grids, "tuning_grids.json")
    # biểu đồ
    d = res[~res.model.str.startswith("Đoán")].sort_values("cv_macro_f1_mean")
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.barh(d.model, d.cv_macro_f1_mean, xerr=d.cv_macro_f1_std, color="#0b1b33", capsize=3)
    for y, (m, s) in enumerate(zip(d.cv_macro_f1_mean, d.cv_macro_f1_std)):
        ax.text(m + s + 0.004, y, f"{m:.3f}", va="center", fontsize=9)
    ax.set_xlim(0.5, 1); ax.set_xlabel("Macro-F1 (CV 5-fold trên tập huấn luyện, trung bình ± độ lệch chuẩn)")
    ax.set_title("So sánh công bằng: mọi mô hình đều đã chỉnh siêu tham số"); plt.tight_layout(); plt.savefig(OUT / "tuning_results.png", dpi=150); plt.close()
print(res[["model", "cv_macro_f1_mean", "cv_macro_f1_std", "val_macro_f1", "test_macro_f1"]].to_string())
