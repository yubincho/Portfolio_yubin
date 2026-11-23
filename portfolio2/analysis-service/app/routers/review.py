"""
리뷰 API

POST /review  {"from_date": "2026-01-01", "to_date": "2026-06-30"}
"""

from fastapi import APIRouter, HTTPException

from app.schemas.review import ReviewRequest, ReviewResponse
from app.services.review_service import LlmUnavailableError, create_review

router = APIRouter(tags=["review"])


@router.post("/review", response_model=ReviewResponse)
def review(req: ReviewRequest) -> ReviewResponse:
    try:
        return create_review(req)
    except LlmUnavailableError as e:
        # 503: "지금은 서비스를 쓸 수 없어요" → Spring이 이걸 보고 대체 응답을 보여줘요
        raise HTTPException(status_code=503, detail=f"AI 리뷰를 만들 수 없어요: {e}") from e

