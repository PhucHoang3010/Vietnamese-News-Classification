from collections import defaultdict
from typing import Any


def build_keyword_document_map(
    rows: list[dict[str, Any]],
) -> dict[str, set[int]]:
    result: dict[str, set[int]] = defaultdict(set)

    for row in rows:
        result[row["keyword"]].add(
            int(row["news_id"])
        )

    return dict(result)


def calculate_jaccard(
    left: set[int],
    right: set[int],
) -> float:
    if not left or not right:
        return 0.0

    union = left | right

    if not union:
        return 0.0

    return len(left & right) / len(union)


def build_cooccurrence_graph(
    rows: list[dict[str, Any]],
    min_overlap: int = 2,
    min_jaccard: float = 0.20,
) -> dict[str, dict[str, float]]:
    keyword_docs = build_keyword_document_map(rows)

    keywords = sorted(keyword_docs)

    graph: dict[str, dict[str, float]] = {
        keyword: {}
        for keyword in keywords
    }

    for i, left_keyword in enumerate(keywords):
        left_docs = keyword_docs[left_keyword]

        for right_keyword in keywords[i + 1:]:
            right_docs = keyword_docs[right_keyword]

            overlap = left_docs & right_docs

            if len(overlap) < min_overlap:
                continue

            jaccard = calculate_jaccard(
                left_docs,
                right_docs,
            )

            if jaccard < min_jaccard:
                continue

            graph[left_keyword][right_keyword] = jaccard
            graph[right_keyword][left_keyword] = jaccard

    return graph


def find_topic_clusters(
    graph: dict[str, dict[str, float]],
    min_cluster_size: int = 2,
) -> list[list[str]]:
    visited: set[str] = set()
    clusters: list[list[str]] = []

    for keyword in graph:
        if keyword in visited:
            continue

        stack = [keyword]
        component: list[str] = []

        while stack:
            current = stack.pop()

            if current in visited:
                continue

            visited.add(current)
            component.append(current)

            for neighbor in graph[current]:
                if neighbor not in visited:
                    stack.append(neighbor)

        if len(component) >= min_cluster_size:
            clusters.append(
                sorted(component)
            )

    return clusters


def rank_topic_keywords(
    keywords: list[str],
    trend_records: dict[str, dict[str, Any]],
) -> list[str]:
    return sorted(
        keywords,
        key=lambda keyword: (
            trend_records.get(
                keyword,
                {},
            ).get(
                "trend_score",
                0.0,
            ),
            trend_records.get(
                keyword,
                {},
            ).get(
                "total_articles",
                0,
            ),
        ),
        reverse=True,
    )


def build_hot_topic(
    keywords: list[str],
    trend_records: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    ranked = rank_topic_keywords(
        keywords,
        trend_records,
    )

    top_keyword = ranked[0] if ranked else ""

    scores = [
        trend_records.get(
            keyword,
            {},
        ).get(
            "trend_score",
            0.0,
        )
        for keyword in keywords
    ]

    article_counts = [
        trend_records.get(
            keyword,
            {},
        ).get(
            "total_articles",
            0,
        )
        for keyword in keywords
    ]

    return {
        "label": (
            trend_records.get(
                top_keyword,
                {},
            ).get(
                "display_keyword",
                top_keyword,
            )
            if top_keyword
            else ""
        ),
        "keywords": ranked,
        "keyword_count": len(ranked),
        "max_trend_score": max(scores) if scores else 0.0,
        "topic_strength": (
            sum(scores) / len(scores)
            if scores
            else 0.0
        ),
        "article_volume": max(
            article_counts,
            default=0,
        ),
    }


def rank_hot_topics(
    topics: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return sorted(
        topics,
        key=lambda topic: (
            topic["topic_strength"],
            topic["keyword_count"],
            topic["article_volume"],
        ),
        reverse=True,
    )
