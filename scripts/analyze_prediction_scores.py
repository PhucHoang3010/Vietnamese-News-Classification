from pathlib import Path
import joblib
import pandas as pd

MODEL_PATH = Path("models/p2_linear_svm_balanced.joblib")
VECTORIZER_PATH = Path("models/p2_tfidf_vectorizer.joblib")
INPUT = Path("data/external/viet_online_news_test.csv")
OUTPUT = Path("reports/external/prediction_score_analysis.csv")

print("=" * 80)
print("ANALYZING LINEAR SVM DECISION SCORES")
print("=" * 80)

print("\nLoading model...")
model = joblib.load(MODEL_PATH)

print("Loading vectorizer...")
vectorizer = joblib.load(VECTORIZER_PATH)

print("Loading dataset...")
df = pd.read_csv(INPUT, encoding="utf-8-sig")

print(f"Rows: {len(df)}")

# ---------------------------------------------------------
# Preprocess
# ---------------------------------------------------------

from underthesea import word_tokenize

def preprocess(text):
    text = str(text)
    tokens = word_tokenize(text)
    return " ".join(tokens)

print("\nPreprocessing...")

texts = df["text"].fillna("").map(preprocess)

X = vectorizer.transform(texts)

print(f"Matrix shape: {X.shape}")

# ---------------------------------------------------------
# Decision scores
# ---------------------------------------------------------

print("\nCalculating decision scores...")

scores = model.decision_function(X)

classes = model.classes_

# Top 1 / Top 2
top_indices = scores.argsort(axis=1)[:, ::-1]

top1_idx = top_indices[:, 0]
top2_idx = top_indices[:, 1]

df["prediction_top1"] = classes[top1_idx]
df["score_top1"] = scores[
    range(len(df)),
    top1_idx
]

df["prediction_top2"] = classes[top2_idx]
df["score_top2"] = scores[
    range(len(df)),
    top2_idx
]

df["margin"] = (
    df["score_top1"]
    - df["score_top2"]
)

df["correct"] = (
    df["ground_truth"]
    == df["prediction_top1"]
)

# ---------------------------------------------------------
# Focus on Khoa học -> Kinh doanh
# ---------------------------------------------------------

subset = df[
    (df["ground_truth"] == "Khoa học")
    & (df["prediction_top1"] == "Kinh doanh")
].copy()

subset = subset.sort_values("margin")

columns = [
    "id",
    "title",
    "source_category",
    "ground_truth",
    "prediction_top1",
    "score_top1",
    "prediction_top2",
    "score_top2",
    "margin",
    "correct",
]

subset[columns].to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

print("\n" + "=" * 80)
print("KHOA HỌC → KINH DOANH")
print("=" * 80)

print(f"Total: {len(subset)}")

print("\nLowest-margin examples:\n")

print(
    subset[columns]
    .head(30)
    .to_string(index=False)
)

print("\nSaved:")
print(OUTPUT)