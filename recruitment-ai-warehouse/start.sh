#!/usr/bin/env sh
# SERVICE=api  : chỉ chạy FastAPI (cổng $PORT, mặc định 8000)
# SERVICE=web  : chỉ chạy Streamlit (cổng $PORT, mặc định 8501)
# SERVICE=all  : chạy cả hai trong 1 container (API nội bộ 8000, web công khai $PORT)
set -e
SERVICE="${SERVICE:-all}"
case "$SERVICE" in
  api)
    exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers ;;
  web)
    exec streamlit run frontend/app.py --server.port "${PORT:-8501}" --server.address 0.0.0.0 ;;
  *)
    uvicorn app.main:app --host 127.0.0.1 --port 8000 &
    export API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
    exec streamlit run frontend/app.py --server.port "${PORT:-8501}" --server.address 0.0.0.0 ;;
esac
