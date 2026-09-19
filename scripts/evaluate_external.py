from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)


# ============================================================
# CONFIG
# ============================================================

MODEL_PATH = Path("models/p2_linear_svm_balanced.joblib")
VECTORIZER_PATH = Path("models/p2_tfidf_vectorizer.joblib")

TEST_PATH = Path(
    "data/external/viet_online_news_test.csv"
)

REPORT_DIR = Path("reports/external")

PREDICTIONS_PATH = REPORT_DIR / "external_predictions.csv"
CLASSIFICATION_REPORT_PATH = (
    REPORT_DIR / "external_classification_report.csv"
)
CONFUSION_MATRIX_PATH = (
    REPORT_DIR / "external_confusion_matrix.csv"
)
MARGIN_ANALYSIS_PATH = (
    REPORT_DIR / "external_margin_analysis.csv"
)
SUMMARY_PATH = REPORT_DIR / "external_summary.json"


# ============================================================
# PREPROCESSING
# ============================================================

def preprocess_text(text: str) -> str:
    """
    IMPORTANT:
    Must match the preprocessing used when training P2.
    """

    from underthesea import word_tokenize

    text = str(text).strip()

    if not text:
        return ""

    tokens = word_tokenize(text)

    return " ".join(tokens)


# ============================================================
# LOAD MODEL
# ============================================================

print("=" * 80)
print("EXTERNAL EVALUATION - P2")
print("=" * 80)

print("\nLoading model...")

model = joblib.load(MODEL_PATH)

print(f"Model      : {type(model).__name__}")

print("\nLoading vectorizer...")

vectorizer = joblib.load(VECTORIZER_PATH)

print(
    f"Vectorizer : {type(vectorizer).__name__}"
)


# ============================================================
# LOAD TEST DATA
# ============================================================

print("\nLoading external test set...")

df = pd.read_csv(
    TEST_PATH,
    encoding="utf-8-sig",
)

print(f"Rows       : {len(df):,}")


required_columns = [
    "text",
    "ground_truth",
]

missing = [
    col
    for col in required_columns
    if col not in df.columns
]

if missing:
    raise RuntimeError(
        f"Missing columns: {missing}"
    )


df["text"] = df["text"].fillna("").astype(str)
df["ground_truth"] = (
    df["ground_truth"]
    .fillna("")
    .astype(str)
)


# ============================================================
# PREPROCESS
# ============================================================

print("\nPreprocessing text...")

df["processed_text"] = df["text"].apply(
    preprocess_text
)


# ============================================================
# TF-IDF
# ============================================================

print("\nTransforming with existing TF-IDF...")

X = vectorizer.transform(
    df["processed_text"]
)

print(
    f"TF-IDF shape: {X.shape}"
)


# ============================================================
# PREDICT
# ============================================================

print("\nRunning LinearSVC prediction...")

predictions = model.predict(X)

decision_scores = model.decision_function(X)


# ============================================================
# HANDLE DECISION SCORE SHAPE
# ============================================================

if decision_scores.ndim == 1:

    # Binary case
    sorted_scores = np.sort(
        decision_scores.reshape(-1, 1),
        axis=1,
    )

    margins = np.abs(
        decision_scores
    )

else:

    sorted_scores = np.sort(
        decision_scores,
        axis=1,
    )

    # Difference between top 1 and top 2
    margins = (
        sorted_scores[:, -1]
        - sorted_scores[:, -2]
    )


# ============================================================
# RESULTS
# ============================================================

df["prediction"] = predictions
df["correct"] = (
    df["prediction"]
    == df["ground_truth"]
)

df["margin"] = margins


# ============================================================
# METRICS
# ============================================================

y_true = df["ground_truth"]
y_pred = df["prediction"]

accuracy = accuracy_score(
    y_true,
    y_pred,
)

report_dict = classification_report(
    y_true,
    y_pred,
    output_dict=True,
    zero_division=0,
)

report_df = pd.DataFrame(
    report_dict
).transpose()


# ============================================================
# CONFUSION MATRIX
# ============================================================

labels = sorted(
    set(y_true)
    | set(y_pred)
)

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


# ============================================================
# MARGIN ANALYSIS
# ============================================================

def margin_bucket(margin):

    if margin < 0.10:
        return "<0.10"

    if margin < 0.20:
        return "0.10–0.20"

    if margin < 0.30:
        return "0.20–0.30"

    if margin < 0.50:
        return "0.30–0.50"

    return ">=0.50"


df["margin_bucket"] = df["margin"].apply(
    margin_bucket
)


margin_rows = []

bucket_order = [
    "<0.10",
    "0.10–0.20",
    "0.20–0.30",
    "0.30–0.50",
    ">=0.50",
]

for bucket in bucket_order:

    subset = df[
        df["margin_bucket"] == bucket
    ]

    total = len(subset)

    errors = int(
        (~subset["correct"]).sum()
    )

    correct = int(
        subset["correct"].sum()
    )

    error_rate = (
        errors / total
        if total
        else 0
    )

    accuracy_bucket = (
        correct / total
        if total
        else 0
    )

    margin_rows.append({
        "margin_bucket": bucket,
        "total": total,
        "correct": correct,
        "errors": errors,
        "accuracy": accuracy_bucket,
        "error_rate": error_rate,
    })


