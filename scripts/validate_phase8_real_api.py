from __future__ import annotations

import asyncio

import httpx

from src.crawler.prediction_client import NewsPredictionClient


API_BASE_URL = "http://127.0.0.1:8000"


async def main() -> None:
    print("=" * 70)
    print("SECTION 8.4 REAL FASTAPI INTEGRATION VALIDATION")
    print("=" * 70)

    async with httpx.AsyncClient() as http_client:
        # -------------------------------------------------------------
        # 1. Check FastAPI health
        # -------------------------------------------------------------
        health_response = await http_client.get(
            f"{API_BASE_URL}/health",
            timeout=10.0,
        )

        assert health_response.status_code == 200, (
            f"Health check failed: "
            f"{health_response.status_code} "
            f"{health_response.text}"
        )

        print("PASS FastAPI health endpoint")

        # -------------------------------------------------------------
        # 2. Create REAL prediction client
        # -------------------------------------------------------------
        prediction_client = NewsPredictionClient(
            http_client,
            base_url=API_BASE_URL,
        )

        print("PASS NewsPredictionClient initialized")

        # -------------------------------------------------------------
        # 3. Send REAL HTTP request to FastAPI /predict/batch
        # -------------------------------------------------------------
        articles = [
            {
                "text": (
                    "Chính phủ đưa ra chính sách mới nhằm "
                    "hỗ trợ doanh nghiệp và thúc đẩy tăng trưởng kinh tế."
                )
            },
            {
                "text": (
                    "Bộ Giáo dục công bố phương án tuyển sinh "
                    "đại học mới cho năm học tới."
                )
            },
            {
                "text": (
                    "Các nhà khoa học công bố nghiên cứu mới "
                    "về công nghệ và trí tuệ nhân tạo."
                )
            },
        ]

        predictions = await prediction_client.predict_batch(
            articles
        )

        # -------------------------------------------------------------
        # 4. Validate prediction count
        # -------------------------------------------------------------
        assert len(predictions) == len(articles), (
            f"Prediction count mismatch: "
            f"{len(predictions)} != {len(articles)}"
        )

        print("PASS prediction count")

        # -------------------------------------------------------------
        # 5. Validate response contract
        # -------------------------------------------------------------
        for index, prediction in enumerate(predictions):
            assert isinstance(prediction, dict), (
                f"Prediction {index} is not a dict"
            )

            assert isinstance(
                prediction.get("label"),
                str,
            ), (
                f"Prediction {index} has invalid label"
            )

            assert prediction.get("status") in {
                "OK",
                "UNKNOWN",
            }, (
                f"Prediction {index} has invalid status: "
                f"{prediction.get('status')!r}"
            )

            if prediction["status"] == "OK":
                assert prediction.get("score") is not None, (
                    f"Prediction {index} has OK status "
                    "but score is None"
                )

        print("PASS prediction response contract")

        # -------------------------------------------------------------
        # 6. Print real predictions
        # -------------------------------------------------------------
        print()
        print("REAL FASTAPI PREDICTIONS:")

        for index, prediction in enumerate(predictions, start=1):
            print(
                f"  Article {index}: "
                f"label={prediction['label']!r}, "
                f"score={prediction['score']!r}, "
                f"status={prediction['status']!r}"
            )

        # -------------------------------------------------------------
        # 7. Empty batch contract
        # -------------------------------------------------------------
        empty_result = await prediction_client.predict_batch([])

        assert empty_result == [], (
            f"Expected empty result, got {empty_result!r}"
        )

        print("PASS empty batch handling")

    print()
    print("=" * 70)
    print("SECTION 8.4 REAL FASTAPI INTEGRATION: PASS")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())