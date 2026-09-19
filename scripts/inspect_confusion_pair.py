from pathlib import Path
import pandas as pd


INPUT = Path(
    "reports/external/external_predictions.csv"
)

OUTPUT = Path(
    "reports/external/"
    "confusion_khoahoc_kinhdoanh.csv"
)


df = pd.read_csv(
    INPUT,
    encoding="utf-8-sig",
)


subset = df[
    (df["ground_truth"] == "Khoa học")
    & (df["prediction"] == "Kinh doanh")
].copy()


subset = subset.sort_values(
    "margin"
)


columns = [
    "id",
    "title",
    "source_category",
    "ground_truth",
    "prediction",
    "correct",
    "margin",
]


subset[columns].to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8-sig",
)


print("=" * 80)
print("KHOA HỌC → KINH DOANH")
print("=" * 80)

print(
    f"Total: {len(subset)}"
)

print("\nLowest-margin examples:\n")

print(
    subset[columns]
    .head(20)
    .to_string(index=False)
)

print("\nSaved:")
print(OUTPUT)