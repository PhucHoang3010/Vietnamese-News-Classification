# Vietnamese News Classification & Trend Analytics Platform

> **P2 — Vietnamese News Classification & Trend Analytics Platform**  
> Automated Vietnamese news collection, NLP classification, storage and trend analytics dashboard.

## 1. Overview

Vietnamese News Classification & Trend Analytics Platform is an end-to-end data and machine learning system for:

- Collecting Vietnamese news articles from RSS feeds.
- Fetching full article content from source websites.
- Cleaning and preprocessing Vietnamese text.
- Classifying news into predefined categories using Machine Learning.
- Storing classified news in PostgreSQL.
- Analyzing category distribution and daily trends.
- Monitoring crawler and data quality.
- Providing an interactive analytics dashboard.

### Current pipeline

```text
RSS Feed
   │
   ▼
RSS Parser
   │
   ▼
URL / Content Deduplication
   │
   ▼
Article Fetcher
   │
   ├── Full Article Content
   │
   └── RSS Fallback
   │
   ▼
Vietnamese Text Preprocessing
   │
   ▼
TF-IDF Vectorization
   │
   ▼
LinearSVC Classifier
   │
   ▼
PostgreSQL
   │
   ▼
Analytics API
   │
   ▼
React + Vite Dashboard