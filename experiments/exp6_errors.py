"""Thí nghiệm 6 — Phân tích lỗi định lượng: 88 bài sai ở đâu, độ dài bài, độ tự tin, và xuất danh sách để đọc/gắn thẻ."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.svm import LinearSVC

plt.rcParams["font.family"] = "DejaVu Sans"
df, i_tr, i_va, i_te = load(); check_split(df, i_tr, i_va, i_te)
C = load_json("tuning_results_best_svm.json")["C"]
vec = tfidf().fit(df.text.iloc[i_tr]); A, T = vec.transform(df.text.iloc[i_tr]), vec.transform(df.text.iloc[i_te])
svm = LinearSVC(C=C).fit(A, df.label.iloc[i_tr]); cls = list(svm.classes_); W = svm.coef_; names = np.array(vec.get_feature_names_out())
D = df.iloc[i_te].reset_index(drop=True); s = svm.decision_function(T)
z = s * 4.3; z -= z.max(1, keepdims=True); p = np.exp(z); p /= p.sum(1, keepdims=True)      # T = 4,3 như website
pred = np.array(cls)[s.argmax(1)]; D["pred"] = pred; D["ok"] = D.pred == D.label
D["pct"] = (p.max(1) * 100).round(1); srt = np.sort(p, 1); D["gap"] = (srt[:, -1] - srt[:, -2]).round(3)
D["words"] = D.text.str.split().str.len(); D["rank_truth"] = [int((s[i] > s[i, cls.index(l)]).sum()) + 1 for i, l in enumerate(D.label)]
print("Đúng:", int(D.ok.sum()), "Sai:", int((~D.ok).sum()))
# phân tích theo độ dài
D["len_q"] = pd.qcut(D.words, 4, labels=["Q1 ngắn nhất", "Q2", "Q3", "Q4 dài nhất"])
bylen = D.groupby("len_q", observed=True).agg(n=("ok", "size"), words_median=("words", "median"), acc=("ok", "mean")).reset_index()
bylen.to_csv(OUT / "error_by_length.csv", index=False, encoding="utf-8-sig"); print(bylen.round(3).to_string())
conf = dict(pct_correct=float(D.pct[D.ok].mean()), pct_wrong=float(D.pct[~D.ok].mean()), gap_correct=float(D.gap[D.ok].mean()), gap_wrong=float(D.gap[~D.ok].mean()),
            truth_rank2=int(((~D.ok) & (D.rank_truth == 2)).sum()), truth_rank3plus=int(((~D.ok) & (D.rank_truth >= 3)).sum()), n_wrong=int((~D.ok).sum()))
for th in (80, 90):
    conf[f"n_wrong_pct_ge_{th}"] = int(((~D.ok) & (D.pct >= th)).sum())            # bài sai nhưng AI nghiêng ≥ th%
    conf[f"n_all_pct_ge_{th}"] = int((D.pct >= th).sum())                            # tất cả bài có AI nghiêng ≥ th%
save_json(conf, "error_confidence.json"); print(conf)
# xuất 88 lỗi
rows = []
for i in np.where(~D.ok.values)[0]:
    x = T[i].toarray().ravel(); kp = cls.index(D.pred[i]); kt = cls.index(D.label[i])
    top = lambda k: [names[j] for j in np.argsort(-(x * W[k]))[:6] if x[j] * W[k][j] > 0]
    rows.append(dict(id=int(D.id[i]), truth=D.label[i], pred=D.pred[i], pct=D.pct[i], gap=D.gap[i], rank_truth=int(D.rank_truth[i]), words=int(D.words[i]),
                     title=D.title[i].strip(), desc=D.description[i].strip()[:300], pred_keywords=", ".join(top(kp)), truth_keywords=", ".join(top(kt)), body_start=D.content[i].strip()[:500]))
E = pd.DataFrame(rows).sort_values(["truth", "pred"]).reset_index(drop=True); E.to_csv(OUT / "errors_88.csv", index=False, encoding="utf-8-sig")
E[E.pct >= 90].sort_values("pct", ascending=False)[["id", "truth", "pred", "pct", "title"]].to_csv(OUT / "errors_confident.csv", index=False, encoding="utf-8-sig")   # để cả nhóm đọc: AI rất chắc chắn mà vẫn sai
E.to_json(OUT / "errors_88.json", orient="records", force_ascii=False, indent=1)
pairs = E.groupby(["truth", "pred"]).size().sort_values(ascending=False).reset_index(name="n"); pairs.to_csv(OUT / "error_pairs.csv", index=False, encoding="utf-8-sig"); print(pairs.head(10).to_string())
fig, ax = plt.subplots(figsize=(6, 3.6)); ax.bar(bylen.len_q.astype(str), bylen.acc * 100, color="#0b1b33")
for x, v, m in zip(range(4), bylen.acc * 100, bylen.words_median): ax.text(x, v + .4, f"{v:.1f}%", ha="center", fontsize=9)
ax.set_ylim(70, 100); ax.set_ylabel("Accuracy (%)"); ax.set_title("Bài càng ngắn càng khó?"); plt.tight_layout(); plt.savefig(OUT / "error_by_length.png", dpi=150); plt.close()
