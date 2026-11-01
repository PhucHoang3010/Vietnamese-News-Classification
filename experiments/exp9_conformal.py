"""Thí nghiệm 9 — Dự đoán có bảo đảm (conformal prediction): AI nêu TẬP chuyên mục thay vì ép chọn 1.

Mô hình: model.joblib (chỉ học từ 3.850 bài huấn luyện). Điểm "AI chưa từng thấy bài đó" có 3 nguồn:
  - tập kiểm định (825 bài) và tập kiểm thử (825 bài): chấm bằng chính model.joblib
  - tập huấn luyện (3.850 bài): chấm bằng dự đoán chéo 5-fold (mỗi bài được chấm bởi mô hình không học bài đó)
Quy trình:
  (a) So sánh phương pháp (hiệu chỉnh trên kiểm định + dự đoán chéo = 4.675 bài, đo trên 825 bài kiểm thử): top-k cố định, LAC, APS ngẫu nhiên,
      khoảng cách điểm SVM chung và theo từng chuyên mục (Mondrian)
  (b) Mức bảo đảm 90% / 95% / 99%: độ phủ thực tế, kích thước tập, tập 1 chuyên mục đúng bao nhiêu, bao nhiêu bài đoán sai được "cứu"
  (c) Kiểm tra giả định trộn hai nguồn điểm: hiệu chỉnh CHỈ bằng dự đoán chéo rồi đo trên 1.650 bài kiểm định + kiểm thử
  (d) Lặp 300 lần chia ngẫu nhiên 50/50 trên toàn bộ 5.500 điểm chưa từng thấy: độ phủ (cả theo từng chuyên mục) dao động quanh mục tiêu thế nào
Chạy:  python experiments/exp9_conformal.py
"""
import sys, time
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
sys.path.insert(0, str(ROOT))
import conformal as cf
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

plt.rcParams["font.family"] = "DejaVu Sans"
t0 = time.time()
df, i_tr, i_va, i_te = load(); check_split(df, i_tr, i_va, i_te)
model = joblib.load(ROOT / "model.joblib"); CL = list(model.classes_); K = len(CL); CLA = np.array(CL)
TEMP = 4.3
svmC = load_json("tuning_results_best_svm.json")["C"]


def idx_of(idx):
    y = np.searchsorted(CLA, df.label.iloc[idx].values); assert (CLA[y] == df.label.iloc[idx].values).all(); return y


Dv = model.decision_function(df.text.iloc[i_va]); yv = idx_of(i_va)
Dt = model.decision_function(df.text.iloc[i_te]); yt = idx_of(i_te)
yo = idx_of(i_tr)
cache = CACHE / "oof_train_scores.npy"
if cache.exists():
    Do = np.load(cache)
else:
    Do = cf.cross_fit_scores(df.text.iloc[i_tr].values, df.label.iloc[i_tr].values, lambda: Pipeline([("tfidf", tfidf()), ("clf", LinearSVC(C=svmC))]))
    np.save(cache, Do)
print("Accuracy top-1: kiểm thử", round(float((Dt.argmax(1) == yt).mean()), 4), "| kiểm định", round(float((Dv.argmax(1) == yv).mean()), 4),
      "| huấn luyện (dự đoán chéo)", round(float((Do.argmax(1) == yo).mean()), 4), f"| {time.time() - t0:.0f}s", flush=True)
Dcal, ycal = np.vstack([Dv, Do]), np.concatenate([yv, yo])                  # 4.675 bài AI chưa từng thấy


def softmax(D):
    z = (D - D.max(1, keepdims=True)) * TEMP; e = np.exp(z); return e / e.sum(1, keepdims=True)


def with_top1(mask, D):
    mask[np.arange(len(mask)), D.argmax(1)] = True        # không để tập rỗng (chỉ làm độ phủ tăng thêm)
    return mask


def m_topk(k):
    def f(Dc, yc, Dx, alpha):
        mask = np.zeros(Dx.shape, bool); np.put_along_axis(mask, np.argsort(-Dx, 1)[:, :k], True, 1); return mask
    return f


def m_lac(mondrian):
    def f(Dc, yc, Dx, alpha):
        s = 1 - softmax(Dc)[np.arange(len(Dc)), yc]; Px = softmax(Dx)
        q = np.array([cf.conformal_quantile(s[yc == k], alpha) for k in range(K)])[None, :] if mondrian else cf.conformal_quantile(s, alpha)
        return with_top1((1 - Px) <= q, Dx)
    return f


