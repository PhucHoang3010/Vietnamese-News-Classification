from pathlib import Path
import sys
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

from src.predictor.preprocessing import (
    load_stopwords,
    preprocess_text,
)


MODEL_PATH = PROJECT_ROOT / "models" / "p2_linear_svm_balanced.joblib"
VECTORIZER_PATH = PROJECT_ROOT / "models" / "p2_tfidf_vectorizer.joblib"
INPUT = PROJECT_ROOT / "data" / "processed" / "test.csv"

OUTPUT_DIR = PROJECT_ROOT / "reports" / "internal"
STOPWORDS_PATH = PROJECT_ROOT / "data" / "stopwords_vi.txt"

stopwords = load_stopwords(
    STOPWORDS_PATH
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


print("=" * 80)
print("P2 INTERNAL TEST EVALUATION")
print("=" * 80)

print("\nLoading model...")
model = joblib.load(MODEL_PATH)

print("Loading vectorizer...")
vectorizer = joblib.load(VECTORIZER_PATH)

print("Loading test dataset...")
df = pd.read_csv(INPUT)

print(f"Rows: {len(df)}")
print(f"Columns: {df.columns.tolist()}")

# ---------------------------------------------------------
# Check labels
# ---------------------------------------------------------

y_true = df["label"].astype(str)

print("\nClass distribution:")
print(y_true.value_counts().sort_index().to_string())

# ---------------------------------------------------------
# Preprocess
# ---------------------------------------------------------

print("\nPreprocessing test data...")

texts = df["text"].fillna("").map(
    lambda text: preprocess_text(
        text,
        stopwords,
    )
)

X = vectorizer.transform(texts)

print(f"TF-IDF shape: {X.shape}")

# ---------------------------------------------------------
# Prediction
# ---------------------------------------------------------

print("\nPredicting...")

y_pred = model.predict(X)

# ---------------------------------------------------------
# Accuracy
# ---------------------------------------------------------

accuracy = accuracy_score(y_true, y_pred)

print("\n" + "=" * 80)
print("RESULT")
print("=" * 80)

print(f"\nAccuracy: {accuracy:.6f}")
print(f"Accuracy: {accuracy * 100:.2f}%")

# ---------------------------------------------------------
# Classification report
# ---------------------------------------------------------

report = classification_report(
    y_true,
    y_pred,
    output_dict=True,
    zero_division=0,
)

report_df = pd.DataFrame(report).transpose()

print("\nClassification report:")
print(report_df.to_string())

# ---------------------------------------------------------
# Confusion matrix
# ---------------------------------------------------------

labels = sorted(y_true.unique())

cm = confusion_matrix(
    y_true,
    y_pred,
    labels=labels,
)

cm_df = pd.DataFrame(
    cm,
    index=labels,
    columns=labels,
)

print("\nConfusion matrix:")
print(cm_df.to_string())

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

report_df.to_csv(
    OUTPUT_DIR / "internal_classification_report.csv",
    encoding="utf-8-sig",
)

cm_df.to_csv(
    OUTPUT_DIR / "internal_confusion_matrix.csv",
    encoding="utf-8-sig",
)

summary = {
    "dataset": "data/processed/test.csv",
    "samples": len(df),
    "accuracy": float(accuracy),
    "model": "p2_linear_svm_balanced.joblib",
    "vectorizer": "p2_tfidf_vectorizer.joblib",
    "classes": labels,
}

with open(
    OUTPUT_DIR / "internal_summary.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(
        summary,
        f,
        ensure_ascii=False,
        indent=2,
    )

print("\nSaved:")
print(OUTPUT_DIR / "internal_classification_report.csv")
print(OUTPUT_DIR / "internal_confusion_matrix.csv")
print(OUTPUT_DIR / "internal_summary.json")