margin_df = pd.DataFrame(
    margin_rows
)


# ============================================================
# PER-CLASS SUMMARY
# ============================================================

class_rows = []

for category in sorted(
    y_true.unique()
):

    subset = df[
        df["ground_truth"] == category
    ]

    class_rows.append({
        "category": category,
        "total": len(subset),
        "correct": int(
            subset["correct"].sum()
        ),
        "errors": int(
            (~subset["correct"]).sum()
        ),
        "accuracy": float(
            subset["correct"].mean()
        ),
        "avg_margin": float(
            subset["margin"].mean()
        ),
        "median_margin": float(
            subset["margin"].median()
        ),
    })

class_df = pd.DataFrame(
    class_rows
)


# ============================================================
# LOWEST MARGIN EXAMPLES
# ============================================================

lowest_margin_df = (
    df.sort_values("margin")
    [
        [
            "id",
            "title",
            "source_category",
            "ground_truth",
            "prediction",
            "correct",
            "margin",
        ]
    ]
    .head(100)
)


# ============================================================
# SAVE REPORTS
# ============================================================

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


df[
    [
        "id",
        "title",
        "source_category",
        "ground_truth",
        "prediction",
        "correct",
        "margin",
        "margin_bucket",
    ]
].to_csv(
    PREDICTIONS_PATH,
    index=False,
    encoding="utf-8-sig",
)


report_df.to_csv(
    CLASSIFICATION_REPORT_PATH,
    encoding="utf-8-sig",
)


cm_df.to_csv(
    CONFUSION_MATRIX_PATH,
    encoding="utf-8-sig",
)


margin_df.to_csv(
    MARGIN_ANALYSIS_PATH,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# SUMMARY
# ============================================================

summary = {
    "test_rows": int(len(df)),
    "accuracy": float(accuracy),

    "macro_precision": float(
        report_dict["macro avg"]["precision"]
    ),

    "macro_recall": float(
        report_dict["macro avg"]["recall"]
    ),

    "macro_f1": float(
        report_dict["macro avg"]["f1-score"]
    ),

    "weighted_precision": float(
        report_dict["weighted avg"]["precision"]
    ),

    "weighted_recall": float(
        report_dict["weighted avg"]["recall"]
    ),

    "weighted_f1": float(
        report_dict["weighted avg"]["f1-score"]
    ),

    "correct": int(
        df["correct"].sum()
    ),

    "errors": int(
        (~df["correct"]).sum()
    ),

    "margin_distribution": {
        row["margin_bucket"]: {
            "total": int(row["total"]),
            "correct": int(row["correct"]),
            "errors": int(row["errors"]),
            "accuracy": float(row["accuracy"]),
            "error_rate": float(row["error_rate"]),
        }
        for _, row in margin_df.iterrows()
    },
}


with open(
    SUMMARY_PATH,
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        summary,
        f,
        ensure_ascii=False,
        indent=2,
    )


# ============================================================
# PRINT RESULTS
# ============================================================

print("\n" + "=" * 80)
print("EXTERNAL EVALUATION RESULT")
print("=" * 80)

print(
    f"\nTest samples : {len(df):,}"
)

print(
    f"Correct      : {summary['correct']:,}"
)

print(
    f"Errors       : {summary['errors']:,}"
)

print(
    f"\nAccuracy     : {accuracy:.4f}"
)

print(
    f"Macro F1     : "
    f"{summary['macro_f1']:.4f}"
)

print(
    f"Weighted F1  : "
    f"{summary['weighted_f1']:.4f}"
)


print("\n" + "=" * 80)
print("CLASSIFICATION REPORT")
print("=" * 80)

print(
    report_df.to_string()
)


print("\n" + "=" * 80)
print("MARGIN DISTRIBUTION")
print("=" * 80)

print(
    margin_df.to_string(index=False)
)


print("\n" + "=" * 80)
print("PER-CLASS ACCURACY")
print("=" * 80)

print(
    class_df[
        [
            "category",
            "total",
            "correct",
            "errors",
            "accuracy",
            "avg_margin",
        ]
    ].to_string(index=False)
)


print("\n" + "=" * 80)
print("LOWEST MARGIN EXAMPLES")
print("=" * 80)

print(
    lowest_margin_df.head(20).to_string(
        index=False
    )
)


print("\n" + "=" * 80)
print("REPORTS SAVED")
print("=" * 80)

print(
    f"Predictions       : {PREDICTIONS_PATH}"
)

print(
    f"Classification    : "
    f"{CLASSIFICATION_REPORT_PATH}"
)

print(
    f"Confusion matrix  : "
    f"{CONFUSION_MATRIX_PATH}"
)

print(
    f"Margin analysis   : "
    f"{MARGIN_ANALYSIS_PATH}"
)

print(
    f"Summary           : "
    f"{SUMMARY_PATH}"
)

print("\nDone.")