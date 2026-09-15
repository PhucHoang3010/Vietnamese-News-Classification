from dataclasses import dataclass
from datetime import datetime


@dataclass
class CrawledArticle:
    url: str
    title: str
    content: str
    source: str
    published_at: datetime | None = None