"""
리뷰 API의 요청/응답 "모양"
- 스키마 (Pydantic)

TradeReview는 LLM에게 "이 모양으로만 답해"라고 알려주는 틀이기도 해요.
Gemini가 이 모양에 맞춰 JSON으로 답하고, 우리는 그걸 그대로 검증해서 써요.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator


class ReviewRequest(BaseModel):
    """Spring이 보내는 요청: 리뷰할 기간 (한국 시간, 양 끝 포함)"""
    from_date: date = Field(description="시작일 (예: 2026-01-01)")
    to_date: date = Field(description="종료일 (예: 2026-06-30)")

    @model_validator(mode="after")
    def check_period(self):
        if self.from_date > self.to_date:
            raise ValueError("from_date는 to_date보다 늦을 수 없어요")
        return self


class TradeReview(BaseModel):
    """LLM이 채워야 하는 리뷰 틀"""
    headline: str = Field(description="기간 전체를 한 문장으로 요약 (40자 이내)")
    strengths: list[str] = Field(description="잘한 점 1~3개. 반드시 숫자 근거를 포함")
    weaknesses: list[str] = Field(description="아쉬운 점 1~3개. 반드시 숫자 근거를 포함")
    suggestions: list[str] = Field(description="다음 매매를 위한 구체적인 제안 1~3개")


class ReviewResponse(BaseModel):
    """Spring에게 돌려주는 응답"""
    from_date: date
    to_date: date
    sell_count: int
    review: TradeReview | None          # 매도가 없으면 리뷰 없음
    message: str | None = None          # 리뷰가 없을 때 이유
    model: str | None = None            # 어떤 LLM으로 만들었는지
    prompt_version: str | None = None   # 어떤 프롬프트로 만들었는지
    generated_at: datetime
