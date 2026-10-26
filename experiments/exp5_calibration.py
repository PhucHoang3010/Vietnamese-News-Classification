"""Thí nghiệm 5 — 'Độ tin cậy' của mô hình có đáng tin không? (hiệu chỉnh xác suất + dự đoán có chọn lọc)
Mô hình: Linear SVM cuối. So 4 cách tạo 'xác suất' trên tập TEST chính thức (tham số hiệu chỉnh chỉ học trên train/val):
  1) softmax(3×điểm)  — hệ số ban đầu của website   2) softmax(T×điểm), T chọn trên tập val (temperature scaling) — website hiện dùng T làm tròn 4,3
  3) CalibratedClassifierCV (Platt, 5-fold trên train)   4) Logistic Regression
"""
import sys, time, ast
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

plt.rcParams["font.family"] = "DejaVu Sans"
df, i_tr, i_va, i_te = load(); check_split(df, i_tr, i_va, i_te)
C = load_json("tuning_results_best_svm.json")["C"]
lrp = max(load_json("tuning_grids.json")["Logistic Regression"], key=lambda r: r["cv_mean"])["params"]
vec = tfidf().fit(df.text.iloc[i_tr]); A, V, T = (vec.transform(df.text.iloc[i]) for i in (i_tr, i_va, i_te))
ytr, yva, yte = (df.label.iloc[i].values for i in (i_tr, i_va, i_te))
svm = LinearSVC(C=C).fit(A, ytr); cls = svm.classes_
sv, st = svm.decision_function(V), svm.decision_function(T)
yv_i = np.searchsorted(cls, yva); yt_i = np.searchsorted(cls, yte)


def softmax(s, k):
    z = s * k; z = z - z.max(1, keepdims=True); e = np.exp(z); return e / e.sum(1, keepdims=True)


def metrics(P, y_i):
    conf = P.max(1); pred = P.argmax(1); ok = (pred == y_i)
    bins = np.linspace(0, 1, 11); ece = 0; rel = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            ece += m.mean() * abs(ok[m].mean() - conf[m].mean()); rel.append((conf[m].mean(), ok[m].mean(), int(m.sum())))
    oh = np.eye(P.shape[1])[y_i]
    return dict(acc=float(ok.mean()), mean_conf=float(conf.mean()), ECE=float(ece), brier=float(((P - oh) ** 2).sum(1).mean()),
                nll=float(-np.log(np.clip(P[np.arange(len(y_i)), y_i], 1e-12, 1)).mean())), rel


# T chọn trên val
f = lambda k: -np.log(np.clip(softmax(sv, k)[np.arange(len(yv_i)), yv_i], 1e-12, 1)).mean()
Tbest = float(minimize_scalar(f, bounds=(0.5, 60), method="bounded").x)
cal = CalibratedClassifierCV(LinearSVC(C=C), method="sigmoid", cv=5).fit(A, ytr)
lr = LogisticRegression(max_iter=2000, **lrp).fit(A, ytr)
P = {"softmax(3×điểm) — hệ số ban đầu": softmax(st, 3), f"softmax({Tbest:.1f}×điểm) — T chọn trên val, website dùng": softmax(st, Tbest),
     "Platt (CalibratedClassifierCV)": cal.predict_proba(T), "Logistic Regression": lr.predict_proba(T)}
rows, rels = [], {}
for n, p in P.items():
    m, r = metrics(p, yt_i); rows.append(dict(method=n, **m)); rels[n] = r
res = pd.DataFrame(rows); res.to_csv(OUT / "calibration_results.csv", index=False, encoding="utf-8-sig"); print(res.round(4).to_string())
save_json(dict(T=Tbest, C=C), "calibration_T.json")
fig, axs = plt.subplots(1, 4, figsize=(14, 3.7), sharey=True)
for ax, (n, r) in zip(axs, rels.items()):
    ax.plot([0, 1], [0, 1], "--", color="#999"); r = np.array(r); r = r[r[:, 2] >= 10]          # chỉ vẽ nhóm có từ 10 bài trở lên (nhóm quá ít bài rất nhiễu)
    ax.plot(r[:, 0], r[:, 1], "-", color="#0b1b33"); ax.scatter(r[:, 0], r[:, 1], s=12 + r[:, 2] ** 0.7 * 3, color="#0b1b33", zorder=3, clip_on=False)
    ax.set_title(n, fontsize=9); ax.set_xlabel("độ tin cậy dự đoán (kích thước chấm ∝ số bài)"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(.04, .9, f"ECE = {res.set_index('method').loc[n, 'ECE']:.3f}", fontsize=9)
axs[0].set_ylabel("tỉ lệ đúng thực tế"); plt.tight_layout(); plt.savefig(OUT / "calibration.png", dpi=150); plt.close()
# dự đoán có chọn lọc: bỏ bớt bài kém chắc chắn
p0 = softmax(st, 4.3); s = np.sort(p0, 1); gap = s[:, -1] - s[:, -2]; ok = p0.argmax(1) == yt_i      # đúng hệ số T mà website dùng
order = np.argsort(-gap); rc = []
for cov in (1.0, .9, .8, .7, .6, .5, .4, .3):
    k = int(round(cov * len(gap))); rc.append(dict(coverage=cov, n=k, accuracy=float(ok[order[:k]].mean()), min_gap=float(gap[order[k - 1]])))
rc = pd.DataFrame(rc); rc.to_csv(OUT / "risk_coverage.csv", index=False, encoding="utf-8-sig"); print(rc.round(3).to_string())
fig, ax = plt.subplots(figsize=(6.5, 3.8)); ax.plot(rc.coverage * 100, rc.accuracy * 100, "o-", color="#0b1b33")
for x, y in zip(rc.coverage * 100, rc.accuracy * 100): ax.text(x, y + .6, f"{y:.1f}", ha="center", fontsize=8)
ax.set_xlabel("Tỉ lệ bài AI tự quyết (%) — phần còn lại chuyển cho biên tập viên"); ax.set_ylabel("Accuracy trên các bài AI tự quyết (%)"); ax.invert_xaxis(); ax.grid(alpha=.3)
ax.set_title("Chỉ tự động khi AI chắc chắn thì đúng bao nhiêu?"); plt.tight_layout(); plt.savefig(OUT / "risk_coverage.png", dpi=150); plt.close()
