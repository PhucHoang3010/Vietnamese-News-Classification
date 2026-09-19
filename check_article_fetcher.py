import asyncio

from src.crawler.article_fetcher import AsyncArticleFetcher


URL = (
    "https://vnexpress.net/"
    "raphinha-dang-tren-duong-tro-thanh-bieu-tuong-moi-cua-barca-5120208.html"
)


async def main() -> None:
    async with AsyncArticleFetcher() as fetcher:
        article = await fetcher.fetch(URL)

    print("TITLE:")
    print(article.title)

    print()
    print("CONTENT_LEN:")
    print(len(article.content))

    print()
    print("CONTENT_PREVIEW:")
    print(article.content[:1000])


if __name__ == "__main__":
    asyncio.run(main())