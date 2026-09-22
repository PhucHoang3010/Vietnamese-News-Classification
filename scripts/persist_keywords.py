from __future__ import annotations

import argparse
import asyncio
import inspect
import os
import unicodedata

import asyncpg

from src.intelligence.keyword_extractor import VietnameseKeywordExtractor
from src.intelligence.keyword_quality import is_valid_keyword


def get_value(item, *keys, default=None):
    if isinstance(item, dict):
        for key in keys:
            if key in item:
                return item[key]
        return default
    for key in keys:
        if hasattr(item, key):
            return getattr(item, key)
    return default


def normalize_keyword(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value))
    return " ".join(value.strip().split()).casefold()


def normalize_ngram(value) -> int:
    if isinstance(value, int):
        return value
    mapping = {
        "unigram": 1,
        "bigram": 2,
        "trigram": 3,
        "fourgram": 4,
        "fivegram": 5,
        "1gram": 1,
        "2gram": 2,
        "3gram": 3,
        "4gram": 4,
        "5gram": 5,
    }
    return mapping.get(str(value).strip().lower(), 1)


async def main(reset: bool, limit: int | None):
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    conn = await asyncpg.connect(dsn)

    try:
        corpus_rows = await conn.fetch("SELECT title, content FROM news ORDER BY id")
        corpus = [f"{row['title']}\n{row['content']}" for row in corpus_rows]

        print("=" * 80)
        print("KEYWORD PERSISTENCE — FULL CORPUS")
        print("=" * 80)
        print(f"Corpus documents: {len(corpus)}")

        if reset:
            await conn.execute("TRUNCATE TABLE keyword_occurrences RESTART IDENTITY")
            print("Existing keyword_occurrences cleared.")

        extractor = VietnameseKeywordExtractor()
        extractor.fit(corpus)

        query = """
            SELECT id, title, content
            FROM news
            ORDER BY published_at DESC NULLS LAST, id DESC
        """
        if limit is not None:
            query += f" LIMIT {int(limit)}"

        articles = await conn.fetch(query)
        print(f"Articles to process: {len(articles)}")

        extract_params = inspect.signature(extractor.extract).parameters
        total_saved = 0
        total_filtered = 0

        for index, article in enumerate(articles, start=1):
            news_id = article["id"]
            title = article["title"] or ""
            content = article["content"] or ""
            text = f"{title}\n{content}"

            kwargs = {}
            if "title" in extract_params:
                kwargs["title"] = title
            if "top_k" in extract_params:
                kwargs["top_k"] = 10

            keywords = extractor.extract(text, **kwargs)
            saved_for_article = 0

            for item in keywords:
                phrase = get_value(item, "phrase", "keyword", "text", default="")
                if not phrase:
                    continue
                phrase = " ".join(str(phrase).strip().split())

                ngram = normalize_ngram(get_value(item, "ngram", default=1))
                if not is_valid_keyword(phrase, ngram, text):
                    total_filtered += 1
                    continue

                keyword = normalize_keyword(phrase)
                if not keyword:
                    continue

                frequency = int(float(get_value(item, "frequency", "freq", default=1)))
                tfidf = float(get_value(item, "tfidf", default=0.0))
                association = float(get_value(item, "association", "association_boost", default=1.0))
                phrase_quality = float(get_value(item, "phrase_quality", default=1.0))
                boundary_quality = float(get_value(item, "boundary_quality", default=1.0))
                final_score = float(get_value(item, "final_score", "score", default=0.0))

                await conn.execute(
                    """
                    INSERT INTO keyword_occurrences (
                        news_id, keyword, display_keyword, ngram, frequency,
                        tfidf, association, phrase_quality, boundary_quality, final_score
                    )
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                    ON CONFLICT (news_id, keyword)
                    DO UPDATE SET
                        display_keyword = EXCLUDED.display_keyword,
                        ngram = EXCLUDED.ngram,
                        frequency = EXCLUDED.frequency,
                        tfidf = EXCLUDED.tfidf,
                        association = EXCLUDED.association,
                        phrase_quality = EXCLUDED.phrase_quality,
                        boundary_quality = EXCLUDED.boundary_quality,
                        final_score = EXCLUDED.final_score
                    """,
                    news_id, keyword, phrase, ngram, frequency,
                    tfidf, association, phrase_quality, boundary_quality, final_score,
                )
                saved_for_article += 1

            total_saved += saved_for_article
            if index == 1 or index % 25 == 0 or index == len(articles):
                print(
                    f"[{index}/{len(articles)}] news_id={news_id} "
                    f"saved={saved_for_article} total={total_saved} filtered={total_filtered}"
                )

        rows = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS keyword_rows,
                COUNT(DISTINCT news_id) AS article_count
            FROM keyword_occurrences
            """
        )

        print("=" * 80)
        print("PERSISTENCE COMPLETED")
        print(f"Keywords written: {total_saved}")
        print(f"Filtered candidates: {total_filtered}")
        print(f"Rows in database: {rows['keyword_rows']}")
        print(f"Articles with keywords: {rows['article_count']}")
        print("=" * 80)

    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    asyncio.run(main(reset=args.reset, limit=args.limit))