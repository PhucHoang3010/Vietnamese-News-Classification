import math
from typing import Any


def calculate_momentum(
    recent_articles: int,
    previous_articles: int,
) -> float:
    recent_articles = max(0, recent_articles)
    previous_articles = max(0, previous_articles)

    raw = (
        math.log1p(recent_articles)
        - math.log1p(previous_articles)
    )

    return max(0.0, raw)


def calculate_momentum_score(
    recent_articles: int,
    previous_articles: int,
) -> float:
    momentum = calculate_momentum(
        recent_articles,
        previous_articles,
    )

    return 1.0 - math.exp(-momentum)


def calculate_recency_score(
    age_days: int,
) -> float:
    age_days = max(0, age_days)

    return math.exp(
        -age_days / 3.0
    )


def normalize_strength(
    value: float,
    max_value: float,
) -> float:
    if value <= 0 or max_value <= 0:
        return 0.0

    return (
        math.log1p(value)
        / math.log1p(max_value)
    )


def calculate_trend_score(
    strength_score: float,
    momentum_score: float,
    recency_score: float,
) -> float:
    return (
        0.45 * strength_score
        + 0.35 * momentum_score
        + 0.20 * recency_score
    )


def build_trend_record(
    row: dict[str, Any],
    max_strength: float,
) -> dict[str, Any]:
    recent_articles = int(
        row["recent_articles"]
    )

    previous_articles = int(
        row["previous_articles"]
    )

    total_articles = int(
        row["total_articles"]
    )

    total_frequency = int(
        row["total_frequency"]
    )

    keyword_strength = float(
        row["keyword_strength"]
    )

    age_days = int(
        row["age_days"]
    )

    strength_score = normalize_strength(
        keyword_strength,
        max_strength,
    )

    momentum_score = calculate_momentum_score(
        recent_articles,
        previous_articles,
    )

    recency_score = calculate_recency_score(
        age_days
    )

    trend_score = calculate_trend_score(
        strength_score,
        momentum_score,
        recency_score,
    )

    # Display only.
    # Avoid fake "100%" when previous = 0.
    if previous_articles == 0:
        growth_label = "NEW"
        growth_percent = None
    else:
        growth_percent = (
            (
                recent_articles
                - previous_articles
            )
            / previous_articles
        ) * 100.0

        growth_label = (
            f"{growth_percent:+.1f}%"
        )

    return {
        "keyword": row["keyword"],
        "display_keyword": row["display_keyword"],
        "total_articles": total_articles,
        "recent_articles": recent_articles,
        "previous_articles": previous_articles,
        "total_frequency": total_frequency,
        "keyword_strength": keyword_strength,
        "strength_score": strength_score,
        "momentum_score": momentum_score,
        "growth_percent": growth_percent,
        "growth_label": growth_label,
        "age_days": age_days,
        "recency_score": recency_score,
        "trend_score": trend_score,
    }


def sort_trends(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return sorted(
        records,
        key=lambda item: (
            item["trend_score"],
            item["recent_articles"],
            item["total_articles"],
            item["keyword_strength"],
        ),
        reverse=True,
    )