def m_aps(Dc, yc, Dx, alpha, seed=0):
    """APS ngẫu nhiên hóa (Romano và cs., 2020)."""
    rng = np.random.default_rng(seed)
    Pc = softmax(Dc); o = np.argsort(-Pc, 1); Ps = np.take_along_axis(Pc, o, 1); before = np.cumsum(Ps, 1) - Ps
    rank = np.argsort(o, 1)[np.arange(len(Pc)), yc]; n = np.arange(len(Pc))
    q = cf.conformal_quantile(before[n, rank] + rng.random(len(Pc)) * Ps[n, rank], alpha)
    Px = softmax(Dx); ox = np.argsort(-Px, 1); Pxs = np.take_along_axis(Px, ox, 1); bx = np.cumsum(Pxs, 1) - Pxs
    mask = np.zeros(Dx.shape, bool); np.put_along_axis(mask, ox, (bx + rng.random(len(Px))[:, None] * Pxs) <= q, 1)
    return with_top1(mask, Dx)


def m_margin(mondrian):
    def f(Dc, yc, Dx, alpha):
        return cf.predict_sets(Dx, cf.calibrate(Dc, yc, [alpha])[str(alpha)], mondrian=mondrian)
    return f


METHODS = {"Top-1 (không có tập)": m_topk(1), "Top-2 cố định": m_topk(2), "Top-3 cố định": m_topk(3),
           "LAC xác suất (chung)": m_lac(False), "LAC xác suất (theo chuyên mục)": m_lac(True), "APS ngẫu nhiên (chung)": m_aps,
           "Khoảng cách điểm SVM (chung)": m_margin(False), "Khoảng cách điểm SVM (theo chuyên mục)": m_margin(True)}
PROD = "Khoảng cách điểm SVM (theo chuyên mục)"
pd.set_option("display.width", 230)

# ---------------------------------------------------------------- (a)(b) bảng chính: hiệu chỉnh 4.675 bài, đo trên kiểm thử
rows = []
for name, f in METHODS.items():
    for a in cf.ALPHAS:
        rows.append(dict(method=name, alpha=a, target=1 - a, **cf.evaluate(f(Dcal, ycal, Dt, a), yt)))
res = pd.DataFrame(rows); res.to_csv(OUT / "conformal_results.csv", index=False, encoding="utf-8-sig")
print(res.round(3).to_string(), flush=True)
# so với hiệu chỉnh chỉ bằng 825 bài kiểm định
rv = [dict(alpha=a, **cf.evaluate(METHODS[PROD](Dv, yv, Dt, a), yt)) for a in cf.ALPHAS]
pd.DataFrame(rv).to_csv(OUT / "conformal_val_only.csv", index=False, encoding="utf-8-sig"); print("\nHiệu chỉnh CHỈ trên 825 bài kiểm định:\n", pd.DataFrame(rv).round(3).to_string(), flush=True)

# ---------------------------------------------------------------- đường độ phủ – kích thước
grid = np.round(np.concatenate([np.arange(0.01, 0.2, 0.01), np.arange(0.2, 0.41, 0.05)]), 2); curve = []
for name, f in METHODS.items():
    if name.startswith("Top"): continue
    for a in grid:
        r = cf.evaluate(f(Dcal, ycal, Dt, float(a)), yt); curve.append(dict(method=name, alpha=float(a), coverage=r["coverage"], avg_size=r["avg_size"]))
