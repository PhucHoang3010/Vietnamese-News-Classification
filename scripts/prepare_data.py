"""
prepare_data.py
===============
PHASE 1 — Data Preparation Pipeline

Mục đích:
- Load raw CSV
- Validate schema
- Basic cleaning (không học tham số từ dataset)
- Deduplication (URL optional, clean_text bắt buộc)
- Stratified split 70/15/15
- Export train/validation/test + metadata

KHÔNG làm ở Phase 1:
- Tokenizer
- TF-IDF fit
- Model training
- Calibration
- UNKNOWN threshold

Usage:
    python scripts/prepare_data.py
    python scripts/prepare_data.py --input data/raw/news_raw.csv --dataset-version v1.0.0
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup
from sklearn.model_selection import train_test_split

# ============================================================
# CONFIG
# ============================================================

RANDOM_SEED = 42
DEFAULT_TEST_SIZE = 0.15
DEFAULT_VAL_SIZE = 0.15
DEFAULT_DATASET_VERSION = "v1.0.0"

# Mapping từ tên cột dataset gốc → schema chuẩn.
# KHÔNG auto-detect. Phải khai báo rõ ràng.
#
# Ví dụ khi dùng dataset thật có cột khác:
# FIELD_MAPPING = {
#     "category": "label",
#     "body": "content",
#     "headline": "title",
# }
FIELD_MAPPING: dict[str, str] = {}
# UVN-1 đã được chuẩn hóa schema bởi download_uvn1.py
# Không cần mapping thêm.

REQUIRED_COLUMNS = ["id", "title", "content", "label"]
OPTIONAL_COLUMNS = ["url"]

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================
# TEXT CLEANING (deterministic, không học tham số)
# ============================================================

def strip_html(text: str) -> str:
    """Loại bỏ HTML, script, style bằng BeautifulSoup."""
    if not isinstance(text, str) or not text:
        return ""
    soup = BeautifulSoup(text, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator=" ")


def normalize_unicode(text: str) -> str:
    """Chuẩn hóa Unicode về NFC (giữ nguyên dấu tiếng Việt)."""
    if not isinstance(text, str):
        return ""
    return unicodedata.normalize("NFC", text)


def remove_control_chars(text: str) -> str:
    """Loại bỏ control characters, giữ emoji và ký tự Unicode hợp lệ."""
    if not isinstance(text, str):
        return ""
    return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)


def normalize_whitespace(text: str) -> str:
    """Chuẩn hóa whitespace: gộp nhiều space/newline thành 1 space."""
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", text).strip()


def clean_text_pipeline(text: str) -> str:
    """
    Pipeline cleaning cơ bản, KHÔNG học tham số từ dataset.

    Thứ tự:
    1. Unicode NFC
    2. HTML strip (script/style removed)
    3. Control character removal
    4. Whitespace normalization
    """
    if not isinstance(text, str):
        return ""
    text = normalize_unicode(text)
    text = strip_html(text)
    text = remove_control_chars(text)
    text = normalize_whitespace(text)
    return text


# ============================================================
# SCHEMA VALIDATION
# ============================================================

def apply_field_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """Rename cột theo FIELD_MAPPING, log rõ ràng."""
    if not FIELD_MAPPING:
        logger.info("FIELD_MAPPING is empty — using dataset columns as-is.")
        return df

    logger.info("Applying FIELD_MAPPING:")
    rename_map: dict[str, str] = {}
    for src, dst in FIELD_MAPPING.items():
        if src in df.columns:
            rename_map[src] = dst
            logger.info(f"   {src} → {dst}")
        else:
            logger.warning(f"   Field '{src}' not found in dataset, skipping.")

    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def validate_schema(df: pd.DataFrame) -> None:
    """Kiểm tra schema tối thiểu."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}. "
            f"Please update FIELD_MAPPING in prepare_data.py."
        )
    logger.info(f"✅ Schema validated. Required columns present: {REQUIRED_COLUMNS}")

    has_url = "url" in df.columns
    logger.info(f"URL column present: {has_url}")


# ============================================================
# CLEANING
# ============================================================

