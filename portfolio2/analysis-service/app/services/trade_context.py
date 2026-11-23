"""
리뷰 재료 만들기 (pandas)

DB에서 기간 안의 매도(trade_sell)와 끝난 투자 기간(trade_cycle)을 읽어서
LLM에게 줄 "요약 숫자"를 만들어.

Spring 통계 API와 겹치는 숫자(승률, 코인별 손익)도 있지만,
여기서는 SQL로 하기 번거로운 것들을 pandas로 더 계산.
  - 최대 연승 / 최대 연패
  - 가장 크게 번 매매 / 가장 크게 잃은 매매
  - 이긴 매매와 진 매매의 평균 수익률 차이
"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from app.core.database import get_connection

KST = ZoneInfo("Asia/Seoul")
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
HOLD_BUCKETS = [(86400, "1일 미만"), (604800, "1일~1주"), (2592000, "1주~1개월"), (float("inf"), "1개월 이상")]


# ---------- DB 읽기 ----------

def _query(sql: str, params: tuple) -> pd.DataFrame:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        columns = [c.name for c in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=columns)


def load_trades(from_date: date, to_date: date) -> tuple[pd.DataFrame, pd.DataFrame]:
    """기간(한국 시간, 양 끝 포함) 안의 매도와 끝난 투자 기간"""
    start = datetime.combine(from_date, time.min, tzinfo=KST)
    end = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=KST)

    sells = _query(
        """
        SELECT market, sold_at, realized_pnl, cost_amount, return_rate, fee_krw, win
        FROM trade_sell
        WHERE sold_at >= %s AND sold_at < %s
        ORDER BY sold_at
        """,
        (start, end),
    )
    cycles = _query(
        """
        SELECT market, hold_seconds, realized_pnl, return_rate, win
        FROM trade_cycle
        WHERE closed = true AND win IS NOT NULL
          AND ended_at >= %s AND ended_at < %s
        """,
        (start, end),
    )
    return sells, cycles


# ---------- 계산 (DB 없이 테스트할 수 있게 분리) ----------

def _pct(numerator: float, denominator: float) -> float:
    return round(float(numerator) * 100 / float(denominator), 2) if denominator else 0.0


def _won(value) -> int:
    """원 단위 정수 (numpy 숫자를 일반 숫자로 바꿔서 JSON으로 보낼 수 있게)"""
    return int(round(float(value)))


def _plain(value):
    """numpy 숫자(np.int64 등) → 일반 파이썬 숫자"""
    return value.item() if hasattr(value, "item") else value


def _max_streak(wins: pd.Series, value: bool) -> int:
    """연속으로 이긴(또는 진) 최대 횟수"""
    best = current = 0
    for w in wins:
        current = current + 1 if w == value else 0
        best = max(best, current)
    return best


def _group(df: pd.DataFrame, key: str) -> list[dict]:
    g = df.groupby(key, sort=True).agg(
        sell_count=("win", "size"),
        win_count=("win", "sum"),
        pnl=("realized_pnl", "sum"),
        cost=("cost_amount", "sum"),
    )
    return [
        {
            key: _plain(idx),
            "sell_count": int(r.sell_count),
            "win_rate_pct": _pct(r.win_count, r.sell_count),
            "realized_pnl": _won(r.pnl),
            "return_rate_pct": _pct(float(r.pnl), float(r.cost)),
        }
        for idx, r in g.iterrows()
    ]


def build_context(sells: pd.DataFrame, cycles: pd.DataFrame) -> dict:
    """LLM에게 줄 요약 숫자. 매도가 없으면 sell_count = 0 만 돌려줘."""
    if sells.empty:
        return {"sell_count": 0}

    sells = sells.copy()
    for col in ["realized_pnl", "cost_amount", "return_rate", "fee_krw"]:
        sells[col] = sells[col].astype(float)
    sells["win"] = sells["win"].astype(bool)

    local = pd.to_datetime(sells["sold_at"], utc=True).dt.tz_convert(KST)
    sells["coin"] = sells["market"].str.replace("KRW-", "", regex=False)
    sells["weekday"] = local.dt.dayofweek.map(lambda d: WEEKDAYS[d])
    sells["hour"] = local.dt.hour

    wins = sells[sells["win"]]
    losses = sells[~sells["win"]]
    best = sells.loc[sells["realized_pnl"].idxmax()]
    worst = sells.loc[sells["realized_pnl"].idxmin()]

    context = {
        "sell_count": int(len(sells)),
        "win_rate_pct": _pct(len(wins), len(sells)),
        "realized_pnl": _won(sells["realized_pnl"].sum()),
        "return_rate_pct": _pct(sells["realized_pnl"].sum(), sells["cost_amount"].sum()),
        "fee_krw": _won(sells["fee_krw"].sum()),
        "avg_win_return_pct": round(float(wins["return_rate"].mean()) * 100, 2) if len(wins) else None,
        "avg_loss_return_pct": round(float(losses["return_rate"].mean()) * 100, 2) if len(losses) else None,
        "max_win_streak": _max_streak(sells["win"], True),
        "max_loss_streak": _max_streak(sells["win"], False),
        "best_trade": {"coin": best["coin"], "realized_pnl": _won(best["realized_pnl"]),
                       "return_rate_pct": round(float(best["return_rate"]) * 100, 2)},
        "worst_trade": {"coin": worst["coin"], "realized_pnl": _won(worst["realized_pnl"]),
                        "return_rate_pct": round(float(worst["return_rate"]) * 100, 2)},
        "by_coin": sorted(_group(sells, "coin"), key=lambda r: r["realized_pnl"], reverse=True),
        "by_weekday": sorted(_group(sells, "weekday"), key=lambda r: WEEKDAYS.index(r["weekday"])),
        "by_hour": _group(sells, "hour"),
    }

    if not cycles.empty:
        cycles = cycles.copy()
        cycles["hold_seconds"] = cycles["hold_seconds"].astype(float)
        cycles["realized_pnl"] = cycles["realized_pnl"].astype(float)
        cycles["win"] = cycles["win"].astype(bool)
        cycles["hold_period"] = cycles["hold_seconds"].map(
            lambda s: next(label for limit, label in HOLD_BUCKETS if s < limit))
        context["by_hold_period"] = [
            {
                "hold_period": label,
                "cycle_count": int((g := cycles[cycles["hold_period"] == label]).shape[0]),
                "win_rate_pct": _pct(g["win"].sum(), len(g)),
                "realized_pnl": _won(g["realized_pnl"].sum()),
            }
            for _, label in HOLD_BUCKETS
            if (cycles["hold_period"] == label).any()
        ]

    return context
