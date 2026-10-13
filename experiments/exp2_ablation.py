"""Thí nghiệm 2 — Bỏ/đổi TỪNG thành phần (ablation) của pipeline, mỗi lần chỉ đổi một thứ.
Đo bằng 5-fold CV phân tầng trên (train + val) = 4.675 bài. TẬP KIỂM THỬ KHÔNG ĐƯỢC DÙNG.
TF-IDF được học lại trong từng fold (không rò rỉ). Mô hình: Linear SVM với C lấy từ thí nghiệm 1.
Chạy:  python experiments/exp2_ablation.py
"""
import sys, time
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import *
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

plt.rcParams["font.family"] = "DejaVu Sans"
df, i_tr, i_va, i_te = load(); check_split(df, i_tr, i_va, i_te)
dev = np.concatenate([i_tr, i_va])                       # bỏ hẳn tập test
D = df.iloc[dev].reset_index(drop=True)
y = D.label.values
tun = load_json("tuning_results_best_svm.json", {"C": 2.0})
C = float(tun["C"])
print("Dùng C =", C)


def raw_lower(t):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(t)).lower()).strip()


def no_accent(t):
    t = unicodedata.normalize("NFD", t)
    return unicodedata.normalize("NFC", "".join(c for c in t if unicodedata.category(c) != "Mn").replace("đ", "d"))


def keep_digits(t):
    t = unicodedata.normalize("NFC", str(t)).lower()
    t = re.sub(r"https?://\S+|\S+@\S+", " ", t)
    t = re.sub(r"[^\w\s]|_", " ", t)
    return re.sub(r"\s+", " ", t).strip()


raw = (D.title + " " + D.description + " " + D.content)
TEXT = {
    "chuẩn (tiêu đề+sapo+nội dung, đã làm sạch)": D.text.values,
    "chỉ tiêu đề": D.title.map(clean).values,
    "tiêu đề + sapo": (D.title + " " + D.description).map(clean).values,
    "chỉ nội dung": D.content.map(clean).values,
    "chỉ lowercase, không bỏ số/dấu câu": raw.map(raw_lower).values,
    "giữ lại chữ số": raw.map(keep_digits).values,
    "bỏ dấu tiếng Việt": D.text.map(no_accent).values,
}
# tách từ bằng pyvi (nếu cài được)
seg_file = CACHE / "pyvi_seg.json"
try:
    from pyvi import ViTokenizer
    if seg_file.exists():
        seg = json.loads(seg_file.read_text(encoding="utf-8"))
    else:
        t0 = time.time()
        seg = {str(i): ViTokenizer.tokenize(unicodedata.normalize("NFC", a)) for i, a in zip(df.id, df.title + ". " + df.description + ". " + df.content)}
        seg_file.write_text(json.dumps(seg, ensure_ascii=False), encoding="utf-8"); print(f"tách từ xong {time.time()-t0:.0f}s")

    def clean_seg(t):
        t = t.lower(); t = re.sub(r"https?://\S+|\S+@\S+", " ", t); t = re.sub(r"\d+", " ", t); t = re.sub(r"[^\w\s]", " ", t)
        return re.sub(r"\s+", " ", t).strip()
    TEXT["tách từ bằng pyvi"] = np.array([clean_seg(seg[str(i)]) for i in D.id])
except Exception as e:
    print("Bỏ qua tách từ:", repr(e)[:120])

