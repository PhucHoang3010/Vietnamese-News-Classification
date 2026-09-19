FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./alembic.ini

COPY docker/entrypoint.sh ./docker/entrypoint.sh

RUN chmod +x ./docker/entrypoint.sh

COPY models/p2_tfidf_vectorizer.joblib ./models/p2_tfidf_vectorizer.joblib
COPY models/p2_linear_svm_balanced.joblib ./models/p2_linear_svm_balanced.joblib
COPY models/p2_model_metadata.json ./models/p2_model_metadata.json

EXPOSE 8000

CMD ["./docker/entrypoint.sh", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
