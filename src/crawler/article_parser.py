from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ParsedArticle:
    title: str
    content: str


# Minimum amount of text considered a valid full article.
MIN_ARTICLE_CHARS = 500


# Selectors prioritized for common Vietnamese news article layouts.
CONTENT_SELECTORS = (
    # VnExpress article thường
    "article.fck_detail",
    ".fck_detail",
    "article[itemprop='articleBody']",
    "[itemprop='articleBody']",
    ".article-content",
    ".detail-content",

    # VnExpress Podcast / VOD transcript
    ".section-detail-podcast .tab-cheploi.content-tab",
    ".section-detail-podcast .scrolling-ctn",
    "#popupTranscript .scrolling-ctn",
)


# Elements that should not become part of the article body.
REMOVE_SELECTORS = (
    "script",
    "style",
    "noscript",
    "iframe",
    "svg",
    "form",
    ".social",
    ".social-item",
    ".box_embed_video",
    ".box-tin-lien-quan",
    ".box_category",
    ".box_tag",
    ".related-news",
    ".author",
)


def _clean_text(value: str) -> str:
    """
    Normalize extracted HTML/text.

    - Decode HTML entities.
    - Remove non-breaking spaces.
    - Normalize line endings.
    - Collapse repeated spaces.
    - Collapse excessive blank lines.
    """
    value = html.unescape(value)
    value = value.replace("\xa0", " ")

    value = re.sub(r"\r\n?", "\n", value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)

    return value.strip()


def _filter_podcast_noise(text: str) -> str:
    """
    Remove podcast transcript UI noise lines.
    """
    noise_lines = {
        "Xem bản chép lời",
        "Bản chép lời",
        "0:00/0:00",
    }

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and line.strip() not in noise_lines
    ]

    return "\n".join(lines)


def _extract_title(soup: BeautifulSoup) -> str:
    """
    Extract article title from common page structures.
    Priority: h1 -> og:title -> <title> (with VnExpress cleanup)
    """

    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(" ", strip=True)
        if title:
            return title

    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
        if title:
            return title

    if soup.title:
        title = soup.title.get_text(" ", strip=True)
        title = re.sub(r"^Nghe podcasts\s*\|\s*", "", title, flags=re.I)
        title = re.sub(r"\s*-\s*Báo VnExpress\s*$", "", title, flags=re.I)
        return title.strip()

    return ""


def _extract_from_container(container) -> str:
    """
    Extract readable text from an article container.

    Paragraphs/headings are separated by blank lines so the
    downstream tokenizer receives a readable document.
    """

    paragraphs: list[str] = []

    for element in container.select(
        "p, h2, h3, blockquote"
    ):
        text = _clean_text(
            element.get_text(
                " ",
                strip=True,
            )
        )

        if not text:
            continue

        # Avoid immediately duplicated paragraphs.
        if paragraphs and paragraphs[-1] == text:
            continue

        paragraphs.append(text)

    if paragraphs:
        return _filter_podcast_noise("\n\n".join(paragraphs))

    return _filter_podcast_noise(
        _clean_text(
            container.get_text(
                " ",
                strip=True,
            )
        )
    )


def _extract_json_ld(
    soup: BeautifulSoup,
) -> tuple[str, str]:
    """
    Fallback extraction from schema.org JSON-LD.

    Some news websites expose articleBody and headline
    through NewsArticle/Article structured data.
    """

    scripts = soup.select(
        "script[type='application/ld+json']"
    )

    for script in scripts:
        raw = script.string or script.get_text()

        if not raw.strip():
            continue

        try:
            data = json.loads(raw)
        except (
            json.JSONDecodeError,
            TypeError,
        ):
            continue

        objects = (
            data
            if isinstance(data, list)
            else [data]
        )

        # Search both the root object and @graph.
        expanded_objects = list(objects)

        for obj in objects:
            if not isinstance(obj, dict):
                continue

            graph = obj.get("@graph")

            if isinstance(graph, list):
                expanded_objects.extend(
                    item
                    for item in graph
                    if isinstance(item, dict)
                )

        for obj in expanded_objects:
            if not isinstance(obj, dict):
                continue

            article_body = obj.get("articleBody")

            if not article_body:
                continue

            title = _clean_text(
                str(
                    obj.get("headline")
                    or ""
                )
            )

            body_soup = BeautifulSoup(
                str(article_body),
                "html.parser",
            )

            content = _filter_podcast_noise(
                _clean_text(
                    body_soup.get_text(
                        "\n",
                        strip=True,
                    )
                )
            )

            if len(content) >= MIN_ARTICLE_CHARS:
                return title, content

    return "", ""


def parse_article_html(
    html_content: str,
) -> ParsedArticle:
    """
    Parse full HTML page and extract article title/body.

    Raises:
        ValueError:
            If HTML is empty or no sufficiently long
            article body can be extracted.
    """

    if not html_content or not html_content.strip():
        raise ValueError(
            "Empty HTML content."
        )

    soup = BeautifulSoup(
        html_content,
        "html.parser",
    )

    # Remove noisy/non-content elements first.
    for selector in REMOVE_SELECTORS:
        for element in soup.select(selector):
            element.decompose()

    title = _extract_title(soup)

    # ---------------------------------------------------------
    # Primary extraction
    # ---------------------------------------------------------
    for selector in CONTENT_SELECTORS:
        container = soup.select_one(selector)

        if container is None:
            continue

        content = _extract_from_container(
            container
        )

        if len(content) >= MIN_ARTICLE_CHARS:
            return ParsedArticle(
                title=title,
                content=content,
            )

    # ---------------------------------------------------------
    # JSON-LD fallback
    # ---------------------------------------------------------
    json_title, json_content = _extract_json_ld(
        soup
    )

    if len(json_content) >= MIN_ARTICLE_CHARS:
        return ParsedArticle(
            title=title or json_title,
            content=json_content,
        )

    raise ValueError(
        "Could not extract a sufficiently long "
        "article body."
    )