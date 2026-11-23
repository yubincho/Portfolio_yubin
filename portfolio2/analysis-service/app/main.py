"""
analysis-service (FastAPI)

실행 (analysis-service 폴더에서):
  uv run uvicorn app.main:app --reload --port 8000

API 문서(직접 눌러서 테스트 가능): http://localhost:8000/docs
"""

import logging

from fastapi import FastAPI

from app.routers import review

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="BitAnalyzer analysis-service", version="0.1.0")
app.include_router(review.router)


@app.get("/health")
def health() -> dict:
    """서버가 살아 있는지 확인용"""
    return {"status": "ok"}