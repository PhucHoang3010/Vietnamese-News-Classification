import html
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError

from src.crawler.models import CrawledArticle


ATOM_NS = "http://www.w3.org/2005/Atom"


def parse_published_date(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None

    value = value.strip()

    # RSS: RFC 2822, ví dụ:
    # Mon, 14 Sep 2026 08:00:00 +0700
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        pass

    # Atom: ISO 8601, ví dụ:
    # 2026-09-14T10:00:00+07:00
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _clean_rss_html(text: str) -> str:
    """Clean HTML tags/entities from RSS description or content."""
    if not text:
        return ""

    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_link(item: ElementTree.Element) -> str:
    """Extract URL from RSS or Atom link."""
    link_elem = item.find("link")

    if link_elem is None:
        link_elem = item.find(f"{{{ATOM_NS}}}link")

    if link_elem is None:
        return ""

    url = link_elem.attrib.get("href") or link_elem.text or ""
    return url.strip()


def parse_rss(xml_content: str, source: str) -> list[CrawledArticle]:
    if not xml_content or not xml_content.strip():
        return []

    try:
        root = ElementTree.fromstring(xml_content)
    except ParseError:
        return []

    articles: list[CrawledArticle] = []

    # RSS 2.0
    items = root.findall(".//item")

    # Atom
    if not items:
        items = root.findall(f".//{{{ATOM_NS}}}entry")

    for item in items:
        title_raw = item.findtext("title")

        if title_raw is None:
            title_raw = item.findtext(f"{{{ATOM_NS}}}title")

        title = _clean_rss_html(title_raw or "")

        url = _extract_link(item)

        content_raw = (
            item.findtext(
                "{http://purl.org/rss/1.0/modules/content/}encoded"
            )
            or item.findtext("description")
            or item.findtext(f"{{{ATOM_NS}}}summary")
            or item.findtext(f"{{{ATOM_NS}}}content")
            or ""
        )

        content = _clean_rss_html(content_raw)

        published_raw = (
            item.findtext("pubDate")
            or item.findtext("published")
            or item.findtext("updated")
            or item.findtext(
                "{http://purl.org/dc/elements/1.1/}date"
            )
            or item.findtext(f"{{{ATOM_NS}}}published")
            or item.findtext(f"{{{ATOM_NS}}}updated")
        )

        if not title or not url:
            continue

        articles.append(
            CrawledArticle(
                url=url,
                title=title,
                content=content,
                source=source,
                published_at=parse_published_date(published_raw),
            )
        )

    return articles