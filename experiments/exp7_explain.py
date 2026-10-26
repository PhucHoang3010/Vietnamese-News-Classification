"""Thí nghiệm 7 — Lời giải thích của AI Lab có THẬT SỰ phản ánh mô hình không? (độ trung thực của giải thích)

Trang AI Lab tô đậm những từ "đóng góp nhiều nhất" cho chuyên mục AI chọn. Nếu lời giải thích đúng thì:
 (a) XÓA các từ đó -> dự đoán phải dễ đổi (comprehensiveness);
 (b) CHỈ GIỮ các từ đó -> dự đoán phải giữ nguyên (sufficiency).
So sánh với 3 cách chọn từ khác: ngẫu nhiên theo loại từ, ngẫu nhiên theo vị trí (từ hay gặp dễ trúng hơn), và từ có TF-IDF lớn nhất.
Chạy trên 825 bài kiểm thử, mô hình model.joblib (chỉ học từ tập huấn luyện), cùng công thức đóng góp như app.py:
    đóng góp(từ) = (w_lớp dự đoán − w trung bình các lớp khác) × TF-IDF(từ), cụm hai từ chia đều cho hai từ.
Chạy:  python experiments/exp7_explain.py
"""
import sys, time, math
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "DejaVu Sans"
df, i_tr, i_va, i_te = load(); check_split(df, i_tr, i_va, i_te)
model = joblib.load(ROOT / "model.joblib")
VEC, CLF = model.named_steps["tfidf"], model.named_steps["clf"]
CLASSES = list(model.classes_); VOC = VEC.vocabulary_; W = CLF.coef_
test = df.iloc[i_te].reset_index(drop=True)
texts, truth = test.text.tolist(), test.label.values
dec0 = model.decision_function(texts); pred0 = np.array(CLASSES)[dec0.argmax(axis=1)]
print("Accuracy kiểm thử của model.joblib:", round(float((pred0 == truth).mean()), 4), flush=True)
K0 = np.array([CLASSES.index(p) for p in pred0])

MS = [1, 2, 3, 5, 10, 20]
RAND_DRAWS = 3
rng = np.random.default_rng(SEED)
t0 = time.time()


def analyse(text, k):
    """Trả về (tokens, đóng góp gộp theo loại từ, giá trị TF-IDF đơn từ theo loại từ)."""
    tokens = [t for t in text.split() if len(t) >= 2]
    x = VEC.transform([" ".join(tokens)]).tocsr()
    wd = W[k] - (W.sum(axis=0) - W[k]) / (len(CLASSES) - 1)
    feats = {}
    for i, t in enumerate(tokens):
        feats.setdefault(t, []).append((i,))
        if i + 1 < len(tokens):
            feats.setdefault(t + " " + tokens[i + 1], []).append((i, i + 1))
    score = np.zeros(len(tokens))
    for f, occ in feats.items():
        j = VOC.get(f)
        if j is None:
            continue
        c = float(x[0, j]) * float(wd[j]) / len(occ)
        for pos in occ:
            for i in pos:
                score[i] += c / len(pos)
    agg, tfidf_w = {}, {}
    for i, t in enumerate(tokens):
        agg[t] = agg.get(t, 0.0) + score[i]
    for t in agg:
        j = VOC.get(t)
        tfidf_w[t] = float(x[0, j]) if j is not None else 0.0
    return tokens, agg, tfidf_w


pick = {m: {"AI chọn (đóng góp lớn nhất)": [], "Ngẫu nhiên (theo loại từ)": [], "Ngẫu nhiên (theo vị trí)": [], "TF-IDF lớn nhất": []} for m in MS}
for n, (t, k) in enumerate(zip(texts, K0)):
    tokens, agg, tw = analyse(t, k)
    types = list(agg)
    by_contrib = [w for w, v in sorted(agg.items(), key=lambda kv: -kv[1])]
    by_tfidf = [w for w, v in sorted(tw.items(), key=lambda kv: -kv[1])]
    for m in MS:
        d = pick[m]
        d["AI chọn (đóng góp lớn nhất)"].append((tokens, set(by_contrib[:m])))
        d["TF-IDF lớn nhất"].append((tokens, set(by_tfidf[:m])))
        for name, draw in (("Ngẫu nhiên (theo loại từ)", lambda: rng.choice(len(types), size=min(m, len(types)), replace=False)),):
            sets = [set(types[i] for i in draw()) for _ in range(RAND_DRAWS)]
            d[name].append((tokens, sets))
        sets = []
        for _ in range(RAND_DRAWS):
            s = set()
            while len(s) < min(m, len(types)):
                s.add(tokens[int(rng.integers(len(tokens)))])
            sets.append(s)
        d["Ngẫu nhiên (theo vị trí)"].append((tokens, sets))
print("tính đóng góp xong", round(time.time() - t0), "s", flush=True)


