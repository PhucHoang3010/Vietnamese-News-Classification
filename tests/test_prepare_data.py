"""
test_prepare_data.py
====================
PHASE 1 — Unit tests cho prepare_data.py

Chạy:
    pytest tests/ -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

# Thêm project root vào sys.path để import scripts
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.prepare_data import (  # noqa: E402
    check_class_min_samples,
    clean_text_pipeline,
    deduplicate,
    stratified_split,
    validate_schema,
    validate_split_arguments,
)


# ============================================================
# TEST — clean_text_pipeline
# ============================================================

def test_clean_text_pipeline_removes_html():
    raw = "<p>Đây là <b>tin tức</b></p><script>alert('x')</script>"
    result = clean_text_pipeline(raw)
    assert "<p>" not in result
    assert "<b>" not in result
    assert "alert" not in result
    assert "tin tức" in result


def test_clean_text_pipeline_removes_script_style():
    raw = "<style>body{color:red}</style>Nội dung chính"
    result = clean_text_pipeline(raw)
    assert "color" not in result
    assert "Nội dung chính" in result


def test_clean_text_pipeline_normalizes_whitespace():
    raw = "Đây    là\n\n\ntin   tức"
    result = clean_text_pipeline(raw)
    assert result == "Đây là tin tức"


def test_clean_text_pipeline_preserves_vietnamese_accents():
    raw = "Đội tuyển Việt Nam giành chiến thắng"
    result = clean_text_pipeline(raw)
    assert "Đội tuyển" in result
    assert "chiến thắng" in result


def test_clean_text_pipeline_preserves_emoji():
    raw = "Tin vui hôm nay 😀🎉"
    result = clean_text_pipeline(raw)
    assert "😀" in result
    assert "🎉" in result


def test_clean_text_pipeline_handles_non_string():
    assert clean_text_pipeline(None) == ""
    assert clean_text_pipeline(123) == ""


# ============================================================
# TEST — validate_schema
# ============================================================

def test_validate_schema_passes_with_all_required():
    df = pd.DataFrame({
        "id": ["1"],
        "title": ["t"],
        "content": ["c"],
        "label": ["L"],
    })
    validate_schema(df)  # không raise


def test_validate_schema_raises_when_missing():
    df = pd.DataFrame({"id": ["1"], "title": ["t"]})
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_schema(df)


# ============================================================
# TEST — deduplicate
# ============================================================

def test_deduplicate_by_clean_text():
    df = pd.DataFrame({
        "id": ["1", "2", "3"],
        "title": ["a", "a", "b"],
        "content": ["x", "x", "y"],
        "label": ["A", "A", "B"],
        "clean_text": ["a x", "a x", "b y"],
    })
    result = deduplicate(df)
    assert len(result) == 2


def test_deduplicate_keeps_first():
    df = pd.DataFrame({
        "id": ["1", "2"],
        "title": ["a", "a"],
        "content": ["x", "x"],
        "label": ["A", "A"],
        "clean_text": ["same", "same"],
    })
    result = deduplicate(df)
    assert result.iloc[0]["id"] == "1"


def test_deduplicate_url_optional_keeps_no_url_records():
    """Record không có URL vẫn được giữ."""
    df = pd.DataFrame({
        "id": ["1", "2", "3", "4"],
        "title": ["a", "a", "b", "c"],
        "content": ["x", "y", "z", "w"],
        "label": ["A", "A", "B", "C"],
        "url": ["http://a", "http://a", "", ""],
        "clean_text": ["a x", "a y", "b z", "c w"],
    })
    result = deduplicate(df)
    # 1 URL dup bị drop, 2 record không URL vẫn giữ
    assert len(result) == 3


# ============================================================
# TEST — check_class_min_samples
# ============================================================

def test_check_class_min_samples_passes():
    df = pd.DataFrame({"label": ["A"] * 5 + ["B"] * 5})
    check_class_min_samples(df, min_required=3)  # không raise


def test_check_class_min_samples_raises():
    df = pd.DataFrame({"label": ["A"] * 2 + ["B"] * 10})
    with pytest.raises(ValueError, match="insufficient samples"):
        check_class_min_samples(df, min_required=3)


# ============================================================
# TEST — stratified_split
# ============================================================

def test_stratified_split_ratio():
    df = pd.DataFrame({
        "label": ["A"] * 100 + ["B"] * 100,
    })
    train_df, val_df, test_df = stratified_split(
        df, test_size=0.15, val_size=0.15, random_state=42
    )
    total = len(train_df) + len(val_df) + len(test_df)
    assert total == 200
    assert len(train_df) == 140
    assert len(val_df) == 30
    assert len(test_df) == 30


def test_stratified_split_preserves_class_ratio():
    df = pd.DataFrame({
        "label": ["A"] * 100 + ["B"] * 100,
    })
    train_df, val_df, test_df = stratified_split(
        df, test_size=0.15, val_size=0.15, random_state=42
    )
    for split_df in [train_df, val_df, test_df]:
        ratio_a = (split_df["label"] == "A").mean()
        assert 0.45 <= ratio_a <= 0.55  # xấp xỉ 50/50


# ============================================================
# TEST — validate_split_arguments
# ============================================================

def test_validate_split_arguments_ok():
    validate_split_arguments(test_size=0.15, val_size=0.15)


def test_validate_split_arguments_bad_test_size():
    with pytest.raises(ValueError, match="--test-size"):
        validate_split_arguments(test_size=1.5, val_size=0.15)


def test_validate_split_arguments_bad_val_size():
    with pytest.raises(ValueError, match="--val-size"):
        validate_split_arguments(test_size=0.15, val_size=-0.1)


def test_validate_split_arguments_sum_too_large():
    with pytest.raises(ValueError, match="test_size \\+ val_size"):
        validate_split_arguments(test_size=0.6, val_size=0.6)