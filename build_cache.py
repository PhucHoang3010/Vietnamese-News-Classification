"""Dự đoán sẵn chủ đề cho toàn bộ bài báo -> data/predictions.json (chạy tự động lần đầu nếu thiếu)."""
import json, re, unicodedata
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent
SEED = 42


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
    p = np.exp(S * 3); p /= p.sum(1, keepdims=True)
    cls = list(model.classes_); out = {}
    for i, r in enumerate(df.itertuples()):
        o = np.argsort(-p[i])
        out[str(int(r.id))] = {"label": cls[o[0]], "pct": round(float(p[i][o[0]]) * 100, 1),
                               "gap": round(float(p[i][o[0]] - p[i][o[1]]), 3), "test": int(r.id) in test_ids,
                               "split": "test" if int(r.id) in test_ids else "val" if int(r.id) in val_ids else "train" if int(r.id) in train_ids else "dup"}
    acc = np.mean([out[str(int(r.id))]["label"] == r.ground_truth for r in df.itertuples() if int(r.id) in test_ids])
    print("Số bài:", len(out), "| tập kiểm thử:", len(test_ids), "| accuracy kiểm thử:", round(float(acc), 4))
    (ROOT / "data/predictions.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    build()
