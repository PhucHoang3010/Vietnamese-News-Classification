"""Thí nghiệm 8 — Đánh giá chức năng 'Hỏi AI về tin tức' (truy hồi + trích câu, không tự sinh nội dung).
Phép thử 'tìm đúng bài' (known-item search): truy vấn = TIÊU ĐỀ của một bài; chỉ mục KHÔNG chứa tiêu đề (tránh rò rỉ) → bài đúng có lên top không?
 (a) so sánh chỉ mục: chỉ sapo / chỉ nội dung / kết hợp (chọn trọng số)      (b) định tuyến theo chuyên mục có giúp không?
 (c) điểm của bài cao nhất có phản ánh độ đúng không (để đặt nhãn 'độ chắc chắn')  (d) ngưỡng 'không trả lời': truy vấn thật vs truy vấn ngẫu nhiên
Chạy:  python experiments/exp8_qa.py
"""
import sys, time
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import roc_auc_score

plt.rcParams["font.family"] = "DejaVu Sans"
model = joblib.load(ROOT / "model.joblib"); VEC = model.named_steps["tfidf"]; CLASSES = list(model.classes_)
df, i_tr, i_va, i_te = load()
D = df.reset_index(drop=True)
desc = [(r.description.strip() or r.content[:200]) for r in D.itertuples()]            # giống app.py
STOPQ = set("là gì nào sao thế bao nhiêu ai đâu khi không có được của và các những này đó thì mà ở tại cho với trong về như hay hoặc bị đã sẽ đang rất cũng còn hôm nay vậy ra làm".split())
def qclean(q): return " ".join(w for w in clean(q).split() if w not in STOPQ) or clean(q)
t0 = time.time()
SV = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1, max_df=0.5).fit([clean(t + " " + t + " " + d) for t, d in zip(D.title, desc)])
AXc = VEC.transform([clean(d + " " + c) for d, c in zip(desc, D.content)])             # nội dung, KHÔNG có tiêu đề
SXc = SV.transform([clean(d) for d in desc])                                          # sapo, KHÔNG có tiêu đề
print("chỉ mục xong", round(time.time() - t0), "s", flush=True)
Q = [qclean(t) for t in D.title]; QV = VEC.transform(Q); QS = SV.transform(Q)
Sc = (QV @ AXc.T).toarray(); Ss = (QS @ SXc.T).toarray(); n = len(D)
def rank(S): return (S > S.diagonal()[:, None]).sum(1) + 1
rows = []
def rec(S, name, group):
    rk = rank(S); rows.append(dict(nhom=group, bien_the=name, recall_at_1=(rk <= 1).mean(), recall_at_5=(rk <= 5).mean(), recall_at_10=(rk <= 10).mean(), mrr=(1 / rk).mean())); return rk
rec(Ss, "Chỉ sapo (TF-IDF tìm kiếm)", "Chỉ mục"); rec(Sc, "Chỉ nội dung (TF-IDF của bộ phân loại)", "Chỉ mục")
for w in (0.3, 0.5, 0.6, 0.7, 0.8): rec(w * Sc + (1 - w) * Ss, f"Kết hợp: nội dung {w:.1f} + sapo {1 - w:.1f}", "Trọng số")
W = 0.7; S0 = W * Sc + (1 - W) * Ss
sc = model.decision_function(Q) * 3; sc -= sc.max(1, keepdims=True); PQ = np.exp(sc); PQ /= PQ.sum(1, keepdims=True)
PQa = PQ[:, [CLASSES.index(l) for l in D.label]]
for lam in (0.2, 0.5, 1.0): rec(S0 * (1 + lam * PQa), f"+ định tuyến chuyên mục (λ={lam})", "Định tuyến")
res = pd.DataFrame(rows); res.to_csv(OUT / "qa_retrieval.csv", index=False, encoding="utf-8-sig"); print(res.round(4).to_string(), flush=True)
# (c) độ chắc chắn
top = S0.argmax(1); ok = top == np.arange(n); mx = S0.max(1)
bins = [(0, .08), (.08, .15), (.15, .20), (.20, .25), (.25, .30), (.30, .50), (.50, 9)]
cb = []
for lo, hi in bins:
    m = (mx >= lo) & (mx < hi)
    if m.any(): cb.append(dict(khoang=f"[{lo:.2f}, {min(hi,1):.2f})", n=int(m.sum()), ty_le_dung_bai=float(ok[m].mean())))
cb = pd.DataFrame(cb); cb.to_csv(OUT / "qa_confidence.csv", index=False, encoding="utf-8-sig"); print(cb.round(3).to_string(), flush=True)
# (d) ngưỡng không trả lời: truy vấn thật (tiêu đề) vs truy vấn ngẫu nhiên (5 từ bất kỳ trong từ điển)
rng = np.random.default_rng(SEED); vocab = np.array([w for w in VEC.get_feature_names_out() if " " not in w and len(w) > 2])
RQ = [" ".join(rng.choice(vocab, 5, replace=False)) for _ in range(n)]
Sr = W * (VEC.transform(RQ) @ AXc.T).toarray() + (1 - W) * (SV.transform(RQ) @ SXc.T).toarray(); mr = Sr.max(1)
auc = float(roc_auc_score(np.r_[np.ones(n), np.zeros(n)], np.r_[mx, mr]))
ab = {"auc_thuc_vs_ngau_nhien": auc, "thresholds": []}
for th in (0.05, 0.08, 0.10, 0.12, 0.15):
    ab["thresholds"].append(dict(nguong=th, tu_choi_nham_truy_van_that=float((mx < th).mean()), tra_loi_nham_truy_van_ngau_nhien=float((mr >= th).mean())))
save_json(ab, "qa_abstain.json"); print(json.dumps(ab, ensure_ascii=False, indent=1), flush=True)
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
axs[0].bar(range(len(cb)), cb.ty_le_dung_bai * 100, color="#0b1b33"); axs[0].set_xticks(range(len(cb))); axs[0].set_xticklabels(cb.khoang, rotation=30, fontsize=8)
for x, (v, k) in enumerate(zip(cb.ty_le_dung_bai * 100, cb.n)): axs[0].text(x, v + 1, f"{v:.0f}%\\n(n={k})", ha="center", fontsize=7)
axs[0].set_ylim(0, 112); axs[0].set_ylabel("% truy vấn tìm đúng bài"); axs[0].set_xlabel("điểm của bài cao nhất"); axs[0].set_title("Điểm cao hơn → đúng bài hơn")
axs[1].hist(mx, bins=40, alpha=.8, color="#0b1b33", label="truy vấn thật (tiêu đề)"); axs[1].hist(mr, bins=40, alpha=.6, color="#8fa6c6", label="truy vấn ngẫu nhiên")
axs[1].axvline(0.08, color="r", ls="--"); axs[1].legend(); axs[1].set_xlabel("điểm của bài cao nhất"); axs[1].set_title(f"Phân biệt có/không có căn cứ (AUC = {auc:.3f})")
plt.tight_layout(); plt.savefig(OUT / "qa_confidence.png", dpi=150); plt.close()
print("xong", round(time.time() - t0), "s")
