"""Thí nghiệm 3 — Độ ổn định & độ tin cậy thống kê của kết quả.
 (a) 10 phép chia ngẫu nhiên 70/15/15 khác nhau (seed 0–9): Accuracy / Macro-F1 trên tập test của mỗi phép chia
 (b) 5-fold CV lặp 3 lần trên toàn bộ 5.500 bài
 (c) Khoảng tin cậy 95% bootstrap trên tập test chính thức + kiểm định McNemar giữa các mô hình
 (d) Kiểm tra rò rỉ 'gần trùng': độ giống cosine lớn nhất giữa mỗi bài test và các bài train
Chạy sau thí nghiệm 1:  python experiments/exp3_stability.py
"""
import sys, time, ast
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.naive_bayes import ComplementNB
from sklearn.svm import LinearSVC

plt.rcParams["font.family"] = "DejaVu Sans"
df, i_tr, i_va, i_te = load(); check_split(df, i_tr, i_va, i_te)
tun = pd.read_csv(OUT / "tuning_results.csv"); P = {r.model: ast.literal_eval(r.best_params) for r in tun.itertuples()}
svmC = load_json("tuning_results_best_svm.json")["C"]
mk = {"Linear SVM": lambda: LinearSVC(C=svmC),
      "Complement Naive Bayes": lambda: ComplementNB(**P["Complement Naive Bayes"]),
      "Logistic Regression": lambda: LogisticRegression(max_iter=2000, **P["Logistic Regression"])}
X, y = df.text.values, df.label.values


def one_split(seed):
    idx = np.arange(len(df))
    a, b = train_test_split(idx, test_size=0.30, stratify=y, random_state=seed)
    _, c = train_test_split(b, test_size=0.50, stratify=y[b], random_state=seed)
    vec = tfidf(); Xa = vec.fit_transform(X[a]); Xc = vec.transform(X[c])
    out = {}
    for n, f in mk.items():
        s = scores(y[c], f().fit(Xa, y[a]).predict(Xc)); out[n] = s
    return seed, out


def one_fold(tr, te):
    vec = tfidf(); Xa = vec.fit_transform(X[tr]); Xb = vec.transform(X[te])
    return {n: scores(y[te], f().fit(Xa, y[tr]).predict(Xb)) for n, f in mk.items()}


t0 = time.time()
sp = Parallel(n_jobs=4)(delayed(one_split)(s) for s in range(10))
rows = [dict(seed=s, model=n, **v) for s, o in sp for n, v in o.items()]
split_df = pd.DataFrame(rows); split_df.to_csv(OUT / "stability_splits.csv", index=False, encoding="utf-8-sig")
print("(a) xong", round(time.time() - t0), "s")
rk = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED)
cvr = Parallel(n_jobs=4)(delayed(one_fold)(tr, te) for tr, te in rk.split(X, y))
cv_rows = [dict(fold=i, model=n, **v) for i, o in enumerate(cvr) for n, v in o.items()]
cv_df = pd.DataFrame(cv_rows); cv_df.to_csv(OUT / "stability_cv_repeated.csv", index=False, encoding="utf-8-sig")
print("(b) xong", round(time.time() - t0), "s")
summ = []
for name in mk:
    a = split_df[split_df.model == name]; b = cv_df[cv_df.model == name]
    summ.append(dict(model=name, split_acc_mean=a.acc.mean(), split_acc_std=a.acc.std(ddof=1), split_f1_mean=a.macro_f1.mean(), split_f1_std=a.macro_f1.std(ddof=1),
                     split_f1_min=a.macro_f1.min(), split_f1_max=a.macro_f1.max(),
                     cv_f1_mean=b.macro_f1.mean(), cv_f1_std=b.macro_f1.std(ddof=1), cv_acc_mean=b.acc.mean(), cv_acc_std=b.acc.std(ddof=1)))
summ = pd.DataFrame(summ); summ.to_csv(OUT / "stability_summary.csv", index=False, encoding="utf-8-sig"); print(summ.round(4).to_string())

