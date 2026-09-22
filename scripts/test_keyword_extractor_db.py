"""
Real-database integration test for the Vietnamese keyword extractor.

Version: v0.4
Pipeline:
    PostgreSQL corpus -> VietnameseKeywordExtractor.fit()
                       -> article extraction -> ranked keyword output

This script intentionally does NOT modify the production classifier or database.
It is a read-only evaluation script for the intelligence/keyword_extractor module.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import sys
import traceback
from typing import Any

from sqlalchemy import select

from src.db.database import AsyncSessionLocal
from src.db.models import News
from src.intelligence.keyword_extractor import VietnameseKeywordExtractor


VERSION = "v0.4"
DEFAULT_ARTICLE_LIMIT = 10
DEFAULT_TOP_K = 10


def clean_text(value: Any) -> str:
    """Normalize nullable DB text into a compact, safe string."""
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def build_article_text(title: str, content: str) -> str:
    """Build extractor input while preserving the title as a separate first line."""
    title = clean_text(title)
    content = clean_text(content)

    if title and content:
        return f"{title}\n{content}"

    return title or content


def get_field(item: Any, *names: str, default: Any = None) -> Any:
    """Read a field from either a dict-like result or an object/dataclass."""
    if isinstance(item, dict):
        for name in names:
            if name in item and item[name] is not None:
                return item[name]
        return default

    for name in names:
        value = getattr(item, name, None)

        if value is not None:
            return value

    return default


def format_number(value: Any, digits: int = 4) -> str:
    """Format optional numeric values safely."""
    if value is None:
        return "-"

    try:
        return f"{float(value):.{digits}f}"

    except (TypeError, ValueError):
        return str(value)


def format_frequency(value: Any) -> str:
    """Format frequency/count values safely."""
    if value is None:
        return "-"

    try:
        return str(int(value))

    except (TypeError, ValueError):
        return str(value)


def print_keyword(item: Any, rank: int) -> None:
    """Print one keyword result using a schema-tolerant formatter."""
    phrase = get_field(
        item,
        "phrase",
        "keyword",
        "text",
        "term",
        "ngram_text",
        default="<unknown>",
    )

    ngram_type = get_field(
        item,
        "ngram",
        "ngram_type",
        "type",
        "length",
        default="",
    )

    freq = get_field(
        item,
        "freq",
        "frequency",
        "count",
    )

    tfidf = get_field(
        item,
        "tfidf",
        "tfidf_score",
    )

    score = get_field(
        item,
        "score",
        "keyword_score",
        "final_score",
    )

    association = get_field(
        item,
        "association_boost",
        "association",
        "pmi",
        "pmi_score",
    )

    line = (
        f"{rank:>2}. {str(phrase):<34} "
        f"{str(ngram_type):<9} "
        f"freq={format_frequency(freq):<4} "
        f"tfidf={format_number(tfidf):<8} "
        f"score={format_number(score):<8}"
    )

    if association is not None:
        line += f" assoc={format_number(association, 3)}"

    print(line, flush=True)


def call_extractor(
    extractor: VietnameseKeywordExtractor,
    text: str,
    title: str,
    top_k: int,
) -> Any:
    """
    Call extract() while remaining compatible with title-aware
    and title-unaware extractor APIs.
    """
    kwargs: dict[str, Any] = {
        "top_k": top_k,
    }

    try:
        parameters = inspect.signature(
            extractor.extract
        ).parameters

        if "title" in parameters:
            kwargs["title"] = title

        elif "article_title" in parameters:
            kwargs["article_title"] = title

    except (TypeError, ValueError):
        # Fallback for implementations where signature inspection
        # is not available.
        kwargs["title"] = title

    return extractor.extract(
        text,
        **kwargs,
    )


async def load_corpus(session) -> list[str]:
    """
    Load the complete corpus used for:
    - TF-IDF fitting
    - corpus frequency statistics
    - PMI / association statistics
    """
    stmt = (
        select(
            News.title,
            News.content,
        )
        .order_by(
            News.id.asc()
        )
    )

    result = await session.execute(stmt)

    rows = result.all()

    corpus: list[str] = []

    for title, content in rows:
        text = build_article_text(
            title,
            content,
        )

        if text:
            corpus.append(text)

    return corpus


async def load_articles(
    session,
    limit: int,
) -> list[News]:
    """Load the newest articles for reproducible manual evaluation."""
    stmt = (
        select(News)
        .order_by(
            News.published_at.desc().nullslast(),
            News.crawled_at.desc(),
            News.id.desc(),
        )
        .limit(limit)
    )

    result = await session.execute(stmt)

    return list(
        result.scalars().all()
    )


async def main(
    article_limit: int,
    top_k: int,
) -> None:
    print(
        "=" * 80,
        flush=True,
    )

    print(
        f"KEYWORD EXTRACTION {VERSION} - CORPUS TEST",
        flush=True,
    )

    print(
        "=" * 80,
        flush=True,
    )

    print(
        "[STEP 1] Opening PostgreSQL session...",
        flush=True,
    )

    async with AsyncSessionLocal() as session:

        print(
            "[STEP 2] Loading complete keyword corpus...",
            flush=True,
        )

        corpus = await load_corpus(
            session
        )

        if not corpus:
            raise RuntimeError(
                "The news table returned no usable "
                "title/content documents."
            )

        print(
            f"Corpus documents: {len(corpus)}",
            flush=True,
        )

        print(
            "[STEP 3] Fitting v0.4 extractor on corpus...",
            flush=True,
        )

        extractor = VietnameseKeywordExtractor()

        extractor.fit(
            corpus
        )

        print(
            "TF-IDF / corpus statistics fitted.",
            flush=True,
        )

        print(
            "[STEP 3 OK] extractor.fit() completed.",
            flush=True,
        )

        print(
            f"[STEP 4] Loading "
            f"{article_limit} newest articles for evaluation...",
            flush=True,
        )

        articles = await load_articles(
            session,
            article_limit,
        )

        if not articles:
            raise RuntimeError(
                "No articles are available "
                "for extraction testing."
            )

        print(
            f"Articles tested: {len(articles)}",
            flush=True,
        )

        print(
            "[STEP 5] Extracting keywords...",
            flush=True,
        )

        for index, article in enumerate(
            articles,
            start=1,
        ):
            title = clean_text(
                article.title
            )

            text = build_article_text(
                article.title,
                article.content,
            )

            print(
                "\n" + "-" * 80,
                flush=True,
            )

            print(
                f"[{index}] ID={article.id}",
                flush=True,
            )

            print(
                f"Category: "
                f"{clean_text(article.category)}",
                flush=True,
            )

            print(
                f"Title: {title}",
                flush=True,
            )

            print(
                "\nKeywords:",
                flush=True,
            )

            try:
                keywords = call_extractor(
                    extractor=extractor,
                    text=text,
                    title=title,
                    top_k=top_k,
                )

            except Exception:
                print(
                    f"[ERROR] Extraction failed "
                    f"for article ID={article.id}",
                    file=sys.stderr,
                    flush=True,
                )

                traceback.print_exc()

                raise

            if keywords is None:
                print(
                    "  No keywords returned.",
                    flush=True,
                )
                continue

            # Support either:
            #   list[dict]
            # or
            #   {"keywords": [...]}
            # or
            #   {"results": [...]}
            if isinstance(
                keywords,
                dict,
            ):
                keywords_list = keywords.get(
                    "keywords",
                    keywords.get(
                        "results",
                        [],
                    ),
                )

            else:
                keywords_list = list(
                    keywords
                )

            if not keywords_list:
                print(
                    "  No keywords returned.",
                    flush=True,
                )
                continue

            for rank, item in enumerate(
                keywords_list,
                start=1,
            ):
                print_keyword(
                    item,
                    rank,
                )

        print(
            "\n" + "=" * 80,
            flush=True,
        )

        print(
            "v0.4 TEST COMPLETED",
            flush=True,
        )

        print(
            "=" * 80,
            flush=True,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run v0.4 Vietnamese keyword extraction "
            "against the real PostgreSQL corpus."
        )
    )

    parser.add_argument(
        "--articles",
        type=int,
        default=DEFAULT_ARTICLE_LIMIT,
        help=(
            f"Number of newest articles to evaluate "
            f"(default: {DEFAULT_ARTICLE_LIMIT})."
        ),
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help=(
            f"Number of keywords per article "
            f"(default: {DEFAULT_TOP_K})."
        ),
    )

    args = parser.parse_args()

    if args.articles < 1:
        parser.error(
            "--articles must be >= 1"
        )

    if args.top_k < 1:
        parser.error(
            "--top-k must be >= 1"
        )

    return args


if __name__ == "__main__":
    args = parse_args()

    asyncio.run(
        main(
            article_limit=args.articles,
            top_k=args.top_k,
        )
    )