from __future__ import annotations

import httpx


class PredictionAPIError(Exception):
    """Prediction API request failed."""


class NewsPredictionClient:
    """
    HTTP client for the FastAPI prediction service.

    The crawler communicates with the ML predictor through
    POST /predict/batch instead of importing the Predictor directly.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str = "http://127.0.0.1:8000",
        timeout_seconds: float = 30.0,
    ) -> None:
        self.client = client
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def predict_batch(
        self,
        articles: list[dict[str, str]],
    ) -> list[dict]:
        """
        Send articles to FastAPI /predict/batch.

        Expected input:
            [{"text": "..."}]

        Expected output:
            {
                "results": [
                    {
                        "label": "...",
                        "score": ...,
                        "status": "OK" | "UNKNOWN"
                    }
                ],
                "count": ...
            }
        """

        if not articles:
            return []

        response = await self.client.post(
            f"{self.base_url}/predict/batch",
            json={"items": articles},
            timeout=self.timeout_seconds,
        )

        if response.status_code >= 400:
            raise PredictionAPIError(
                f"Prediction API returned HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise PredictionAPIError(
                "Prediction API returned invalid JSON."
            ) from exc

        results = payload.get("results")

        if not isinstance(results, list):
            raise PredictionAPIError(
                "Prediction API response does not contain "
                "a valid 'results' list."
            )

        if len(results) != len(articles):
            raise PredictionAPIError(
                "Prediction count does not match input article count: "
                f"{len(results)} != {len(articles)}"
            )

        normalized_results: list[dict] = []

        for index, result in enumerate(results):
            if not isinstance(result, dict):
                raise PredictionAPIError(
                    f"Prediction result at index {index} is not an object."
                )

            label = result.get("label")
            score = result.get("score")
            status = result.get("status")

            if not isinstance(label, str):
                raise PredictionAPIError(
                    f"Prediction result at index {index} has invalid 'label'."
                )

            if status not in {"OK", "UNKNOWN"}:
                raise PredictionAPIError(
                    f"Prediction result at index {index} has invalid "
                    f"'status': {status!r}"
                )

            normalized_results.append(
                {
                    "label": label,
                    "score": score,
                    "status": status,
                }
            )

        return normalized_results