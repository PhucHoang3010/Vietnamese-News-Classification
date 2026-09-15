import hashlib
from urllib.parse import urlparse, parse_qsl, urlencode


TRACKING_PARAM_EXACT = {
    "fbclid",
    "gclid",
    "ref",
    "redirect",
    "source",
    "rss",
    "from",
    "zarsrc",
    "catename",
}


def generate_content_hash(title: str, content: str) -> dict[str, str]:
    """
    Generate SHA-256 hash of title + content for deduplication.

    Returns:
        Dict with 'content_hash' (64-char hex string)
    """
    combined = (title.strip() + "\n" + content.strip()).encode("utf-8")
    content_hash = hashlib.sha256(combined).hexdigest()
    return {"content_hash": content_hash}


def normalize_url(url: str) -> str:
    """
    Normalize URL for deduplication:
    - Strip whitespace
    - Remove fragment
    - Remove tracking query parameters (utm_*, fbclid, gclid, etc.)
    - Normalize scheme/host
    - Remove trailing slash (except root)
    """
    url = url.strip()

    if not url:
        return ""

    parsed = urlparse(url)

    # Remove tracking parameters
    query_params = parse_qsl(
        parsed.query,
        keep_blank_values=True,
    )

    filtered_params = []

    for key, value in query_params:
        key_lower = key.lower()

        if key_lower.startswith("utm_"):
            continue

        if key_lower in TRACKING_PARAM_EXACT:
            continue

        filtered_params.append((key, value))

    new_query = urlencode(
        filtered_params,
        doseq=True,
    )

    # Reconstruct without fragment and with filtered query
    normalized = parsed._replace(
        fragment="",
        query=new_query,
    ).geturl()

    # Remove trailing slash (except for root path)
    if normalized.endswith("/") and len(normalized) > len(parsed.scheme + "://" + parsed.netloc + "/"):
        normalized = normalized.rstrip("/")

    return normalized