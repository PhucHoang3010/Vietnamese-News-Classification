#!/bin/sh

set -e

echo "Waiting for PostgreSQL..."

until pg_isready -h postgres -p 5432 -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-vietnamese_news}" > /dev/null 2>&1
do
    echo "PostgreSQL is unavailable - waiting..."
    sleep 2
done

echo "PostgreSQL is ready."

echo "Running database migrations..."

alembic upgrade head

echo "Database migrations completed."

echo "Starting FastAPI..."

exec "$@"
