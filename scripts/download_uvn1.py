"""
download_uvn1.py
================
PHASE 1.5 — UVN-1 Dataset Ingestion

Mục đích:
- Tải dataset UVN-1 từ HuggingFace (undertheseanlp/UVN-1)
- Normalize schema về format chuẩn của P2
- Export ra data/raw/uvn1_news.csv

TRÁCH NHIỆM DUY NHẤT: Dataset ingestion
KHÔNG làm: cleaning, dedup, split, tokenization, TF-IDF, training.

Output schema: id, title, content, label, url
Dataset contract: 10 categories (raise error nếu khác).
License: CC-BY-NC-4.0 (research/educational use only).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)

# ============================================================
# CONFIG
# ============================================================

HF_DATASET_ID = "undertheseanlp/UVN-1"
HF_SPLIT = "train"

DEFAULT_OUTPUT = Path("data/raw/uvn1_news.csv")
DEFAULT_DATASET_VERSION = "uvn1-v1.0.0"

EXPECTED_NUM_CATEGORIES = 13
EXPECTED_CATEGORIES = {
    "Công đoàn",
    "Giáo dục",
    "Giải trí",
    "Khoa học",
    "Kinh doanh",
    "Pháp luật",
    "Sức khỏe",
    "Thế giới",
    "Thể thao",
    "Thời sự",
    "Xe",
    "Xã hội",
    "Đời sống",
}

OUTPUT_COLUMNS = ["id", "title", "content", "label", "url"]
FIELD_MAPPING = {"category": "label"}


# ============================================================
# VALIDATION
# ============================================================

def validate_input_schema(df) -> None:
    required = ["id", "title", "content", "category", "url"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"UVN-1 schema thay đổi — thiếu cột: {missing}. "
            f"Cột hiện có: {list(df.columns)}"
        )
    logger.info(f"✅ Input schema OK: {list(df.columns)}")


def validate_dataset_contract(df) -> None:
    actual = set(df["label"].dropna().unique().tolist())
    actual_count = len(actual)

    logger.info("-" * 60)
    logger.info("DATASET CONTRACT VALIDATION")
    logger.info(f"  Expected: {EXPECTED_NUM_CATEGORIES}")
    logger.info(f"  Actual  : {actual_count}")

    if actual_count != EXPECTED_NUM_CATEGORIES:
        raise ValueError(
            f"UVN-1 contract violation: expected "
            f"{EXPECTED_NUM_CATEGORIES} categories, got {actual_count}. "
            f"Found: {sorted(actual)}"
        )

    if actual != EXPECTED_CATEGORIES:
        extra = actual - EXPECTED_CATEGORIES
        missing = EXPECTED_CATEGORIES - actual
        raise ValueError(
            f"UVN-1 contract violation:\n"
            f"  Missing: {sorted(missing) if missing else 'none'}\n"
            f"  Extra  : {sorted(extra) if extra else 'none'}"
        )

    logger.info("  ✅ Categories khớp contract")


# ============================================================
# DOWNLOAD + CONVERT
# ============================================================

def download_and_convert(output_path: Path) -> None:
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError(
            "Thư viện 'datasets' chưa cài. Chạy:\n"
            "    pip install datasets"
        )

    logger.info("=" * 60)
    logger.info("UVN-1 DATASET INGESTION")
    logger.info("=" * 60)
    logger.info(f"HF Dataset ID : {HF_DATASET_ID}")
    logger.info(f"HF Split      : {HF_SPLIT}")
    logger.info(f"Output        : {output_path}")
    logger.info("=" * 60)

    logger.info("Đang tải UVN-1 từ HuggingFace...")
    dataset = load_dataset(HF_DATASET_ID)

    if HF_SPLIT not in dataset:
        raise ValueError(
            f"Split '{HF_SPLIT}' không tồn tại. "
            f"Splits: {list(dataset.keys())}"
        )

    split_data = dataset[HF_SPLIT]
    logger.info(f"✅ Loaded split '{HF_SPLIT}': {len(split_data)} articles")

    df = split_data.to_pandas()
    logger.info(f"Columns gốc: {list(df.columns)}")

    validate_input_schema(df)

    df = df.rename(columns=FIELD_MAPPING)
    logger.info(f"Đã rename: {FIELD_MAPPING}")

    validate_dataset_contract(df)

    df = df[OUTPUT_COLUMNS].copy()
    logger.info(f"Columns output: {list(df.columns)}")

    logger.info("-" * 60)
    logger.info("Category distribution:")
    for cat, count in df["label"].value_counts().sort_index().items():
        logger.info(f"   - {cat}: {count}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    logger.info("-" * 60)
    logger.info(f"✅ Đã lưu: {output_path}")
    logger.info(f"✅ Tổng số bài báo: {len(df)}")
    logger.info(f"✅ Số categories: {df['label'].nunique()}")
    logger.info("=" * 60)
    logger.info("BƯỚC TIẾP THEO:")
    logger.info(
        f"  python scripts/prepare_data.py "
        f"--input {output_path} --dataset-version uvn1-v1.0.0"
    )
    logger.info("=" * 60)


# ============================================================
# MAIN
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download UVN-1 và normalize schema.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--dataset-version",
        type=str,
        default=DEFAULT_DATASET_VERSION,
        help=f"Dataset version (default: {DEFAULT_DATASET_VERSION})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parent.parent
    output_path = (
        args.output if args.output.is_absolute() else project_root / args.output
    )
    logger.info(f"Dataset version: {args.dataset_version}")
    download_and_convert(output_path)


if __name__ == "__main__":
    main()