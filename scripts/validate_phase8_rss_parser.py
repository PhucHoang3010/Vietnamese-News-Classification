from src.crawler.config import DEFAULT_RSS_FEEDS
from src.crawler.rss_parser import parse_rss


TEST_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
    <channel>
        <title>Test News</title>

        <item>
            <title>AI đang thay đổi ngành công nghệ</title>
            <link>https://example.com/article-1</link>
            <description><![CDATA[
                <a href="#">
                    <img src="test.jpg"/>
                </a>
                Nội dung bài viết thử nghiệm.
            ]]></description>
            <pubDate>Mon, 14 Sep 2026 08:00:00 +0700</pubDate>
        </item>

        <item>
            <title>Bài viết thứ hai</title>
            <link>https://example.com/article-2</link>
            <content:encoded>
                <![CDATA[
                Nội dung bài viết thứ hai.
                ]]>
            </content:encoded>
            <pubDate>Mon, 14 Sep 2026 09:00:00 +0700</pubDate>
        </item>

        <item>
            <title></title>
            <link>https://example.com/invalid</link>
            <description>Missing title</description>
        </item>
    </channel>
</rss>
"""


ATOM_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>Test Atom Feed</title>

    <entry>
        <title>Atom News</title>
        <link href="https://example.com/atom-1"/>
        <summary><![CDATA[
            <p>Nội dung Atom thử nghiệm.</p>
        ]]></summary>
        <updated>2026-09-14T10:00:00+07:00</updated>
    </entry>
</feed>
"""


MALFORMED_XML = (
    "<?xml version='1.0'?>"
    "<rss><channel>"
    "<item><title>Lỗi XML không đóng tag"
)


def main():
    print("=" * 70)
    print("SECTION 8.1 RSS PARSER VALIDATION")
    print("=" * 70)

    # ---------------------------------------------------------
    # TEST 1: Feed configuration
    # ---------------------------------------------------------
    assert len(DEFAULT_RSS_FEEDS) >= 1

    feed = DEFAULT_RSS_FEEDS[0]

    assert feed.name
    assert feed.url
    assert feed.source
    assert feed.enabled is True

    print("PASS RSS feed configuration")

    # ---------------------------------------------------------
    # TEST 2: RSS parsing
    # ---------------------------------------------------------
    articles = parse_rss(
        TEST_RSS,
        source="Test Source",
    )

    assert len(articles) == 2

    print("PASS RSS item parsing")

    # ---------------------------------------------------------
    # TEST 3: RSS fields + HTML cleaning
    # ---------------------------------------------------------
    first = articles[0]

    assert first.title == "AI đang thay đổi ngành công nghệ"
    assert first.url == "https://example.com/article-1"
    assert "Nội dung bài viết thử nghiệm" in first.content
    assert "<img" not in first.content
    assert "<a" not in first.content
    assert first.source == "Test Source"
    assert first.published_at is not None

    print("PASS article fields & HTML cleaning")

    # ---------------------------------------------------------
    # TEST 4: content:encoded
    # ---------------------------------------------------------
    second = articles[1]

    assert second.content
    assert "Nội dung bài viết thứ hai" in second.content

    print("PASS content:encoded extraction")

    # ---------------------------------------------------------
    # TEST 5: Invalid item
    # ---------------------------------------------------------
    assert all(article.title for article in articles)
    assert all(article.url for article in articles)

    print("PASS invalid RSS item handling")

    # ---------------------------------------------------------
    # TEST 6: Atom support
    # ---------------------------------------------------------
    atom_articles = parse_rss(
        ATOM_FEED,
        source="Atom Source",
    )

    assert len(atom_articles) == 1

    atom_article = atom_articles[0]

    assert atom_article.title == "Atom News"
    assert atom_article.url == "https://example.com/atom-1"
    assert "Nội dung Atom thử nghiệm" in atom_article.content
    assert "<p>" not in atom_article.content
    assert atom_article.published_at is not None

    print("PASS Atom feed support")

    # ---------------------------------------------------------
    # TEST 7: Malformed XML safety
    # ---------------------------------------------------------
    bad_articles = parse_rss(
        MALFORMED_XML,
        source="Bad Source",
    )

    assert bad_articles == []

    print("PASS malformed XML safety check")

    # ---------------------------------------------------------
    # TEST 8: Empty XML safety
    # ---------------------------------------------------------
    assert parse_rss("", source="Empty Source") == []
    assert parse_rss("   ", source="Empty Source") == []

    print("PASS empty XML safety check")

    print("=" * 70)
    print("SECTION 8.1 RSS PARSER: PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()