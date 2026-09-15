from typing import List, Optional

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """
    Request for predicting one Vietnamese news article.
    """

    text: str = Field(
        ...,
        min_length=1,
        max_length=20_000,
        description="Vietnamese news title/content to classify."
    )


class PredictionResponse(BaseModel):
    """
    Prediction result for one news article.
    """

    label: str = Field(
        ...,
        description="Predicted news category."
    )

    score: Optional[float] = Field(
        default=None,
        description="LinearSVC decision score. Not a probability."
    )

    status: str = Field(
        ...,
        description="Prediction status: OK or UNKNOWN."
    )


class BatchPredictionRequest(BaseModel):
    """
    Request for predicting multiple Vietnamese news articles.
    """

    items: List[PredictionRequest] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of news articles to classify."
    )


class BatchPredictionResponse(BaseModel):
    """
    Batch prediction response.
    """

    results: List[PredictionResponse] = Field(
        ...,
        description="Prediction results."
    )

    count: int = Field(
        ...,
        ge=0,
        description="Number of prediction results."
    )
