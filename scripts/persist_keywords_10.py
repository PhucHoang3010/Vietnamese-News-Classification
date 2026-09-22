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
    value = " ".join(value.strip().split())
    return value.casefold()


def normalize_ngram(value) -> int:
    if isinstance(value, int):
        return value

    text = str(value).strip().lower()

    mapping = {
        "unigram": 1,
        "bigram": 2,
        "trigram": 3,
        "fourgram": 4,
        "1gram": 1,
        "2gram": 2,
        "3gram": 3,
        "4gram": 4,
    }

    return mapping.get(text, 1)


async def main():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not set.")

    dsn = database_url.replace(
        "postgresql+asyncpg://",
        "postgresql://",
        1,
    )

    conn = await asyncpg.connect(dsn)

    try:
        print("=" * 80)
        print("KEYWORD PERSISTENCE TEST — 10 ARTICLES")
        print("=" * 80)

        # ---------------------------------------------------------
        # STEP 1: Load full corpus
        # ---------------------------------------------------------
        print("[STEP 1] Loading complete keyword corpus...")

        corpus_rows = await conn.fetch(
            """
            SELECT title, content
            FROM news
            ORDER BY id
            """
        )

        corpus = [
            f"{row['title']}\n{row['content']}"
            for row in corpus_rows
        ]

        print(f"Corpus documents: {len(corpus)}")

        # ---------------------------------------------------------
        # STEP 2: Fit extractor
        # ---------------------------------------------------------
        print("[STEP 2] Fitting keyword extractor...")

        extractor = VietnameseKeywordExtractor()
        extractor.fit(corpus)

        print("[STEP 2 OK] extractor.fit() completed.")

        # ---------------------------------------------------------
        # STEP 3: Load newest 10 articles
        # ---------------------------------------------------------
        print("[STEP 3] Loading 10 newest articles for evaluation...")

        articles = await conn.fetch(
            """
            SELECT id, title, content
            FROM news
            ORDER BY published_at DESC NULLS LAST, id DESC
            LIMIT 10
            """
        )

        print(f"Articles tested: {len(articles)}")

        # ---------------------------------------------------------
        # STEP 4: Inspect extract signature
        # ---------------------------------------------------------
        extract_signature = inspect.signature(extractor.extract)
        extract_params = extract_signature.parameters

        # ---------------------------------------------------------
        # STEP 5: Extract and persist
        # ---------------------------------------------------------
        print("[STEP 4] Extracting and persisting keywords...")

        total_saved = 0

        for index, article in enumerate(articles, start=1):
            news_id = article["id"]
            title = article["title"] or ""
            content = article["content"] or ""

            print()
            print("-" * 80)
            print(f"[{index}/10] ID={news_id}")
            print(f"Title: {title}")

            text = f"{title}\n{content}"

            kwargs = {}

            if "title" in extract_params:
                kwargs["title"] = title

            if "top_k" in extract_params:
                kwargs["top_k"] = 10

            keywords = extractor.extract(
                text,
                **kwargs,
            )

            if not keywords:
                print("  No keywords extracted.")
                continue

            saved_for_article = 0

            for item in keywords[:10]:
                phrase = get_value(
                    item,
                    "phrase",
                    "keyword",
                    "text",
                    default="",
                )

                if not phrase:
                    continue

                phrase = " ".join(
                    str(phrase).strip().split()
                )

                display_keyword = phrase

                ngram = normalize_ngram(
                    get_value(
                        item,
                        "ngram",
                        default=1,
                    )
                )

# -------------------------------------------------
                # QUALITY GATE
                # -------------------------------------------------
                if not is_valid_keyword(
                    display_keyword,
                    ngram,
                    text,
                ):
                    print(
                        f"  [FILTERED] {display_keyword}"
                    )
                    continue

                keyword = normalize_keyword(
                    display_keyword
                )

                if not keyword:
                    continue

                frequency = int(
                    float(
                        get_value(
                            item,
                            "frequency",
                            "freq",
                            default=1,
                        )
                    )
                )

                tfidf = float(
                    get_value(
                        item,
                        "tfidf",
                        default=0.0,
                    )
                )

                association = float(
                    get_value(
                        item,
                        "association",
                        default=1.0,
                    )
                )

                phrase_quality = float(
                    get_value(
                        item,
                        "phrase_quality",
                        default=1.0,
                    )
                )

                boundary_quality = float(
                    get_value(
                        item,
                        "boundary_quality",
                        default=1.0,
                    )
                )

                final_score = float(
                    get_value(
                        item,
                        "final_score",
                        "score",
                        default=0.0,
                    )
                )

                await conn.execute(
                    """
                    INSERT INTO keyword_occurrences (
                        news_id,
                        keyword,
                        display_keyword,
                        ngram,
                        frequency,
                        tfidf,
                        association,
                        phrase_quality,
                        boundary_quality,
                        final_score
                    )
                    VALUES (
                        $1,
                        $2,
                        $3,
                        $4,
                        $5,
                        $6,
                        $7,
                        $8,
                        $9,
                        $10
                    )
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
                    news_id,
                    keyword,
                    display_keyword,
                    ngram,
                    frequency,
                    tfidf,
                    association,
                    phrase_quality,
                    boundary_quality,
                    final_score,
                )

                saved_for_article += 1

                print(
                    f"  {saved_for_article:2}. "
                    f"{display_keyword:<35} "
                    f"score={final_score:.4f}"
                )

            total_saved += saved_for_article

            print(
                f"  Saved: {saved_for_article} keywords"
            )

        # ---------------------------------------------------------
        # STEP 6: Verification
        # ---------------------------------------------------------
        print()
        print("=" * 80)
        print("PERSISTENCE TEST COMPLETED")
        print("=" * 80)

        total_rows = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM keyword_occurrences
            """
        )

        article_count = await conn.fetchval(
            """
            SELECT COUNT(DISTINCT news_id)
            FROM keyword_occurrences
            """
        )

        print(f"Keywords written this run: {total_saved}")
        print(f"Rows in database: {total_rows}")
        print(f"Articles with keywords: {article_count}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
