from contextlib import asynccontextmanager

from fastapi import FastAPI

from predictor.predictor import VietnameseNewsPredictor
from api.routes.prediction import router as prediction_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize shared application resources once at startup.
    """
    app.state.predictor = VietnameseNewsPredictor()

    yield

    # Reserved for future cleanup resources.
    app.state.predictor = None


app = FastAPI(
    title="Vietnamese News Classification API",
    description=(
        "REST API for Vietnamese news classification "
        "using Underthesea, TF-IDF and LinearSVC."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get(
    "/health",
    tags=["System"],
    summary="Health check"
)
def health():
    return {
        "status": "OK",
        "service": "Vietnamese News Classification API"
    }


app.include_router(prediction_router)
