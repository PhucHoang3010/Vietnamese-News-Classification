from pathlib import Path
import pandas as pd


INPUT = Path(
    "reports/external/external_predictions.csv"
)

OUTPUT = Path(
    "reports/external/top_confusion_pairs.csv"
)


df = pd.read_csv(
    INPUT,
    encoding="utf-8-sig",
)


# Chỉ lấy prediction sai
errors = df[
    df["ground_truth"] != df["prediction"]
].copy()


# Đếm từng cặp
pairs = (
    errors
    .groupby(
        ["ground_truth", "prediction"]
    )
    .size()
    .reset_index(
        name="count"
    )
    .sort_values(
        "count",
        ascending=False,
    )
)


# Tỷ lệ lỗi trong từng ground-truth class
class_errors = (
    errors
    .groupby("ground_truth")
    .size()
    .to_dict()
)


pairs["error_rate_within_class"] = (
    pairs.apply(
        lambda row:
        row["count"]
        / class_errors[row["ground_truth"]],
        axis=1,
    )
)


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)


pairs.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8-sig",
)


print("=" * 80)
print("TOP CONFUSION PAIRS")
print("=" * 80)

print(
    pairs.head(30).to_string(
        index=False
    )
)


print("\nSaved:")
print(OUTPUT)