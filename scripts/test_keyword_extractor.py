from pathlib import Path

from src.intelligence.keyword_extractor import (
    VietnameseKeywordExtractor,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

STOPWORDS_PATH = (
    PROJECT_ROOT
    / "data"
    / "stopwords_vi.txt"
)


def main():

    extractor = VietnameseKeywordExtractor(
        STOPWORDS_PATH
    )

    text = """
    Giá vàng trong nước tiếp tục tăng mạnh
    trong phiên giao dịch hôm nay. Giá vàng thế giới
    biến động do kỳ vọng về chính sách lãi suất của Fed.
    Thị trường vàng đang nhận được sự quan tâm lớn
    từ nhà đầu tư.
    """

    keywords = extractor.extract(
        text,
        top_k=15,
    )

    print("\nKEYWORDS\n")

    for item in keywords:
        print(
            f"{item['term']:<30}"
            f"{item['type']:<10}"
            f"freq={item['frequency']:<3}"
            f"score={item['score']:.2f}"
        )


if __name__ == "__main__":
    main()