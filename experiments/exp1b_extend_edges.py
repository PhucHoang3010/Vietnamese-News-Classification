"""Thí nghiệm 1b — Nếu giá trị tối ưu nằm ở BIÊN của lưới tìm kiếm, mở rộng lưới cho tới khi tối ưu nằm bên trong.
Chỉ dùng 5-fold CV trên tập huấn luyện (như thí nghiệm 1). Ghi đè kết quả mở rộng vào tuning_grids.json."""
import sys, time
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

df, i_tr, i_va, i_te = load(); check_split(df, i_tr, i_va, i_te)
X_tr, y_tr = df.text.iloc[i_tr], df.label.iloc[i_tr]
cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
EXT = {"Linear SVM": (LinearSVC(), "C", [16, 32, 64]),
       "Logistic Regression": (LogisticRegression(max_iter=3000), "C", [100, 300]),
       "Complement Naive Bayes": (ComplementNB(), "alpha", [0.003, 0.01])}
grids = load_json("tuning_grids.json")
only = sys.argv[1:] or list(EXT)
for name in only:
    clf, par, vals = EXT[name]
    t0 = time.time()
    gs = GridSearchCV(Pipeline([("tfidf", tfidf()), ("clf", clf)]), {f"clf__{par}": vals}, scoring="f1_macro", cv=cv, n_jobs=4, refit=False).fit(X_tr, y_tr)
    r = gs.cv_results_
    new = [dict(params={par: v}, cv_mean=float(m), cv_std=float(s)) for v, m, s in zip(vals, r["mean_test_score"], r["std_test_score"])]
    grids[name] = sorted(grids[name] + new, key=lambda d: list(d["params"].values())[0])
    for d in new: print(f"{name:25s} {par}={list(d['params'].values())[0]:<6} CV={d['cv_mean']:.4f}±{d['cv_std']:.4f}", flush=True)
    print(f"  ({time.time()-t0:.0f}s)")
save_json(grids, "tuning_grids.json")