def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Xử lý missing title/content, drop missing label."""
    n_before = len(df)

    df = df.dropna(subset=["label"]).copy()
    n_dropped_label = n_before - len(df)
    if n_dropped_label > 0:
        logger.warning(f"Dropped {n_dropped_label} rows with missing label.")

    for col in ["title", "content"]:
        n_missing = df[col].isna().sum()
        if n_missing > 0:
            logger.warning(
                f"Filling {n_missing} missing values in '{col}' with empty string."
            )
        df[col] = df[col].fillna("").astype(str)

    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply cleaning pipeline lên title và content."""
    logger.info("Cleaning title and content...")
    df = df.copy()
    df["title"] = df["title"].apply(clean_text_pipeline)
    df["content"] = df["content"].apply(clean_text_pipeline)

    df["text"] = (df["title"] + " " + df["content"]).str.strip()
    df["clean_text"] = df["text"]

    return df


# ============================================================
# DEDUPLICATION (URL optional)
# ============================================================

def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate theo:
    1. URL nếu URL tồn tại
    2. clean_text

    URL là optional:
    - Có URL     → dedup URL
    - Không URL  → KHÔNG được drop record

    Giữ bản ghi đầu tiên.
    """
    df = df.copy()

    # --------------------------------------------------------
    # 1. URL dedup — chỉ áp dụng cho record có URL
    # --------------------------------------------------------
    if "url" in df.columns:
        url_values = df["url"].fillna("").astype(str).str.strip()
        has_url = url_values.ne("")

        with_url = df.loc[has_url].copy()
        without_url = df.loc[~has_url].copy()

        before_url = len(with_url)

        if not with_url.empty:
            with_url = with_url.drop_duplicates(
                subset=["url"],
                keep="first",
            )

        url_duplicates_removed = before_url - len(with_url)

        logger.info(
            f"URL dedup: removed {url_duplicates_removed} duplicates "
            f"(kept {len(without_url)} records without URL)."
        )

        df = pd.concat(
            [with_url, without_url],
            ignore_index=True,
        )

    # --------------------------------------------------------
    # 2. clean_text dedup
    # --------------------------------------------------------
    before_text = len(df)

    df = df.drop_duplicates(
        subset=["clean_text"],
        keep="first",
    )

    text_duplicates_removed = before_text - len(df)

    logger.info(
        f"clean_text dedup: removed {text_duplicates_removed} duplicates."
    )

    # --------------------------------------------------------
    # 3. Reset index
    # --------------------------------------------------------
    df = df.reset_index(drop=True)

    logger.info(
        f"Deduplication completed: {len(df)} unique records remaining."
    )

    return df


# ============================================================
# SPLIT
# ============================================================

def check_class_min_samples(df: pd.DataFrame, min_required: int = 3) -> None:
    """Raise error nếu class có < min_required mẫu."""
    counts = df["label"].value_counts()
    bad = counts[counts < min_required]
    if not bad.empty:
        bad_list = ", ".join(f"'{k}' ({v})" for k, v in bad.items())
        raise ValueError(
            f"Class with insufficient samples for stratified split: {bad_list}. "
            f"Each class must have >= {min_required} samples. "
            f"Please fix the dataset before continuing."
        )
    logger.info(
        f"✅ Class validation passed. All classes have >= {min_required} samples."
    )


def stratified_split(
    df: pd.DataFrame,
    test_size: float,
    val_size: float,
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Stratified 70/15/15 split bằng 2 lần train_test_split."""
    train_df, temp_df = train_test_split(
        df,
        test_size=(test_size + val_size),
        stratify=df["label"],
        random_state=random_state,
    )

    relative_test_size = test_size / (test_size + val_size)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=relative_test_size,
        stratify=temp_df["label"],
        random_state=random_state,
    )

    return (
        train_df.reset_index(drop=True),
        val_df.reset_index(drop=True),
        test_df.reset_index(drop=True),
    )


# ============================================================
# EXPORT
# ============================================================

def export_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: Path,
    encoding: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(output_dir / "train.csv", index=False, encoding=encoding)
    val_df.to_csv(output_dir / "validation.csv", index=False, encoding=encoding)
    test_df.to_csv(output_dir / "test.csv", index=False, encoding=encoding)
    logger.info(f"✅ Exported train/validation/test to {output_dir}")


