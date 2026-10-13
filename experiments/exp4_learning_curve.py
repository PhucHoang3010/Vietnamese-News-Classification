"""Thí nghiệm 4 — Đường cong học: kết quả thay đổi thế nào khi tăng lượng dữ liệu huấn luyện? (Linear SVM, tập val)"""
import sys, time
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
from sklearn.svm import LinearSVC

plt.rcParams["font.family"] = "DejaVu Sans"
df, i_tr, i_va, i_te = load(); check_split(df, i_tr, i_va, i_te)
C = load_json("tuning_results_best_svm.json")["C"]
Xtr, ytr = df.text.values[i_tr], df.label.values[i_tr]; Xva, yva = df.text.values[i_va], df.label.values[i_va]
FR = [0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0]


def job(fr, rep):
    if fr >= 1.0:
        sel = np.arange(len(ytr))
    else:
        sel, _ = train_test_split(np.arange(len(ytr)), train_size=fr, stratify=ytr, random_state=SEED + rep)
    vec = tfidf(); A = vec.fit_transform(Xtr[sel]); V = vec.transform(Xva)
    m = LinearSVC(C=C).fit(A, ytr[sel])
    return dict(frac=fr, rep=rep, n=len(sel), train_acc=float((m.predict(A) == ytr[sel]).mean()), **{("val_" + k): v for k, v in scores(yva, m.predict(V)).items()})


t0 = time.time()
r = Parallel(n_jobs=4)(delayed(job)(fr, rep) for fr in FR for rep in (range(5) if fr < 1 else range(1)))
d = pd.DataFrame(r); d.to_csv(OUT / "learning_curve_raw.csv", index=False, encoding="utf-8-sig")
g = d.groupby(["frac", "n"]).agg(train_acc=("train_acc", "mean"), val_acc=("val_acc", "mean"), val_f1=("val_macro_f1", "mean"), val_f1_std=("val_macro_f1", "std")).reset_index()
g.to_csv(OUT / "learning_curve.csv", index=False, encoding="utf-8-sig"); print(g.round(4).to_string())
fig, ax = plt.subplots(figsize=(7.5, 4.2))
ax.plot(g.n, g.train_acc * 100, "o-", color="#8fa6c6", label="Accuracy trên tập huấn luyện")
ax.errorbar(g.n, g.val_f1 * 100, yerr=g.val_f1_std.fillna(0) * 100, fmt="o-", color="#0b1b33", capsize=3, label="Macro-F1 trên tập kiểm định")
ax.set_xlabel("Số bài huấn luyện"); ax.set_ylabel("%"); ax.set_ylim(40, 101); ax.grid(alpha=.3); ax.legend(loc="center right")
ax.set_title("Đường cong học: thêm dữ liệu có giúp không?"); plt.tight_layout(); plt.savefig(OUT / "learning_curve.png", dpi=150); plt.close()
print("xong", round(time.time() - t0), "s")
