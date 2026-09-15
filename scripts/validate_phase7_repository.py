import inspect

from src.db.repository import NewsRepository


print("=" * 60)
print("PHASE 7 — SECTION 7.9.1")
print("REPOSITORY DEDUPLICATION VALIDATION")
print("=" * 60)


required_methods = [
    "exists_by_url",
    "exists_by_content_hash",
    "create_news",
    "create_news_deduplicated",
    "get_news_by_id",
    "list_news",
]


for method_name in required_methods:
    check = hasattr(NewsRepository, method_name)

    if not check:
        raise AssertionError(
            f"Missing repository method: {method_name}"
        )

    print(f"PASS: {method_name}")


method = getattr(
    NewsRepository,
    "create_news_deduplicated",
)

if not inspect.iscoroutinefunction(method):
    raise AssertionError(
        "create_news_deduplicated must be async"
    )

print(
    "PASS: create_news_deduplicated is async"
)

print("=" * 60)
print("SECTION 7.9.1 VALIDATION: PASS")
print("=" * 60)