def export_interim(df: pd.DataFrame, interim_dir: Path, encoding: str) -> None:
    interim_dir.mkdir(parents=True, exist_ok=True)
    path = interim_dir / "news_clean.csv"
    df.to_csv(path, index=False, encoding=encoding)
    logger.info(f"✅ Exported interim clean dataset to {path}")


def export_categories(
    df: pd.DataFrame,
    output_dir: Path,
    dataset_version: str,
) -> list[str]:
    categories = sorted(df["label"].unique().tolist())
    payload = {
        "dataset_version": dataset_version,
        "categories": categories,
        "num_classes": len(categories),
        "label_column": "label",
    }
    path = output_dir / "categories.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ Exported categories.json ({len(categories)} classes)")
    return categories


def export_metadata(
    original_df: pd.DataFrame,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    categories: list[str],
    output_dir: Path,
    dataset_version: str,
    random_state: int,
    test_size: float,
    val_size: float,
) -> None:
    payload: dict[str, Any] = {
        "dataset_version": dataset_version,
        "source": None,      # TODO: cập nhật khi dùng dataset thật
        "license": None,     # TODO: cập nhật khi dùng dataset thật
        "format": "csv",
        "total_samples": int(len(train_df) + len(val_df) + len(test_df)),
        "original_samples": int(len(original_df)),
        "num_classes": len(categories),
        "categories": categories,
        "columns": {
            "input": ["id", "title", "content", "label"],
            "optional": ["url"],
            "generated": ["text", "clean_text"],
        },
        "split": {
            "train": int(len(train_df)),
            "validation": int(len(val_df)),
            "test": int(len(test_df)),
            "test_size": test_size,
            "val_size": val_size,
            "random_state": random_state,
        },
        "preprocessing": {
            "unicode_normalization": "NFC",
            "html_strip": True,
            "remove_script_style": True,
            "control_char_removal": True,
            "whitespace_normalization": True,
            "teencode_normalization": False,
        },
        "tokenizer": {
            "name": None,     # Phase 2 sẽ điền: underthesea
            "version": None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    path = output_dir / "dataset_metadata.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info("✅ Exported dataset_metadata.json")


# ============================================================
# SUMMARY
# ============================================================

def print_summary(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    categories: list[str],
) -> None:
    logger.info("=" * 60)
    logger.info("DATASET SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total samples : {len(train_df) + len(val_df) + len(test_df)}")
    logger.info(f"Classes       : {len(categories)} → {categories}")
    logger.info(f"Train         : {len(train_df)}")
    logger.info(f"Validation    : {len(val_df)}")
    logger.info(f"Test          : {len(test_df)}")
    logger.info("-" * 60)
    logger.info("Class distribution (Train / Val / Test):")
    train_counts = train_df["label"].value_counts().sort_index()
    val_counts = val_df["label"].value_counts().sort_index()
    test_counts = test_df["label"].value_counts().sort_index()
    for cat in categories:
        logger.info(
            f"   {cat:15s} : {train_counts.get(cat, 0):4d} / "
            f"{val_counts.get(cat, 0):4d} / {test_counts.get(cat, 0):4d}"
        )
    logger.info("=" * 60)


# ============================================================
# MAIN
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 1 — Data Preparation Pipeline",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/news_raw.csv"),
        help="Input raw CSV path.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Output directory for train/validation/test.",
    )
    parser.add_argument(
        "--interim-dir",
        type=Path,
        default=Path("data/interim"),
        help="Directory for interim cleaned dataset.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=RANDOM_SEED,
        help=f"Random seed (default: {RANDOM_SEED}).",
    )
    parser.add_argument(
        "--dataset-version",
        type=str,
        default=DEFAULT_DATASET_VERSION,
        help=f"Dataset version (default: {DEFAULT_DATASET_VERSION}).",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=DEFAULT_TEST_SIZE,
        help=f"Test split ratio (default: {DEFAULT_TEST_SIZE}).",
    )
    parser.add_argument(
        "--val-size",
        type=float,
        default=DEFAULT_VAL_SIZE,
        help=f"Validation split ratio (default: {DEFAULT_VAL_SIZE}).",
    )
    parser.add_argument(
        "--encoding",
        type=str,
        default="utf-8-sig",
        help="CSV encoding (default: utf-8-sig).",
    )
    return parser.parse_args()


