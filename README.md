# P2 — Vietnamese News Classification & Trend Analytics Platform

> **Phase 1** — Data Preparation & Dataset Pipeline

## ⚠️ Trạng thái

-  Phase 1: Data preparation
-  Phase 2: Preprocessing + Tokenization + TF-IDF 
-  Phase 3+: ML + Backend + Crawler + Frontend 

**Lưu ý**: Dataset hiện tại là **SYNTHETIC**, chỉ dùng để test pipeline. Dataset chính thức sẽ được chọn sau khi Phase 1 synthetic PASS.

## 🚀 Quick Start

### 1. Tạo môi trường

**Windows PowerShell:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Cài dependencies

```bash
pip install -r requirements.txt
```

### 3. Sinh synthetic dataset

```bash
python scripts/generate_synthetic_data.py
```

Kỳ vọng: `data/raw/news_raw.csv` với 300 samples, 5 classes.

### 4. Chạy data preparation

```bash
python scripts/prepare_data.py
```

Kỳ vọng:
- `data/interim/news_clean.csv`
- `data/processed/train.csv` (210)
- `data/processed/validation.csv` (45)
- `data/processed/test.csv` (45)
- `data/processed/categories.json`
- `data/processed/dataset_metadata.json`

### 5. Chạy EDA

```bash
jupyter notebook notebooks/01_eda.ipynb
```

### 6. Chạy tests

```bash
pytest tests/ -v
```

## 📁 Project Structure

```
P2-vietnamese-news-classifier/
├── backend/
│   ├── __init__.py
│   └── app/
│       ├── __init__.py
│       └── services/
│           └── __init__.py
├── scripts/
│   ├── __init__.py
│   ├── generate_synthetic_data.py
│   └── prepare_data.py
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── notebooks/
│   └── 01_eda.ipynb
├── tests/
│   ├── __init__.py
│   └── test_prepare_data.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## ⚠️ Data Leakage Rules

- ❌ KHÔNG fit TF-IDF trên toàn dataset
- ❌ KHÔNG build vocabulary trước split
- ❌ KHÔNG dùng statistics toàn dataset để tạo feature
- ✅ CHỈ fit TF-IDF trên TRAIN (Phase 2)
- ✅ Test set LOCKED cho đến final evaluation

## 🎯 Phase 1 Scope

**ĐƯỢC làm:**
- Load + validate schema
- Basic cleaning (NFC, HTML strip, whitespace)
- Dedup (URL optional, clean_text bắt buộc)
- Stratified 70/15/15
- Export dataset + metadata

**KHÔNG được làm:**
- ❌ Tokenizer
- ❌ TF-IDF
- ❌ Model training
- ❌ Calibration
- ❌ FastAPI / PostgreSQL / Crawler / Frontend
