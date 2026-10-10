"""Đánh giá tóm tắt tự động: ROUGE trên 400 bài, lấy phần mô tả (sapo) do biên tập viên viết làm bản tham chiếu.
So TextRank với 2 phương pháp cơ sở: Lead-2 (2 câu đầu) và chọn ngẫu nhiên.   python eval_summary.py"""
import json, random, re
from collections import Counter
from pathlib import Path
import app as A

def toks(t): return re.findall(r"[^\W\d_]+", t.lower())
def rouge(hyp, ref, n):
    g = lambda w: Counter(tuple(w[i:i + n]) for i in range(len(w) - n + 1))
    h, r = g(toks(hyp)), g(toks(ref)); ov = sum((h & r).values())
    if not ov: return 0.0
    p, rc = ov / sum(h.values()), ov / sum(r.values()); return 2 * p * rc / (p + rc)

rng = random.Random(1); ids = rng.sample(A.IDS, 400); K = 2
res = {"TextRank": [[], []], "Lead-2": [[], []], "Ngẫu nhiên": [[], []]}
for i in ids:
    a = A.ART[i]; ref = a["desc"]; sents = A.split_sentences(a["content"])[:80]
    if len(sents) < 4 or len(ref.split()) < 8: continue
    tr, _, _ = A.summarize(a["content"], K, a["title"])
    cand = {"TextRank": tr, "Lead-2": sents[:K], "Ngẫu nhiên": rng.sample(sents, K)}
    for name, c in cand.items():
        for j, n in enumerate((1, 2)): res[name][j].append(rouge(" ".join(c), ref, n))
out = {k: {"rouge1": round(sum(v[0]) / len(v[0]), 4), "rouge2": round(sum(v[1]) / len(v[1]), 4), "n": len(v[0])} for k, v in res.items()}
Path(__file__).parent.joinpath("outputs/summary_eval.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