# (c) bootstrap + McNemar trên tập test chính thức
tp = pd.read_csv(OUT / "test_predictions.csv"); truth = tp.truth.values
rng = np.random.default_rng(SEED); B = 2000; n = len(tp); ix = rng.integers(0, n, (B, n))
models = [c for c in tp.columns if c not in ("id", "truth") and not c.startswith("Đoán")]
svm = "Linear SVM"
# dùng dự đoán của mô hình SVM cuối (C theo quy tắc 1 SE) thay vì C tốt nhất của thí nghiệm 1 nếu khác nhau
vec = tfidf(); Xa = vec.fit_transform(df.text.iloc[i_tr]); Xt = vec.transform(df.text.iloc[i_te])
final = LinearSVC(C=svmC).fit(Xa, df.label.iloc[i_tr]); tp[svm] = final.predict(Xt)
def mf1(p, t): return f1_score(t, p, average="macro")
def boot(p):
    c = (p == truth)
    acc = c[ix].mean(1); f = np.array([mf1(p[i], truth[i]) for i in ix])
    return acc, f
ci = {}
accs, fs = boot(tp[svm].values)
ci["Linear SVM"] = dict(acc=float(np.mean(tp[svm].values == truth)), acc_lo=float(np.percentile(accs, 2.5)), acc_hi=float(np.percentile(accs, 97.5)),
                        f1=float(mf1(tp[svm].values, truth)), f1_lo=float(np.percentile(fs, 2.5)), f1_hi=float(np.percentile(fs, 97.5)))
print("CI SVM:", ci["Linear SVM"])
mc = []
for m in models:
    if m == svm: continue
    a, b = (tp[svm].values == truth), (tp[m].values == truth)
    n01, n10 = int(((~a) & b).sum()), int((a & (~b)).sum())           # SVM sai/mô hình kia đúng ; SVM đúng/mô hình kia sai
    p = float(stats.binomtest(min(n01, n10), n01 + n10, 0.5).pvalue) if n01 + n10 else 1.0
    d = (a.astype(int) - b.astype(int))[ix].mean(1)                    # chênh Accuracy bootstrap
    mc.append(dict(vs=m, svm_only_right=n10, other_only_right=n01, mcnemar_p=min(1.0, p), acc_diff=float(a.mean() - b.mean()),
                   diff_lo=float(np.percentile(d, 2.5)), diff_hi=float(np.percentile(d, 97.5))))
mc = pd.DataFrame(mc); mc.to_csv(OUT / "significance_vs_svm.csv", index=False, encoding="utf-8-sig"); print(mc.round(4).to_string())
save_json(ci, "bootstrap_ci.json")

# (d) gần trùng giữa test và train
sim = (Xt @ Xa.T).toarray(); mx = sim.max(1)
ok = (tp[svm].values == truth)
nd = dict(n_test=int(len(mx)), median=float(np.median(mx)), p90=float(np.percentile(mx, 90)), max=float(mx.max()))
for th in (0.5, 0.7, 0.8, 0.9):
    m = mx >= th; nd[f"n_ge_{th}"] = int(m.sum()); nd[f"acc_ge_{th}"] = float(ok[m].mean()) if m.any() else None
    nd[f"acc_lt_{th}"] = float(ok[~m].mean()) if (~m).any() else None
save_json(nd, "near_duplicates.json"); print(nd)
fig, ax = plt.subplots(figsize=(7, 3.6)); ax.hist(mx, bins=30, color="#0b1b33"); ax.set_xlabel("Độ giống cosine lớn nhất với một bài trong tập huấn luyện"); ax.set_ylabel("Số bài test")
ax.set_title("Bài test có 'gần trùng' với bài huấn luyện không?"); plt.tight_layout(); plt.savefig(OUT / "near_duplicates.png", dpi=150); plt.close()
# biểu đồ ổn định
fig, ax = plt.subplots(figsize=(8.5, 4))
for k, name in enumerate(mk):
    a = split_df[split_df.model == name].macro_f1.values * 100
    ax.scatter(a, np.full(len(a), k) + np.random.default_rng(1).uniform(-.12, .12, len(a)), s=28, color="#0b1b33", alpha=.8)
    ax.plot([a.mean()] * 2, [k - .3, k + .3], color="#c0392b", lw=2)
ax.set_yticks(range(len(mk))); ax.set_yticklabels(list(mk)); ax.set_xlabel("Macro-F1 (%) trên tập test của 10 phép chia ngẫu nhiên (vạch đỏ = trung bình)")
ax.set_title("Kết quả có phụ thuộc vào cách chia dữ liệu không?"); plt.tight_layout(); plt.savefig(OUT / "stability.png", dpi=150); plt.close()
print("xong", round(time.time() - t0), "s")
