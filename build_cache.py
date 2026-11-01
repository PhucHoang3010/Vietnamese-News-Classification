"""Dự đoán sẵn chủ đề cho toàn bộ bài báo -> data/predictions.json (chạy tự động lần đầu nếu thiếu)."""
import json, re, unicodedata
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import train_test_split

import conformal

ROOT = Path(__file__).resolve().parent
SEED = 42
TEMP = 4.3          # phải trùng với TEMP trong app.py (hệ số nhiệt độ chọn trên tập kiểm định, xem experiments/exp5_calibration.py)


def clean(t):
    t = unicodedata.normalize("NFC", str(t)).lower()
    t = re.sub(r"https?://\S+|\S+@\S+", " ", t); t = re.sub(r"\d+", " ", t)
    t = re.sub(r"[^\w\s]|_", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def build():
    model = joblib.load(ROOT / "model.joblib")
    df = pd.read_csv(ROOT / "data/news_dataset.csv", usecols=["id", "title", "description", "content", "ground_truth"])
    df["text"] = (df.title.fillna("") + " " + df.description.fillna("") + " " + df.content.fillna("")).map(clean)
    # tái tạo đúng cách chia dữ liệu của train.py để biết bài nào thuộc tập kiểm thử (chưa dùng khi huấn luyện)
    d2 = df[df.text.str.len() > 30].drop_duplicates("text").reset_index(drop=True)
    tr, tmp = train_test_split(d2, test_size=0.30, stratify=d2.ground_truth, random_state=SEED)
    va, te = train_test_split(tmp, test_size=0.50, stratify=tmp.ground_truth, random_state=SEED)
    test_ids = set(te.id.astype(int)); val_ids = set(va.id.astype(int)); train_ids = set(tr.id.astype(int))
    S = model.decision_function(df.text)
    p = np.exp((S - S.max(axis=1, keepdims=True)) * TEMP); p /= p.sum(1, keepdims=True)
    cls = list(model.classes_); out = {}
    # --- dự đoán có bảo đảm (conformal): chỉ dùng điểm của AI "chưa từng thấy bài đó" -------------------------------
    # bài kiểm định/kiểm thử: điểm của chính mô hình cuối; bài huấn luyện (mô hình đã học thuộc): dự đoán chéo 5-fold
    ids = df.id.astype(int).to_numpy(); row_of = {int(i): n for n, i in enumerate(ids)}
    tr_ids = tr.id.astype(int).to_numpy(); oof_file = ROOT / "data/oof_train.npz"
    if oof_file.exists() and np.array_equal(np.load(oof_file)["ids"], tr_ids):
        Doof = np.load(oof_file)["D"]
    else:
        print("Đang tính dự đoán chéo 5-fold cho 3.850 bài huấn luyện (khoảng 1–2 phút, chỉ chạy một lần)...", flush=True)
        Doof = conformal.cross_fit_scores(tr.text.to_numpy(), tr.ground_truth.to_numpy(), lambda: clone(model))
        np.savez_compressed(oof_file, ids=tr_ids, D=Doof.astype(np.float32))
    Dun = S.copy()                                                    # điểm "chưa từng thấy" cho mọi bài
    for n, i in enumerate(tr_ids): Dun[row_of[int(i)]] = Doof[n]
    cal_ids = np.concatenate([va.id.astype(int).to_numpy(), tr_ids]); cal_rows = [row_of[int(i)] for i in cal_ids]
    y_all = np.searchsorted(np.array(cls), df.ground_truth.to_numpy())
    thr = conformal.calibrate(Dun[cal_rows], y_all[cal_rows])        # 4.675 bài (kiểm định + dự đoán chéo)
    SETS = {a: conformal.predict_sets(Dun, thr[str(a)]) for a in conformal.ALPHAS}
    te_rows = [row_of[int(i)] for i in te.id.astype(int)]
    info = {"method": conformal.METHOD, "classes": cls, "n_cal": len(cal_rows), "alphas": list(conformal.ALPHAS), "default_alpha": 0.05, "thresholds": thr,
            "test": {str(a): conformal.evaluate(SETS[a][te_rows], y_all[te_rows]) for a in conformal.ALPHAS}}
    (ROOT / "data/conformal.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    for i, r in enumerate(df.itertuples()):
        o = np.argsort(-p[i])
        out[str(int(r.id))] = {"label": cls[o[0]], "pct": round(float(p[i][o[0]]) * 100, 1),
                               "gap": round(float(p[i][o[0]] - p[i][o[1]]), 3), "test": int(r.id) in test_ids,
                               "split": "test" if int(r.id) in test_ids else "val" if int(r.id) in val_ids else "train" if int(r.id) in train_ids else "dup",
                               "sets": {str(round((1 - a) * 100)): [cls[k] for k in np.argsort(-Dun[i]) if SETS[a][i, k]] for a in conformal.ALPHAS},
                               "mg": {cls[k]: round(float(Dun[i].max() - Dun[i][k]), 3) for k in np.argsort(-Dun[i]) if SETS[conformal.ALPHAS[-1]][i, k]}}   # khoảng cách điểm tới chuyên mục đứng đầu (càng nhỏ càng sát nút)
    acc = np.mean([out[str(int(r.id))]["label"] == r.ground_truth for r in df.itertuples() if int(r.id) in test_ids])
    print("Số bài:", len(out), "| tập kiểm thử:", len(test_ids), "| accuracy kiểm thử:", round(float(acc), 4))
    for a in conformal.ALPHAS:
        t = info["test"][str(a)]; print(f"  bảo đảm {round((1 - a) * 100)}%: độ phủ kiểm thử {t['coverage']:.3f}, trung bình {t['avg_size']:.2f} chuyên mục/bài, {t['singleton_share']:.0%} bài chỉ 1 chuyên mục")
    (ROOT / "data/predictions.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    build()
