"""
빗썸 기간별 거래내역 엑셀(.xlsx)을 읽어 trade_order_event 테이블에 저장하는 일회성 스크립트.
- 매수/매도 거래만 저장 (입출금, 예치금 이용료 등은 제외)
- UUID가 없으므로 거래 정보로 해시를 만들어 trade_uuid로 사용 (중복 방지)
- source 컬럼에 'EXCEL' 기록
실행: (venv 활성화 후) python -m scripts.import_excel
"""

import sys
import hashlib
from datetime import datetime

import pandas as pd

from app.core.database import get_connection

# ── 설정 ────────────────────────────────────────────
# EXCEL_PATH = "data/20260606.xlsx"   # 엑셀 파일 경로
EXCEL_PATH = "data/20251127.xlsx"
HEADER_ROW = 2                       # 실제 헤더("거래일시"...)가 있는 행 (0부터 시작)

# 엑셀 자산명 → 빗썸 코드 매핑
SYMBOL_MAP = {
    "엑스알피[리플]": "KRW-XRP",
    "테더": "KRW-USDT",
    "도지코인": "KRW-DOGE",
    "비트코인": "KRW-BTC",
}

# 엑셀 거래구분 → ask_bid 매핑
SIDE_MAP = {
    "매수": "BID",
    "매도": "ASK",
}


def clean_number(value):
    """'2,568.0000 KRW', '638.77 XRP' 같은 문자열에서 숫자만 추출."""
    if value is None:
        return None
    text = str(value).strip()
    # 숫자/소수점/마이너스만 남기고 콤마·단위·공백 제거
    cleaned = "".join(ch for ch in text if ch.isdigit() or ch in ".-")
    if cleaned in ("", "-", "."):
        return None
    return float(cleaned)


def to_millis(dt_str):
    """'2026-01-15 04:52:36' → Unix 밀리초(bigint)."""
    dt = datetime.strptime(str(dt_str).strip(), "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp() * 1000)


def make_trade_uuid(traded_at, symbol, side, volume, price):
    """UUID가 없는 엑셀 데이터의 중복 방지용 고유 키 생성."""
    raw = f"{traded_at}|{symbol}|{side}|{volume}|{price}"
    return "EXCEL-" + hashlib.sha256(raw.encode()).hexdigest()[:32]


def main():
    # 1) 엑셀 읽기 (헤더가 3번째 행에 있음)
    df = pd.read_excel(EXCEL_PATH, header=HEADER_ROW)
    print(f"엑셀 전체 행 수: {len(df)}")

    # 2) 매수/매도만 필터링
    df = df[df["거래구분"].isin(["매수", "매도"])].copy()
    print(f"매수/매도 행 수: {len(df)}")

    conn = get_connection()
    cur = conn.cursor()

    inserted, skipped = 0, 0

    for _, row in df.iterrows():
        try:
            traded_at = str(row["거래일시"]).strip()
            asset = str(row["자산"]).strip()
            side_kr = str(row["거래구분"]).strip()

            # 매핑되지 않는 자산은 건너뜀 (혹시 모를 다른 코인 방어)
            if asset not in SYMBOL_MAP:
                print(f"⚠️ 매핑 없는 자산 건너뜀: {asset}")
                skipped += 1
                continue

            code = SYMBOL_MAP[asset]
            ask_bid = SIDE_MAP[side_kr]
            volume = clean_number(row["거래수량"])
            price = clean_number(row["체결가격"])
            fee = clean_number(row["수수료"])
            ts_millis = to_millis(traded_at)

            trade_uuid = make_trade_uuid(traded_at, code, ask_bid, volume, price)

            # 3) 중복 체크
            cur.execute(
                "SELECT 1 FROM trade_order_event WHERE trade_uuid = %s",
                (trade_uuid,),
            )
            if cur.fetchone():
                skipped += 1
                continue

            # 4) INSERT
            cur.execute(
                """
                INSERT INTO trade_order_event
                    (trade_uuid, code, ask_bid, order_type, state,
                     price, volume, executed_volume, paid_fee,
                     order_timestamp, trade_timestamp, stream_type,
                     created_at, source)
                VALUES
                    (%s, %s, %s, %s, %s,
                     %s, %s, %s, %s,
                     %s, %s, %s,
                     %s, %s)
                """,
                (
                    trade_uuid, code, ask_bid, "limit", "done",
                    price, volume, volume, fee,
                    ts_millis, ts_millis, "EXCEL",
                    datetime.now(), "EXCEL",
                ),
            )
            inserted += 1

        except Exception as e:
            print(f"❌ 행 처리 실패: {row.to_dict()} | 오류: {e}")
            skipped += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n⭕ 완료 — 저장: {inserted}건, 건너뜀: {skipped}건")


if __name__ == "__main__":
    main()