def validate_split_arguments(test_size: float, val_size: float) -> None:
    """Validate train/validation/test ratios."""
    if not 0 < test_size < 1:
        raise ValueError(f"--test-size must be between 0 and 1. Got: {test_size}")
    if not 0 < val_size < 1:
        raise ValueError(f"--val-size must be between 0 and 1. Got: {val_size}")
    if test_size + val_size >= 1:
        raise ValueError(
            f"test_size + val_size must be < 1. Got {test_size + val_size}"
        )


def load_dataset(input_path: Path, encoding: str) -> pd.DataFrame:
    """Load raw CSV dataset."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_path}")
    logger.info(f"Loading dataset: {input_path}")
    df = pd.read_csv(input_path, encoding=encoding)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns.")
    return df


def main() -> None:
    args = parse_args()

    project_root = Path(__file__).resolve().parent.parent

    input_path = (
        args.input if args.input.is_absolute() else project_root / args.input
    )
    output_dir = (
        args.output_dir
        if args.output_dir.is_absolute()
        else project_root / args.output_dir
    )
    interim_dir = (
        args.interim_dir
        if args.interim_dir.is_absolute()
        else project_root / args.interim_dir
    )

    logger.info("=" * 70)
    logger.info("P2 — VIETNAMESE NEWS CLASSIFICATION")
    logger.info("PHASE 1 — DATA PREPARATION")
    logger.info("=" * 70)
    logger.info(f"Input             : {input_path}")
    logger.info(f"Output directory  : {output_dir}")
    logger.info(f"Interim directory : {interim_dir}")
    logger.info(f"Dataset version   : {args.dataset_version}")
    logger.info(f"Random state      : {args.random_state}")
    logger.info(f"Validation size   : {args.val_size}")
    logger.info(f"Test size         : {args.test_size}")
    logger.info(f"Encoding          : {args.encoding}")

    # 1. Validate split config
    validate_split_arguments(test_size=args.test_size, val_size=args.val_size)

    # 2. Load
    df = load_dataset(input_path=input_path, encoding=args.encoding)
    original_df = df.copy()

    # 3. Field mapping
    df = apply_field_mapping(df)

    # 4. Schema validation
    validate_schema(df)

    # 5. Missing values
    df = handle_missing(df)

    # 6. Cleaning
    df = clean_dataframe(df)

    # 7. Drop empty text
    empty_text_mask = df["clean_text"].str.strip().eq("")
    empty_count = int(empty_text_mask.sum())
    if empty_count > 0:
        logger.warning(f"Dropping {empty_count} rows with empty clean_text.")
        df = df.loc[~empty_text_mask].copy()

    # 8. Dedup
    df = deduplicate(df)

    # 9. Class validation
    check_class_min_samples(df, min_required=3)

    # 10. Export interim
    export_interim(df=df, interim_dir=interim_dir, encoding=args.encoding)

    # 11. Stratified split
    train_df, val_df, test_df = stratified_split(
        df=df,
        test_size=args.test_size,
        val_size=args.val_size,
        random_state=args.random_state,
    )

    # 12. Export splits
    export_splits(
        train_df=train_df,
        val_df=val_df,
        test_df=test_df,
        output_dir=output_dir,
        encoding=args.encoding,
    )

    # 13. Categories
    categories = export_categories(
        df=df,
        output_dir=output_dir,
        dataset_version=args.dataset_version,
    )

    # 14. Metadata
    export_metadata(
        original_df=original_df,
        train_df=train_df,
        val_df=val_df,
        test_df=test_df,
        categories=categories,
        output_dir=output_dir,
        dataset_version=args.dataset_version,
        random_state=args.random_state,
        test_size=args.test_size,
        val_size=args.val_size,
    )

    # 15. Summary
    print_summary(
        train_df=train_df,
        val_df=val_df,
        test_df=test_df,
        categories=categories,
    )

    logger.info("✅ PHASE 1 DATA PREPARATION COMPLETED")
    logger.info("⚠️  No tokenizer, TF-IDF or model training was performed.")


if __name__ == "__main__":
    main()