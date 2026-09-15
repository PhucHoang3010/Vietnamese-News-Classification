from fastapi import APIRouter, Request

from api.schemas import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
)

router = APIRouter(
    prefix="/predict",
    tags=["Prediction"]
)


@router.post(
    "",
    response_model=PredictionResponse,
    summary="Predict one Vietnamese news article"
)
def predict(
    request: Request,
    payload: PredictionRequest
) -> PredictionResponse:

    predictor = request.app.state.predictor

    result = predictor.predict_one(payload.text)

    return PredictionResponse(
        label=result["label"],
        score=result["score"],
        status=result["status"]
    )


@router.post(
    "/batch",
    response_model=BatchPredictionResponse,
    summary="Predict multiple Vietnamese news articles"
)
def predict_batch(
    request: Request,
    payload: BatchPredictionRequest
) -> BatchPredictionResponse:

    predictor = request.app.state.predictor

    texts = [item.text for item in payload.items]

    results = predictor.predict_batch(texts)

    response_results = [
        PredictionResponse(
            label=result["label"],
            score=result["score"],
            status=result["status"]
        )
        for result in results
    ]

    return BatchPredictionResponse(
        results=response_results,
        count=len(response_results)
    )
