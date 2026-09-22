# ML Evaluation Report

## Production model

| Item | Value |
|---|---|
| Model | Linear SVM — Balanced |
| Class weight | balanced |
| Validation Accuracy | 0.8501 |
| Validation Macro-F1 | 0.7136 |
| Test samples | 487 |
| Test Accuracy | 0.8070 |
| Test Macro-F1 | 0.6871 |
| Test Weighted-F1 | 0.8004 |

## Why Macro-F1 is reported

The dataset contains multiple news categories. Macro-F1 gives each class equal weight, so it exposes weak performance on smaller or harder categories that can be hidden by aggregate accuracy.

## Per-class test analysis

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Đời sống | 0.294 | 0.238 | 0.263 | 21 |
| Thế giới | 0.625 | 0.312 | 0.417 | 16 |
| Công đoàn | 0.500 | 0.500 | 0.500 | 6 |
| Xã hội | 0.500 | 0.500 | 0.500 | 6 |
| Thời sự | 0.667 | 0.462 | 0.545 | 26 |
| Pháp luật | 0.655 | 0.864 | 0.745 | 22 |
| Xe | 0.600 | 1.000 | 0.750 | 3 |
| Giải trí | 0.750 | 0.800 | 0.774 | 15 |
| Khoa học | 0.727 | 0.935 | 0.818 | 77 |
| Sức khỏe | 0.833 | 0.893 | 0.862 | 28 |
| Kinh doanh | 0.939 | 0.831 | 0.882 | 166 |
| Giáo dục | 0.902 | 0.937 | 0.919 | 79 |
| Thể thao | 0.917 | 1.000 | 0.957 | 22 |

## Error analysis

The table below contains the most frequent off-diagonal confusion pairs from the locked test confusion matrix.

| Count | True class | Predicted class |
|---:|---|---|
| 14 | Kinh doanh | Khoa học |
| 4 | Đời sống | Pháp luật |
| 4 | Đời sống | Khoa học |
| 3 | Thời sự | Pháp luật |
| 3 | Thời sự | Khoa học |
| 3 | Thế giới | Sức khỏe |
| 3 | Thế giới | Khoa học |
| 3 | Kinh doanh | Đời sống |
| 3 | Kinh doanh | Công đoàn |
| 2 | Đời sống | Thời sự |
| 2 | Đời sống | Kinh doanh |
| 2 | Đời sống | Giải trí |
| 2 | Thời sự | Đời sống |
| 2 | Thời sự | Xã hội |
| 2 | Thời sự | Kinh doanh |

## Ablation study

| Stage | Change | Macro-F1 |
|---|---|---:|
| E0 | Raw baseline | 0.7062 |
| E1 | + Underthesea | 0.7129 |
| E2 | + Vietnamese stopwords | 0.7107 |
| E3 | + TF-IDF tuning | 0.7232 |
| E4 | + Classifier tuning | 0.7381 |
| E5 | Final configuration | 0.7381 |

## Generalization

Internal test and external test should be discussed separately because they measure different data distributions. Do not tune the frozen production model on the external set.

## Release rule

**Do not modify the production model or preprocessing contract as part of this report generation.** The scripts only read the frozen artifacts and evaluation metadata.