curve = pd.DataFrame(curve); curve.to_csv(OUT / "conformal_curve.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- theo từng chuyên mục (alpha = 0,05)
mk_m = m_margin(False)(Dcal, ycal, Dt, 0.05); mk_c = m_margin(True)(Dcal, ycal, Dt, 0.05)
pc = pd.DataFrame({"class": CL, "n_test": [int((yt == k).sum()) for k in range(K)],
                   "coverage_marginal": [float(mk_m[yt == k][np.arange((yt == k).sum()), k].mean()) for k in range(K)],
                   "coverage_per_class": [float(mk_c[yt == k][np.arange((yt == k).sum()), k].mean()) for k in range(K)],
                   "avg_size_marginal": [float(mk_m[yt == k].sum(1).mean()) for k in range(K)], "avg_size_per_class": [float(mk_c[yt == k].sum(1).mean()) for k in range(K)],
                   "top1_acc": [float((Dt.argmax(1)[yt == k] == k).mean()) for k in range(K)]})
pc.to_csv(OUT / "conformal_per_class.csv", index=False, encoding="utf-8-sig"); print("\n", pc.round(3).to_string(), flush=True)

# ---------------------------------------------------------------- phân bố kích thước tập + cứu bài đoán sai (phương pháp sản phẩm)
prod = {}
ok1 = Dt.argmax(1) == yt
for a in cf.ALPHAS:
    m = METHODS[PROD](Dcal, ycal, Dt, a); size = m.sum(1); hit = m[np.arange(len(m)), yt]
    prod[str(a)] = dict(size_hist={str(s): int((size == s).sum()) for s in range(1, K + 1) if (size == s).any()},
                        top1_acc_by_size={str(s): float(ok1[size == s].mean()) for s in range(1, K + 1) if (size == s).any()},
                        covered_by_size={str(s): float(hit[size == s].mean()) for s in range(1, K + 1) if (size == s).any()},
                        n_top1_wrong=int((~ok1).sum()), wrong_rescued=int((hit & ~ok1).sum()), multi_share=float((size >= 2).mean()),
                        multi_acc_top1=float(ok1[size >= 2].mean()) if (size >= 2).any() else None, multi_covered=float(hit[size >= 2].mean()) if (size >= 2).any() else None,
                        **{k: v for k, v in cf.evaluate(m, yt).items()})
save_json(prod, "conformal_prod.json")
print("\n", json.dumps(prod["0.05"], ensure_ascii=False, indent=1), flush=True)

# ---------------------------------------------------------------- (c) giả định trộn hai nguồn điểm: hiệu chỉnh chỉ bằng dự đoán chéo, đo trên 1.650 bài
Dvt, yvt = np.vstack([Dv, Dt]), np.concatenate([yv, yt]); chk = []
for a in cf.ALPHAS:
    for name in ("Khoảng cách điểm SVM (chung)", PROD):
        chk.append(dict(method=name, alpha=a, **cf.evaluate(METHODS[name](Do, yo, Dvt, a), yvt)))
chk = pd.DataFrame(chk); chk.to_csv(OUT / "conformal_oof_to_unseen.csv", index=False, encoding="utf-8-sig"); print("\nHiệu chỉnh bằng dự đoán chéo → đo trên kiểm định + kiểm thử:\n", chk.round(3).to_string(), flush=True)

# ---------------------------------------------------------------- (d) lặp 300 lần chia ngẫu nhiên 50/50 trên toàn bộ 5.500 điểm "chưa từng thấy"
Dall, yall = np.vstack([Dcal, Dt]), np.concatenate([ycal, yt]); rep = []
for a in cf.ALPHAS:
    for name in ("Khoảng cách điểm SVM (chung)", PROD, "LAC xác suất (chung)", "APS ngẫu nhiên (chung)"):
        f = METHODS[name]
        for tr, te in StratifiedShuffleSplit(n_splits=300, test_size=0.5, random_state=SEED).split(Dall, yall):
            r = cf.evaluate(f(Dall[tr], yall[tr], Dall[te], a), yall[te])
            rep.append(dict(method=name, alpha=a, **r))
rep = pd.DataFrame(rep)
agg = rep.groupby(["alpha", "method"]).agg(cov_mean=("coverage", "mean"), cov_std=("coverage", "std"), cov_min=("coverage", "min"), cov_p05=("coverage", lambda x: np.percentile(x, 5)),
                                           size_mean=("avg_size", "mean"), size_std=("avg_size", "std"), singleton_share=("singleton_share", "mean"), singleton_acc=("singleton_acc", "mean"),
                                           worst_class_mean=("worst_class_coverage", "mean"), worst_class_min=("worst_class_coverage", "min")).reset_index()
agg.to_csv(OUT / "conformal_repeat.csv", index=False, encoding="utf-8-sig"); print("\nLặp 300 lần chia 50/50 trên 5.500 điểm (mỗi nửa 2.750 bài):\n", agg.round(4).to_string(), flush=True)

# ---------------------------------------------------------------- biểu đồ
NAVY, MID, LIGHT, RED, GOLD = "#0b1b33", "#5a6b85", "#8fa6c6", "#c0392b", "#b08d57"
sty = {PROD: (NAVY, "-", "o"), "Khoảng cách điểm SVM (chung)": (MID, "--", "s"), "LAC xác suất (chung)": (LIGHT, "-.", "^"), "APS ngẫu nhiên (chung)": (GOLD, ":", "v")}
fig, ax = plt.subplots(2, 2, figsize=(12.5, 8.4))
a0 = ax[0, 0]; a0.plot([0.8, 1], [0.8, 1], "--", color="#999", label="Mục tiêu (1 − α)")
for name, (c, ls, mk) in sty.items():
    d = curve[curve.method == name]; d = d[d.alpha <= 0.2]; a0.plot(1 - d.alpha, d.coverage, color=c, ls=ls, marker=mk, ms=3.5, lw=1.8, label=name)
a0.axhline(float((Dt.argmax(1) == yt).mean()), color=RED, lw=1, ls=":"); a0.text(0.805, float((Dt.argmax(1) == yt).mean()) - 0.012, "AI chọn 1 chuyên mục: đúng 89,3%", color=RED, fontsize=8)
a0.set_xlabel("Độ phủ mục tiêu 1 − α"); a0.set_ylabel("Độ phủ thực tế trên tập kiểm thử"); a0.set_title("Độ phủ có đạt mục tiêu không?", fontsize=11, fontweight="bold"); a0.legend(fontsize=7.5, loc="lower right"); a0.grid(alpha=.25)
a1 = ax[0, 1]
for name, (c, ls, mk) in sty.items():
    d = curve[curve.method == name]; a1.plot(d.coverage, d.avg_size, color=c, ls=ls, marker=mk, ms=3.5, lw=1.8, label=name)
for k, (nm, mk) in enumerate((("Top-1", "*"), ("Top-2", "D"), ("Top-3", "P")), start=1):
    r = cf.evaluate(m_topk(k)(Dcal, ycal, Dt, 0.1), yt); a1.scatter([r["coverage"]], [r["avg_size"]], color=RED, marker=mk, s=45, zorder=5); a1.annotate(nm + " cố định", (r["coverage"], r["avg_size"]), textcoords="offset points", xytext=(-8, 6), fontsize=8, color=RED, ha="right")
a1.set_xlim(0.88, 1.003); a1.set_ylim(0.95, 4.2); a1.set_xlabel("Độ phủ thực tế"); a1.set_ylabel("Kích thước tập trung bình (số chuyên mục)"); a1.set_title("Cùng độ phủ, tập nhỏ hơn top-k cố định", fontsize=11, fontweight="bold"); a1.grid(alpha=.25)
a2 = ax[1, 0]; o = np.argsort(pc.coverage_marginal.values); y_ = np.arange(K); h = 0.38
a2.barh(y_ + h / 2, pc.coverage_marginal.values[o] * 100, height=h, color=LIGHT, label="Ngưỡng chung")
a2.barh(y_ - h / 2, pc.coverage_per_class.values[o] * 100, height=h, color=NAVY, label="Ngưỡng riêng từng chuyên mục")
a2.axvline(95, color=RED, ls="--", lw=1.2); a2.set_yticks(y_); a2.set_yticklabels(CLA[o], fontsize=9); a2.set_xlim(70, 101); a2.set_xlabel("Độ phủ trên tập kiểm thử của từng chuyên mục (%) — mục tiêu 95%")
a2.set_title("Chuyên mục khó có được bảo đảm không?", fontsize=11, fontweight="bold", pad=24); a2.legend(fontsize=8, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, frameon=False)
a3 = ax[1, 1]; ph = prod["0.05"]; sizes = sorted(int(s) for s in ph["size_hist"]); cnt = [ph["size_hist"][str(s)] for s in sizes]; acc = [ph["top1_acc_by_size"][str(s)] * 100 for s in sizes]
a3.bar([str(s) for s in sizes], cnt, color=NAVY); a3.set_xlabel("Số chuyên mục trong tập (bảo đảm 95%)"); a3.set_ylabel("Số bài kiểm thử")
for x_, c_ in zip(range(len(sizes)), cnt): a3.text(x_, c_ + 8, str(c_), ha="center", fontsize=9)
a3.text(0.97, 0.95, "Khi AI chỉ chọn 1 chuyên mục thì đúng:\n" + "\n".join(f"  tập {s} mục: {a:.0f}%" for s, a in zip(sizes[:4], acc[:4])), transform=a3.transAxes, ha="right", va="top", fontsize=8.5, color="#26354d")
a3.set_ylim(0, max(cnt) * 1.18); a3.set_title("Bài càng mơ hồ, tập càng lớn", fontsize=11, fontweight="bold")
plt.suptitle("Dự đoán có bảo đảm (conformal): hiệu chỉnh trên 4.675 bài AI chưa từng thấy, đo trên 825 bài kiểm thử", fontsize=12, y=0.995)
plt.tight_layout(); plt.savefig(OUT / "conformal.png", dpi=150); plt.close()
print("xong", round(time.time() - t0), "s")
