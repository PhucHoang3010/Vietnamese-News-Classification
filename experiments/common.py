"""Dùng chung cho các thí nghiệm: nạp dữ liệu và chia train/val/test GIỐNG HỆT train.py (seed 42)."""
import json, re, sys, time, unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
SEED = 42
OUT = ROOT / "outputs" / "experiments"
OUT.mkdir(parents=True, exist_ok=True)
CACHE = ROOT / "experiments" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)


def clean(t):
    t = unicodedata.normalize("NFC", str(t)).lower()
    t = re.sub(r"https?://\S+|\S+@\S+", " ", t)
    t = re.sub(r"\d+", " ", t)
    t = re.sub(r"[^\w\s]|_", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def load():
    """Trả về df (đủ cột gốc + text đã làm sạch) và chỉ số 3 tập. Phép chia trùng với train.py."""
    df = pd.read_csv(ROOT / "data/news_dataset.csv", encoding="utf-8", usecols=["id", "title", "description", "content", "ground_truth"])
    for c in ("title", "description", "content"):
        df[c] = df[c].fillna("")
    df["text"] = (df.title + " " + df.description + " " + df.content).map(clean)
    df = df[df.text.str.len() > 30].drop_duplicates("text").reset_index(drop=True)
    df = df.rename(columns={"ground_truth": "label"})
    idx = np.arange(len(df))
    i_tr, i_tmp = train_test_split(idx, test_size=0.30, stratify=df.label, random_state=SEED)
    i_va, i_te = train_test_split(i_tmp, test_size=0.50, stratify=df.label.iloc[i_tmp], random_state=SEED)
    return df, i_tr, i_va, i_te


def check_split(df, i_tr, i_va, i_te):
    """Kiểm tra phép chia khớp với dự đoán đã lưu cho website (cờ test)."""
    pred = json.loads((ROOT / "data/predictions.json").read_text(encoding="utf-8"))
    test_ids = {int(k) for k, v in pred.items() if v["test"]}
    mine = set(df.id.iloc[i_te].astype(int))
    assert len(i_tr) == 3850 and len(i_va) == 825 and len(i_te) == 825, (len(i_tr), len(i_va), len(i_te))
    assert mine == test_ids, "Tập test không khớp predictions.json"
    return True


def tfidf(**kw):
    p = dict(ngram_range=(1, 2), min_df=2, max_df=0.9, sublinear_tf=True, max_features=200000)
    p.update(kw)
    return TfidfVectorizer(**p)


def scores(y, p):
    return dict(acc=float(accuracy_score(y, p)), macro_f1=float(f1_score(y, p, average="macro")))


def save_json(obj, name):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=float), encoding="utf-8")


def load_json(name, default=None):
    f = OUT / name
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else default
