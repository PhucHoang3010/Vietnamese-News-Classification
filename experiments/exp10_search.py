"""Thí nghiệm 10 — Tìm kiếm nâng cao và tìm theo nghĩa.

 (A) Bộ tìm Boolean có ĐÚNG không? So 100 truy vấn ngẫu nhiên (AND/OR/NOT, cụm từ, tiền tố từ*, trường) với một cách duyệt tuần tự độc lập;
     đo thời gian trả lời trên 600 truy vấn.
 (B) Tìm theo nghĩa (LSA = TF-IDF + TruncatedSVD) có hơn TF-IDF thường không? Ba phép thử trên 5.500 bài:
       1. tiêu đề -> bài   (chỉ mục không chứa tiêu đề)       2. sapo -> bài   (chỉ mục không chứa sapo)
       3. độ thuần chủ đề: lấy tiêu đề làm truy vấn, 10 bài gần nhất có cùng chuyên mục thật với bài đó không?
     Tham số (số chiều LSA, trọng số trộn) chọn trên một nửa số bài (dev), báo cáo trên nửa còn lại (eval).
Chạy:  python experiments/exp10_search.py
"""
import sys, time, random, re
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
sys.path.insert(0, str(ROOT))
import search_tools as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

t0 = time.time()
raw = pd.read_csv(ROOT / "data/news_dataset.csv", encoding="utf-8", usecols=["id", "title", "description", "content", "ground_truth"]).fillna("")
raw = raw.reset_index(drop=True)
docs = [{"title": r.title, "desc": r.description, "content": r.content, "label": r.ground_truth} for r in raw.itertuples()]
n = len(docs); print("Số bài:", n, flush=True)

# ============================================================== (A) Boolean
idx = st.BoolIndex(docs)
print(f"Dựng chỉ mục Boolean: {time.time() - t0:.1f}s", flush=True)
rng = random.Random(SEED)
vocab = {f: [w for w in idx.terms[f] if len(w) > 2 and idx.mat[f][:, idx.vocab[f][w]].nnz >= 5] for f in idx.FIELDS}
FNAME = {"title": "tieude", "desc": "sapo", "content": "noidung"}


def rand_term():
    f = rng.choice([None, None, "title", "desc", "content"])
    pool = vocab[f or "content"]; kind = rng.random()
    if kind < 0.15:
        w = rng.choice(pool); return (f"{FNAME[f]}:" if f else "") + w[: max(3, len(w) - 2)] + "*"
    if kind < 0.35:                                                     # cụm từ hai từ có thật trong một bài
        d = docs[rng.randrange(n)]; ws = st.fold(d[f or "content"]).split()
        if len(ws) > 3:
            i = rng.randrange(len(ws) - 1); return (f"{FNAME[f]}:" if f else "") + f'"{ws[i]} {ws[i + 1]}"'
    return (f"{FNAME[f]}:" if f else "") + rng.choice(pool)


def rand_query():
    k = rng.choice([2, 3, 4]); terms = [rand_term() for _ in range(k)]; q = terms[0]
    for t in terms[1:]:
        q += " " + rng.choice(["AND", "OR", "NOT", ""]) + " " + t
    return re.sub(r"\s+", " ", q).strip()


FOLD = {f: [st.fold(d[f]) for d in docs] for f in idx.FIELDS}                 # chuẩn hóa một lần
TOKSET = {f: [set(t.split()) for t in FOLD[f]] for f in idx.FIELDS}
LABF = [st.fold(d["label"]) for d in docs]


def naive(tree):
    """Cách duyệt tuần tự độc lập với ma trận: mỗi bài một tập từ / một chuỗi, kiểm tra từng bài."""
    k = tree[0]
    if k == "term":
        _, f, text, ph = tree; q = st.fold(text, star=True); ws = q.split(); res = np.zeros(n, bool)
        for i in range(n):
            if f == "label":
                lb = LABF[i]; res[i] = (q == lb) or (len(q) > 2 and q in lb); continue
            for fl in ((f,) if f else idx.FIELDS):
                toks = TOKSET[fl][i]; ok = True
                for w in ws:
                    ok &= any(t.startswith(w[:-1]) for t in toks) if (w.endswith("*") and len(w) > 2) else (w.strip("*") in toks)
                    if not ok: break
                if ok and ph and len(ws) > 1 and "*" not in q: ok = (" " + q + " ") in (" " + FOLD[fl][i] + " ")
                if ok: res[i] = True; break
        return res
    if k == "not": return ~naive(tree[1])
    ms = [naive(x) for x in tree[1]]; return np.logical_and.reduce(ms) if k == "and" else np.logical_or.reduce(ms)


N_Q, ok_n, times, sizes = 600, 0, [], []
bad = []
for _ in range(N_Q):
    q = rand_query()
    t1 = time.perf_counter(); m, tree = idx.search(q); times.append((time.perf_counter() - t1) * 1000); sizes.append(int(m.sum()))
    if _ < 100:                                                         # duyệt tuần tự chậm: chỉ đối chiếu 100 truy vấn đầu
        same = bool((naive(tree) == m).all()); ok_n += same
        if not same: bad.append(q)
print(f"Đối chiếu duyệt tuần tự: {ok_n}/100 truy vấn khớp 100% | thời gian Boolean trung bình {np.mean(times):.1f} ms, p95 {np.percentile(times, 95):.1f} ms | số bài khớp trung vị {int(np.median(sizes))}", flush=True)
if bad: print("KHÔNG khớp:", bad[:5])
save_json({"n_queries_checked": 100, "n_match": ok_n, "n_queries_timed": N_Q, "ms_mean": float(np.mean(times)), "ms_p95": float(np.percentile(times, 95)), "median_hits": int(np.median(sizes)),
           "examples": ['giá vàng AND (tăng OR giảm) NOT bitcoin', 'tieude:"thuế" noidung:ngân hàng', 'chuyenmuc:"Thể thao" bóng*']}, "search_bool_tests.json")