CV = StratifiedKFold(5, shuffle=True, random_state=SEED)
FOLDS = list(CV.split(np.zeros(len(y)), y))
BASE = dict(ngram_range=(1, 2), min_df=2, max_df=0.9, sublinear_tf=True, max_features=200000, use_idf=True)
VARS = [  # (nhóm, tên, ghi chú, thay đổi tfidf, khóa văn bản)
    ("Chuẩn", "Cấu hình chuẩn", "1–2 gram, min_df=2, max_df=0.9, log-tf, 200.000 đặc trưng", {}, "chuẩn (tiêu đề+sapo+nội dung, đã làm sạch)"),
    ("N-gram", "Chỉ từ đơn (1-gram)", "", dict(ngram_range=(1, 1)), None),
    ("N-gram", "1–3 gram", "", dict(ngram_range=(1, 3)), None),
    ("Trọng số", "Bỏ log-tf (sublinear_tf=False)", "", dict(sublinear_tf=False), None),
    ("Trọng số", "Bỏ IDF (chỉ TF)", "", dict(use_idf=False), None),
    ("Từ vựng", "Tối đa 5.000 đặc trưng", "", dict(max_features=5000), None),
    ("Từ vựng", "Tối đa 20.000 đặc trưng", "", dict(max_features=20000), None),
    ("Từ vựng", "Tối đa 50.000 đặc trưng", "", dict(max_features=50000), None),
    ("Từ vựng", "Không giới hạn đặc trưng", "", dict(max_features=None), None),
    ("Từ vựng", "min_df = 1", "", dict(min_df=1), None),
    ("Từ vựng", "min_df = 5", "", dict(min_df=5), None),
    ("Từ vựng", "max_df = 0.5", "", dict(max_df=0.5), None),
    ("Từ vựng", "max_df = 1.0 (không loại từ phổ biến)", "", dict(max_df=1.0), None),
    ("Dữ liệu vào", "Chỉ tiêu đề", "", {}, "chỉ tiêu đề"),
    ("Dữ liệu vào", "Tiêu đề + sapo", "", {}, "tiêu đề + sapo"),
    ("Dữ liệu vào", "Chỉ nội dung", "", {}, "chỉ nội dung"),
    ("Tiền xử lý", "Chỉ chữ thường (giữ số, dấu câu)", "", {}, "chỉ lowercase, không bỏ số/dấu câu"),
    ("Tiền xử lý", "Giữ chữ số", "", {}, "giữ lại chữ số"),
    ("Tiền xử lý", "Bỏ dấu tiếng Việt", "", {}, "bỏ dấu tiếng Việt"),
]
if "tách từ bằng pyvi" in TEXT:
    VARS += [("Tách từ", "Tách từ (pyvi) + 1-gram", "", dict(ngram_range=(1, 1)), "tách từ bằng pyvi"),
             ("Tách từ", "Tách từ (pyvi) + 1–2 gram", "", {}, "tách từ bằng pyvi")]


def run_fold(tr, te, kw, key):
    X = TEXT[key]
    p = Pipeline([("tfidf", tfidf(**{**BASE, **kw})), ("clf", LinearSVC(C=C))]).fit(X[tr], y[tr])
    pr = p.predict(X[te])
    return scores(y[te], pr)


rows = []
for grp, name, note, kw, key in VARS:
    key = key or "chuẩn (tiêu đề+sapo+nội dung, đã làm sạch)"
    t0 = time.time()
    r = Parallel(n_jobs=4)(delayed(run_fold)(tr, te, kw, key) for tr, te in FOLDS)
    f1 = np.array([a["macro_f1"] for a in r]); ac = np.array([a["acc"] for a in r])
    rows.append(dict(nhom=grp, bien_the=name, macro_f1_mean=f1.mean(), macro_f1_std=f1.std(ddof=1), acc_mean=ac.mean(), folds=f1.tolist()))
    print(f"{grp:12s} {name:42s} F1={f1.mean():.4f}±{f1.std(ddof=1):.4f}  ({time.time()-t0:.0f}s)", flush=True)
res = pd.DataFrame(rows)
base = res.iloc[0]
res["delta_vs_base"] = res.macro_f1_mean - base.macro_f1_mean
# kiểm định cặp (paired) so với cấu hình chuẩn: số fold tốt hơn/kém hơn và t-test cặp
from scipy import stats
bf = np.array(base.folds)
res["folds_better"] = [int((np.array(f) > bf).sum()) for f in res.folds]
res["paired_t_p"] = [1.0 if i == 0 else float(stats.ttest_rel(np.array(f), bf).pvalue) for i, f in enumerate(res.folds)]
res.drop(columns="folds").to_csv(OUT / "ablation_results.csv", index=False, encoding="utf-8-sig")
save_json(res.to_dict("records"), "ablation_results.json")
# biểu đồ chênh lệch so với chuẩn
d = res.iloc[1:].iloc[::-1]
fig, ax = plt.subplots(figsize=(9.5, 7.2))
cols = ["#0b1b33" if v >= 0 else "#8fa6c6" for v in d.delta_vs_base]
ax.barh(d.bien_the, d.delta_vs_base * 100, color=cols)
for y_, v in enumerate(d.delta_vs_base * 100):
    ax.text(v + (0.08 if v >= 0 else -0.08), y_, f"{v:+.2f}", va="center", ha="left" if v >= 0 else "right", fontsize=8)
ax.axvline(0, color="k", lw=1); ax.set_xlabel(f"Thay đổi Macro-F1 so với cấu hình chuẩn ({base.macro_f1_mean*100:.2f}%), đơn vị điểm phần trăm")
ax.set_title("Ablation: đổi từng thành phần, đo bằng 5-fold CV (train+val, không dùng tập test)"); plt.tight_layout(); plt.savefig(OUT / "ablation.png", dpi=150); plt.close()
print(res[["nhom", "bien_the", "macro_f1_mean", "macro_f1_std", "delta_vs_base", "folds_better", "paired_t_p"]].round(4).to_string())
