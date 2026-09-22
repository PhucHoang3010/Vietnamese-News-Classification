from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes.prediction import router as prediction_router
from src.api.routes.analytics import router as analytics_router
from src.api.routes.crawler_control import router as crawler_router
from src.api.routes.intelligence import router as intelligence_router
from src.db.database import check_db_connection
from src.predictor.predictor import VietnameseNewsPredictor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize shared application resources once at startup.
    """
    app.state.predictor = VietnameseNewsPredictor()

    yield

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



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
)
async def health():
    """
    Check API and PostgreSQL database availability.

    Returns HTTP 200 only when the database is reachable.
    Returns HTTP 500 when the database connection fails.
    """
    database_ok = await check_db_connection()

    if not database_ok:
        return JSONResponse(
            status_code=500,
            content={
                "status": "ERROR",
                "service": "Vietnamese News Classification API",
                "database": "UNAVAILABLE",
            },
        )

    return {
        "status": "OK",
        "service": "Vietnamese News Classification API",
        "database": "OK",
    }


app.include_router(prediction_router)
app.include_router(analytics_router)
app.include_router(crawler_router)
app.include_router(intelligence_router)





