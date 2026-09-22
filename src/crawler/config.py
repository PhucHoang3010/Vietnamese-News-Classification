from dataclasses import dataclass


@dataclass(frozen=True)
class RSSFeedConfig:
    name: str
    url: str
    source: str
    enabled: bool = True


DEFAULT_RSS_FEEDS = [
    RSSFeedConfig(
        name="vnexpress",
        url="https://vnexpress.net/rss/tin-moi-nhat.rss",
        source="VnExpress",
    ),
    RSSFeedConfig(
        name="tuoitre",
        url="https://tuoitre.vn/home.rss",
        source="Tuổi Trẻ",
    ),
    RSSFeedConfig(
        name="thanhnien",
        url="https://thanhnien.vn/rss/home.rss",
        source="Thanh Niên",
    ),
]
