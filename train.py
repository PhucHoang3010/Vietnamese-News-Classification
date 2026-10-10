"""Huấn luyện & đánh giá mô hình phân loại tin tức tiếng Việt (CPU, không cần deep learning).

Chạy:  python do_an/train.py
Kết quả: do_an/outputs/ (biểu đồ, bảng, metrics.json) và do_an/model.joblib
"""
import json, re, sys, time, unicodedata
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data/news_dataset.csv"
OUT = ROOT / "outputs"; OUT.mkdir(exist_ok=True)
SEED = 42
plt.rcParams["font.family"] = "DejaVu Sans"


def clean(t: str) -> str:
    t = unicodedata.normalize("NFC", str(t)).lower()
    t = re.sub(r"https?://\S+|\S+@\S+", " ", t)
    t = re.sub(r"\d+", " ", t)                       # bỏ số
    t = re.sub(r"[^\w\s]|_", " ", t)                 # bỏ dấu câu
    return re.sub(r"\s+", " ", t).strip()


df = pd.read_csv(DATA, encoding="utf-8", usecols=["title", "description", "content", "ground_truth"])
df["text"] = (df.title.fillna("") + " " + df.description.fillna("") + " " + df.content.fillna("")).map(clean)
df = df[df.text.str.len() > 30].drop_duplicates("text").reset_index(drop=True)
df = df.rename(columns={"ground_truth": "label"})
print("Số mẫu:", len(df)); print(df.label.value_counts())

# Chia 70/15/15 có phân tầng
X_tr, X_tmp, y_tr, y_tmp = train_test_split(df.text, df.label, test_size=0.30, stratify=df.label, random_state=SEED)
X_va, X_te, y_va, y_te = train_test_split(X_tmp, y_tmp, test_size=0.50, stratify=y_tmp, random_state=SEED)
print(f"train={len(X_tr)} val={len(X_va)} test={len(X_te)}")

# EDA
plt.figure(figsize=(8, 4)); df.label.value_counts().plot.barh(color="#3b82f6")
plt.title("Phân bố số bài theo chủ đề"); plt.tight_layout(); plt.savefig(OUT / "phan_bo_nhan.png", dpi=150); plt.close()
plt.figure(figsize=(8, 4)); df.text.str.split().str.len().clip(upper=2000).plot.hist(bins=50, color="#10b981")
plt.title("Phân bố độ dài bài (số từ)"); plt.xlabel("số từ"); plt.tight_layout(); plt.savefig(OUT / "do_dai_bai.png", dpi=150); plt.close()

# So sánh mô hình (đặc trưng TF-IDF unigram+bigram)
def tfidf(): return TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.9, sublinear_tf=True, max_features=200000)
models = {
    "Complement Naive Bayes": ComplementNB(alpha=0.3),
    "Logistic Regression": LogisticRegression(C=10, max_iter=1000),
    "Linear SVM": LinearSVC(C=1.0),
    "Random Forest": RandomForestClassifier(n_estimators=200, n_jobs=1, random_state=SEED),
}
rows = []
for name, clf in models.items():
    t0 = time.time(); p = Pipeline([("tfidf", tfidf()), ("clf", clf)]).fit(X_tr, y_tr)
    pv = p.predict(X_va)
    rows.append(dict(model=name, val_acc=accuracy_score(y_va, pv), val_macro_f1=f1_score(y_va, pv, average="macro"), train_sec=time.time() - t0))
    print(rows[-1])
bench = pd.DataFrame(rows).sort_values("val_macro_f1", ascending=False)
bench.to_csv(OUT / "so_sanh_mo_hinh.csv", index=False)
plt.figure(figsize=(8, 4)); sns.barplot(data=bench, y="model", x="val_macro_f1", color="#6366f1")
plt.xlim(0.5, 1); plt.title("So sánh Macro-F1 trên tập validation"); plt.tight_layout(); plt.savefig(OUT / "so_sanh_mo_hinh.png", dpi=150); plt.close()

# Tinh chỉnh siêu tham số cho Linear SVM trên train (CV 3-fold)
gs = GridSearchCV(Pipeline([("tfidf", tfidf()), ("clf", LinearSVC())]),
                  {"tfidf__ngram_range": [(1, 1), (1, 2)], "clf__C": [0.1, 0.5, 1, 2]},
                  scoring="f1_macro", cv=3, n_jobs=1).fit(X_tr, y_tr)
print("Best:", gs.best_params_, gs.best_score_)
best = gs.best_estimator_

# Đánh giá cuối trên tập test (chỉ dùng 1 lần)
pt = best.predict(X_te)
rep = classification_report(y_te, pt, output_dict=True, digits=4)
pd.DataFrame(rep).T.to_csv(OUT / "bao_cao_phan_loai.csv", encoding="utf-8-sig")
print(classification_report(y_te, pt, digits=4))
labels = sorted(df.label.unique()); cm = confusion_matrix(y_te, pt, labels=labels)
plt.figure(figsize=(9, 7)); sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels)
plt.xlabel("Dự đoán"); plt.ylabel("Thực tế"); plt.title("Ma trận nhầm lẫn (tập test)"); plt.tight_layout()
plt.savefig(OUT / "ma_tran_nham_lan.png", dpi=150); plt.close()

# Từ khóa đặc trưng mỗi chủ đề
vec, clf = best.named_steps["tfidf"], best.named_steps["clf"]
names = np.array(vec.get_feature_names_out()); kw = {c: names[np.argsort(clf.coef_[i])[-10:][::-1]].tolist() for i, c in enumerate(clf.classes_)}
json.dump(kw, open(OUT / "tu_khoa_dac_trung.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# Lỗi tiêu biểu
err = pd.DataFrame({"that": y_te.values, "du_doan": pt, "doan_van": X_te.str[:200].values})
err[err.that != err.du_doan].to_csv(OUT / "mau_du_doan_sai.csv", index=False, encoding="utf-8-sig")

metrics = dict(n_samples=len(df), n_classes=len(labels), best_params={k: str(v) for k, v in gs.best_params_.items()},
               cv_macro_f1=float(gs.best_score_), test_accuracy=float(accuracy_score(y_te, pt)), test_macro_f1=float(f1_score(y_te, pt, average="macro")),
               test_size=len(X_te))
json.dump(metrics, open(OUT / "metrics.json", "w", encoding="utf-8"), indent=1)
print(metrics)
joblib.dump(best, ROOT / "model.joblib", compress=3)