def run(mode):
    """mode='xoa' hoặc 'giu'. Trả về bảng các phương pháp x m."""
    rows = []
    for m in MS:
        for name, items in pick[m].items():
            multi = isinstance(items[0][1], list)
            flips, margin_drop, frac_tok = [], [], []
            for r in range(RAND_DRAWS if multi else 1):
                new, ntok = [], []
                for tokens, s in items:
                    ss = s[r] if multi else s
                    kept = [w for w in tokens if (w not in ss if mode == "xoa" else w in ss)]
                    new.append(" ".join(kept)); ntok.append(1 - len(kept) / max(len(tokens), 1) if mode == "xoa" else len(kept) / max(len(tokens), 1))
                d = model.decision_function(new); p = np.array(CLASSES)[d.argmax(axis=1)]          # = model.predict, nhưng chỉ vector hóa một lần
                flips.append(float(np.mean(p != pred0)))
                margin_drop.append(float(np.mean(dec0[np.arange(len(K0)), K0] - d[np.arange(len(K0)), K0])))
                frac_tok.append(float(np.mean(ntok)))
            f = float(np.mean(flips)); nn = len(texts) * (RAND_DRAWS if multi else 1)
            lo = (f + 1.96 ** 2 / (2 * nn) - 1.96 * math.sqrt(f * (1 - f) / nn + 1.96 ** 2 / (4 * nn ** 2))) / (1 + 1.96 ** 2 / nn)
            hi = (f + 1.96 ** 2 / (2 * nn) + 1.96 * math.sqrt(f * (1 - f) / nn + 1.96 ** 2 / (4 * nn ** 2))) / (1 + 1.96 ** 2 / nn)
            rows.append(dict(che_do=mode, phuong_phap=name, m=m, ty_le_doi_du_doan=f, ci_lo=lo, ci_hi=hi, giam_diem_lop_du_doan=float(np.mean(margin_drop)),
                             ty_le_token=float(np.mean(frac_tok))))
        print(mode, "m =", m, "xong", round(time.time() - t0), "s", flush=True)
    return rows


rows = run("xoa") + run("giu")
res = pd.DataFrame(rows)
res.to_csv(OUT / "explain_faithfulness.csv", index=False, encoding="utf-8-sig")
for mode in ("xoa", "giu"):
    print(f"\n== {mode.upper()} ==")
    print(res[res.che_do == mode].pivot(index="m", columns="phuong_phap", values="ty_le_doi_du_doan").round(3).to_string())

# ---- biểu đồ
NAVY, GREY, RED, MID = "#0b1b33", "#8fa6c6", "#c0392b", "#5a6b85"
sty = {"AI chọn (đóng góp lớn nhất)": (NAVY, "-", "o"), "TF-IDF lớn nhất": (MID, "--", "s"), "Ngẫu nhiên (theo vị trí)": (GREY, "-.", "^"), "Ngẫu nhiên (theo loại từ)": (GREY, ":", "v")}
fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2))
for a, mode, ttl, yl in ((ax[0], "xoa", "XÓA m từ → dự đoán đổi bao nhiêu % bài?", "% bài bị đổi chuyên mục"), (ax[1], "giu", "CHỈ GIỮ m từ → dự đoán giữ nguyên bao nhiêu % bài?", "% bài giữ nguyên chuyên mục")):
    for name, (c, ls, mk) in sty.items():
        d = res[(res.che_do == mode) & (res.phuong_phap == name)]
        y = d.ty_le_doi_du_doan * 100 if mode == "xoa" else (1 - d.ty_le_doi_du_doan) * 100
        a.plot(d.m, y, color=c, ls=ls, marker=mk, lw=2.2 if name.startswith("AI") else 1.6, label=name)
    a.set_xscale("log"); a.set_xticks(MS); a.set_xticklabels(MS); a.set_xlabel("m = số từ bị xóa" if mode == "xoa" else "m = số từ được giữ lại"); a.set_ylabel(yl); a.set_title(ttl, fontsize=11)
    a.grid(alpha=.25); a.set_ylim(0, 100)
ax[0].legend(fontsize=8.5, loc="upper left")
plt.suptitle("Lời giải thích của AI Lab có phản ánh đúng cách mô hình quyết định không? (825 bài kiểm thử)", fontsize=12, fontweight="bold")
plt.tight_layout(); plt.savefig(OUT / "explain_faithfulness.png", dpi=150); plt.close()

# ---- số liệu tóm tắt cho báo cáo/slide
sm = {"n_test": len(texts), "acc_test": float((pred0 == truth).mean()), "ms": MS}
for mode in ("xoa", "giu"):
    for m in (3, 5, 10):
        for name in pick[m]:
            r = res[(res.che_do == mode) & (res.m == m) & (res.phuong_phap == name)].iloc[0]
            sm[f"{mode}_{m}_{name}"] = dict(rate=float(r.ty_le_doi_du_doan), lo=float(r.ci_lo), hi=float(r.ci_hi), token_share=float(r.ty_le_token))
save_json(sm, "explain_faithfulness.json")
print("\nxong", round(time.time() - t0), "s")
