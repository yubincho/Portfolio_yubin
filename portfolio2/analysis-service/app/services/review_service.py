"""
LLM 매매 리뷰 만들기

흐름: DB에서 매매 읽기 → pandas로 요약 숫자 만들기 → 프롬프트에 넣기 → Gemini 호출 → 정해진 모양(TradeReview)으로 받기

LLM 회사를 바꾸고 싶으면 _call_llm() 함수만 바꾸면 돼요.
모델이 바쁘면(503) 다음 모델로 자동으로 넘어가요. (GEMINI_MODELS 순서대로)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from google import genai

from app.core.config import GEMINI_API_KEY, GEMINI_MODELS
from app.schemas.review import ReviewRequest, ReviewResponse, TradeReview
from app.services.trade_context import build_context, load_trades

log = logging.getLogger(__name__)

PROMPT_VERSION = "review_v1"
PROMPT_TEMPLATE = (Path(__file__).parent.parent / "prompts" / f"{PROMPT_VERSION}.md").read_text(encoding="utf-8")

# 모델 하나당 최대 대기 시간. 이 시간이 지나면 포기하고 다음 모델로 넘어가요.
LLM_TIMEOUT_SECONDS = 30

_client = (
    genai.Client(api_key=GEMINI_API_KEY, http_options={"timeout": LLM_TIMEOUT_SECONDS * 1000})  # 밀리초 단위
    if GEMINI_API_KEY else None
)


class LlmUnavailableError(Exception):
    """LLM을 부를 수 없거나 응답이 이상할 때"""


def create_review(req: ReviewRequest) -> ReviewResponse:
    sells, cycles = load_trades(req.from_date, req.to_date)
    context = build_context(sells, cycles)
    now = datetime.now(ZoneInfo("Asia/Seoul"))

    # 매도가 없으면 LLM을 부르지 않아요 (돈과 시간 아끼기)
    if context["sell_count"] == 0:
        return ReviewResponse(from_date=req.from_date, to_date=req.to_date, sell_count=0,
                              review=None, message="이 기간에는 매도 기록이 없어요.", generated_at=now)

    prompt = PROMPT_TEMPLATE.format(
        from_date=req.from_date, to_date=req.to_date,
        context=json.dumps(context, ensure_ascii=False, indent=2),
    )
    review, used_model = _call_llm(prompt)

    return ReviewResponse(from_date=req.from_date, to_date=req.to_date,
                          sell_count=context["sell_count"], review=review,
                          model=used_model, prompt_version=PROMPT_VERSION, generated_at=now)


# 이 에러들은 "다른 모델로 다시 해 보면 될 수도 있는" 에러예요.
#   404: 이 모델을 쓸 수 없음 / 429: 무료 사용량 초과 / 500, 503: Google 서버가 바쁘거나 일시 오류
RETRYABLE_CODES = {404, 429, 500, 503}


def _call_llm(prompt: str) -> tuple[TradeReview, str]:
    """GEMINI_MODELS를 앞에서부터 시도해요. 성공하면 (리뷰, 쓴 모델 이름)을 돌려줘요."""
    if _client is None:
        raise LlmUnavailableError(".env에 GEMINI_API_KEY가 없어요")

    last_error = "사용할 모델이 없어요 (.env의 GEMINI_MODELS 확인)"
    for model in GEMINI_MODELS:
        log.info("Gemini %s 호출 시작 (최대 %d초)", model, LLM_TIMEOUT_SECONDS)
        try:
            response = _client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": TradeReview,   # 이 모양으로만 답하게 강제
                    "temperature": 0.4,               # 낮을수록 차분하고 일관된 답
                },
            )
        except Exception as e:
            code = getattr(e, "code", None)
            timed_out = "timeout" in type(e).__name__.lower()   # 시간 초과도 다음 모델로
            last_error = f"{model}: {'시간 초과' if timed_out else e}"
            if code in RETRYABLE_CODES or timed_out:
                log.warning("Gemini %s 실패(%s) → 다음 모델 시도", model, "시간 초과" if timed_out else code)
                continue
            log.warning("Gemini 호출 실패: %s", e)   # 키가 틀렸거나(401/403) 요청 자체가 잘못된 경우
            raise LlmUnavailableError(last_error) from e

        if response.parsed is None:
            log.warning("Gemini %s 응답이 정해진 모양이 아니에요: %s", model, response.text)
            last_error = f"{model}: 응답 형식 오류"
            continue

        log.info("Gemini 리뷰 생성 성공 (모델: %s)", model)
        return response.parsed, model

    raise LlmUnavailableError(last_error)