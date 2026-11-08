"""Kiểm thử các hàm chuẩn hoá dữ liệu (Transform)."""
from datetime import date, datetime

import pytest

from app.etl.normalize import (
    map_outcome,
    map_source,
    map_stage,
    map_status,
    normalize_city,
    normalize_email,
    normalize_gender,
    normalize_name,
    normalize_phone,
    parse_datetime,
    parse_salary_million,
    parse_score,
    parse_years_experience,
)
from app.utils import normalize_key, strip_accents


@pytest.mark.parametrize("raw, expected", [
    ("0912 345 678", "0912345678"), ("+84 912345678", "0912345678"), ("0912.345.678", "0912345678"),
    (912345678, "0912345678"), ("84-912-345-678", "0912345678"), ("123", None), ("01234", None), (None, None),
])
def test_phone(raw, expected):
    assert normalize_phone(raw) == expected


def test_email_and_name():
    assert normalize_email("  AN.NGUYEN@GMAIL.COM ") == "an.nguyen@gmail.com"
    assert normalize_email("Nguyễn An <an@x.vn>") == "an@x.vn"
    assert normalize_email("khong co") is None
    assert normalize_name("  nguyễn   văn AN ") == "Nguyễn Văn An"
    assert strip_accents("Đặng Thị Ánh") == "Dang Thi Anh"
    assert normalize_key("Phỏng vấn – Vòng 2!") == "phong van vong 2"


def test_dates():
    assert parse_datetime("15/09/2026 10:22:13") == datetime(2026, 9, 15, 10, 22, 13)
    assert parse_datetime("2026-09-15") == datetime(2026, 9, 15)
    assert parse_datetime("2026-09-15T09:00:00+07:00") == datetime(2026, 9, 15, 9, 0)
    assert parse_datetime("2026-09-15T02:00:00Z") == datetime(2026, 9, 15, 9, 0)  # đổi sang giờ VN
    assert parse_datetime(46280.5) == datetime(2026, 9, 15, 12, 0)  # serial Excel
    assert parse_datetime("không rõ") is None


@pytest.mark.parametrize("raw, expected", [
    ("3 năm", 3.0), ("2,5", 2.5), ("1-2 năm", 1.5), ("Dưới 1 năm", 0.5), ("Chưa có kinh nghiệm", 0.0),
    ("Fresher", 0.0), ("Trên 5 năm", 5.0),
])
def test_years(raw, expected):
    assert parse_years_experience(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("15 triệu", 15.0), ("15tr", 15.0), ("15.000.000", 15.0), ("15-18 triệu", 16.5), ("Thỏa thuận", None),
    (18000000, 18.0),
])
def test_salary(raw, expected):
    assert parse_salary_million(raw) == expected


def test_reference_mappings():
    assert map_source("topcv.vn") == "TOPCV"
    assert map_source("Group Facebook tuyển dụng IT") == "FACEBOOK"
    assert map_source("Bạn bè/người quen giới thiệu") == "REFERRAL"
    assert map_source("Job fair ĐH Bách Khoa") == "JOB_FAIR"
    assert map_source("???") == "OTHER"
    assert map_stage("CV Screening") == "SCREENING"
    assert map_stage("PV kỹ thuật (online)") == "TECH_INTERVIEW"
    assert map_stage("Phỏng vấn vòng 1") == "HR_INTERVIEW"
    assert map_status("Không đạt") == "rejected"
    assert map_status("Rút hồ sơ") == "withdrawn"
    assert map_status("Đã nhận việc") == "hired"
    assert map_outcome("Từ chối") == "withdrawn"
    assert map_outcome("no_show") == "no_show"
    assert normalize_city("Sài Gòn") == "TP. Hồ Chí Minh"
    assert normalize_city("ha noi") == "Hà Nội"
    assert normalize_gender("female") == "Nữ"


def test_score():
    assert parse_score("4/5") == 4.0
    assert parse_score("8/10") == 4.0
    assert parse_score(3.5) == 3.5
    assert parse_score("80%") == 4.0


def test_position_resolver(client, db):
    from app.etl.load import PositionResolver

    resolver = PositionResolver(db)
    assert resolver.resolve("DA").code == "DA-2026"
    assert resolver.resolve("Data analyst (Junior)").code == "DA-2026"
    assert resolver.resolve("Backend Dev (Python)").code == "BE-2026"
    assert resolver.resolve("Front-end Dev").code == "FE-2026"
    assert resolver.resolve("QC/Tester").code == "QA-2026"
    assert resolver.resolve("Kỹ sư AI/ML").code == "AI-2026"
    assert resolver.resolve("Bảo vệ tòa nhà") is None
    assert date(2026, 1, 1)  # giữ import date
