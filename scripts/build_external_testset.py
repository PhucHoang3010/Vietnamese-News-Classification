from pathlib import Path

import pandas as pd
from datasets import load_dataset


# ============================================================
# CONFIG
# ============================================================

DATASET_NAME = "VLUS06/VietOnlineNews"

OUTPUT_DIR = Path("data/external")
OUTPUT_FILE = OUTPUT_DIR / "viet_online_news_test.csv"

SAMPLES_PER_CLASS = 500
RANDOM_STATE = 42


# ============================================================
# CATEGORY MAPPING
# ============================================================

CATEGORY_MAPPING = {
    "Giải trí": "Giải trí",
    "Kinh doanh": "Kinh doanh",
    "Thể thao": "Thể thao",
    "Thời sự": "Thời sự",
    "Giáo dục": "Giáo dục",
    "Khoa học công nghệ": "Khoa học",
    "Đời sống": "Đời sống",
    "Xe": "Xe",
    "Sức khỏe": "Sức khỏe",
    "Thế giới": "Thế giới",
    "Pháp luật": "Pháp luật",
}


# ============================================================
# LOAD
# ============================================================

print("=" * 80)
print("BUILD EXTERNAL TEST SET")
print("=" * 80)

print("\nLoading VietOnlineNews...")

dataset = load_dataset(
    DATASET_NAME,
    split="train",
)

print(f"Total rows loaded: {len(dataset):,}")


# ============================================================
# DATAFRAME
# ============================================================

df = dataset.to_pandas()

required_columns = [
    "title",
    "description",
    "content",
    "category",
]

missing = [
    col for col in required_columns
    if col not in df.columns
]

if missing:
    raise RuntimeError(
        f"Missing required columns: {missing}"
    )


# ============================================================
# CLEAN TEXT
# ============================================================

df["title"] = df["title"].fillna("").astype(str)
df["description"] = df["description"].fillna("").astype(str)
df["content"] = df["content"].fillna("").astype(str)
df["category"] = df["category"].fillna("").astype(str)

# Title + description + content
df["text"] = (
    df["title"]
    + "\n"
    + df["description"]
    + "\n"
    + df["content"]
)

df["text"] = df["text"].str.strip()

# Remove empty articles
df = df[df["text"].str.len() >= 30].copy()


# ============================================================
# FILTER VALID CATEGORIES
# ============================================================

df = df[
    df["category"].isin(CATEGORY_MAPPING.keys())
].copy()

print("\nCategories used for evaluation:")

for category in CATEGORY_MAPPING:
    count = (df["category"] == category).sum()
    print(f"{category:<30} {count:>8,}")


# ============================================================
# STRATIFIED SAMPLE
# ============================================================

samples = []

for source_category, target_category in CATEGORY_MAPPING.items():

    group = df[
        df["category"] == source_category
    ].copy()

    available = len(group)

    sample_size = min(
        SAMPLES_PER_CLASS,
        available,
    )

    sampled = group.sample(
        n=sample_size,
        random_state=RANDOM_STATE,
    ).copy()

    sampled["ground_truth"] = target_category
    sampled["source_category"] = source_category

    samples.append(sampled)


test_df = pd.concat(
    samples,
    ignore_index=True,
)

# Shuffle final test set
test_df = test_df.sample(
    frac=1.0,
    random_state=RANDOM_STATE,
).reset_index(drop=True)


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

output_columns = [
    "id",
    "title",
    "description",
    "content",
    "text",
    "source_category",
    "ground_truth",
]

test_df[output_columns].to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 80)
print("TEST SET CREATED")
print("=" * 80)

print(f"Output : {OUTPUT_FILE}")
print(f"Rows   : {len(test_df):,}")

print("\nGROUND TRUTH DISTRIBUTION")

print(
    test_df["ground_truth"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nDone.")