# ============================================================== (B) tìm theo nghĩa
def cl(s): return clean(s)


TITLE = [cl(d["title"]) for d in docs]; DESC = [cl(d["desc"] or d["content"][:200]) for d in docs]; CONT = [cl(d["content"]) for d in docs]
LAB = np.array([d["label"] for d in docs])
rs = np.random.default_rng(SEED); perm = rs.permutation(n); dev, ev = np.sort(perm[: n // 2]), np.sort(perm[n // 2:])


def eval_rank(S, tgt, qs):
    """S: (n_q, n_docs) điểm; tgt[i] = chỉ số bài đúng của truy vấn i."""
    ranks = (S > S[np.arange(len(S)), tgt][:, None]).sum(1) + 1
    return {"R@1": float((ranks <= 1).mean()), "R@5": float((ranks <= 5).mean()), "R@10": float((ranks <= 10).mean()), "MRR": float((1 / ranks).mean())}


def cos_tfidf_and_lsa(index_text, query_text, comps):
    tf = TfidfVectorizer(sublinear_tf=True, min_df=2, max_df=0.5, max_features=30000); X = tf.fit_transform(index_text); Q = tf.transform(query_text)
    out = {"tfidf": (Q @ X.T).toarray()}
    for k in comps:
        svd = TruncatedSVD(n_components=k, random_state=SEED, n_iter=5); Z = normalize(svd.fit_transform(X)); Zq = normalize(svd.transform(Q))
        out[k] = Zq @ Z.T
    return out


COMPS = (100, 200, 300); ALPHAS = (0.3, 0.5, 0.7)
results = []
task_scores = {}
for task, qtext, itext in (("tiêu đề → bài", TITLE, [f"{d} {c}" for d, c in zip(DESC, CONT)]), ("sapo → bài", DESC, [f"{t} {c}" for t, c in zip(TITLE, CONT)])):
    sc = cos_tfidf_and_lsa(itext, qtext, COMPS); task_scores[task] = sc
    print(f"{task}: đã tính điểm ({time.time() - t0:.0f}s)", flush=True)
# độ thuần chủ đề: bài → 10 bài gần nhất (cả chuỗi tiêu đề + sapo + nội dung làm chỉ mục, bỏ chính nó)
FULL = [f"{t} {d} {c}" for t, d, c in zip(TITLE, DESC, CONT)]
sc_topic = cos_tfidf_and_lsa(FULL, TITLE, COMPS)


def methods(sc):
    m = {"TF-IDF": sc["tfidf"]}
    for k in COMPS:
        m[f"LSA k={k}"] = sc[k]
        for a in ALPHAS: m[f"Trộn k={k}, {int(a * 100)}% TF-IDF"] = a * sc["tfidf"] + (1 - a) * sc[k]
    return m


def topical_p10(S):
    S = S.copy(); np.fill_diagonal(S, -1); top = np.argsort(-S, 1)[:, :10]
    return float((LAB[top] == LAB[:, None]).mean())


rows = []
for name in methods(sc_topic):
    r = {"method": name}
    for task in task_scores:
        S = methods(task_scores[task])[name]
        for part, sel in (("dev", dev), ("eval", ev)):
            e = eval_rank(S[sel], sel, None)
            r.update({f"{task} | {part} | {k}": v for k, v in e.items()})
    St = methods(sc_topic)[name]
    r["độ thuần chủ đề P@10 | dev"] = float((lambda T: (LAB[np.argsort(-T, 1)[:, :10]] == LAB[dev][:, None]).mean())(np.where(np.eye(n, dtype=bool)[dev], -1, St[dev])))
    r["độ thuần chủ đề P@10 | eval"] = float((lambda T: (LAB[np.argsort(-T, 1)[:, :10]] == LAB[ev][:, None]).mean())(np.where(np.eye(n, dtype=bool)[ev], -1, St[ev])))
    rows.append(r)
res = pd.DataFrame(rows)
res["dev_MRR_avg"] = (res["tiêu đề → bài | dev | MRR"] + res["sapo → bài | dev | MRR"]) / 2
res.to_csv(OUT / "search_semantic.csv", index=False, encoding="utf-8-sig")
best = res.sort_values("dev_MRR_avg", ascending=False).iloc[0]
base = res[res.method == "TF-IDF"].iloc[0]
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
show = ["method", "tiêu đề → bài | eval | R@1", "tiêu đề → bài | eval | R@5", "tiêu đề → bài | eval | MRR", "sapo → bài | eval | R@1", "sapo → bài | eval | R@5", "sapo → bài | eval | MRR", "độ thuần chủ đề P@10 | eval", "dev_MRR_avg"]
print(res[show].round(4).to_string(), flush=True)
print("\nChọn trên dev:", best.method, "| dev MRR trung bình", round(best.dev_MRR_avg, 4), "so với TF-IDF", round(base.dev_MRR_avg, 4), flush=True)
save_json({"best_on_dev": best.method, "eval": {c: float(best[c]) for c in show[1:-1]}, "tfidf_eval": {c: float(base[c]) for c in show[1:-1]}}, "search_semantic_best.json")
print("xong", round(time.time() - t0), "s")
