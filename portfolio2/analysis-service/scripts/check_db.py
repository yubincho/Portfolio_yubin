"""
DB 연결 확인 스크립트

확인하는 것:
  1. .env의 접속 정보로 PostgreSQL에 연결되는지
  2. 어떤 계정(analyst?)으로, 어떤 DB(dev?)에 연결됐는지
  3. 분석에 쓸 테이블들을 읽을 수 있는지 (몇 건인지)
  4. 쓰기(삭제)가 막혀 있는지  ← 읽기 전용 계정 확인

[실행] analysis-service 폴더에서
  uv run python -m scripts.check_db
"""

import psycopg2

from app.core.config import DB_CONFIG
from app.core.database import get_connection

TABLES = ["bithumb_order", "bithumb_withdraw", "trade_sell", "trade_cycle"]


def main():
    print(f"접속 정보: host={DB_CONFIG['host']} port={DB_CONFIG['port']} "
          f"db={DB_CONFIG['dbname']} user={DB_CONFIG['user']}")

    if not DB_CONFIG["dbname"] or not DB_CONFIG["user"]:
        print("❌ .env에서 DB_NAME 또는 DB_USER를 못 읽었어요. .env 파일 위치와 이름을 확인해 주세요.")
        return

    # 1. 연결
    try:
        conn = get_connection()
    except psycopg2.OperationalError as e:
        print("❌ 연결 실패:", e)
        return
    print("✅ 연결 성공")

    with conn:
        with conn.cursor() as cur:
            # 2. 누구로, 어디에
            cur.execute("SELECT current_user, current_database()")
            user, db = cur.fetchone()
            print(f"✅ 계정: {user} / DB: {db}")
            if user != "analyst":
                print("⚠️ analyst가 아니에요. .env의 DB_USER를 확인해 주세요.")

            # 3. 테이블 읽기
            for table in TABLES:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    print(f"✅ {table}: {cur.fetchone()[0]}건")
                except psycopg2.Error as e:
                    print(f"❌ {table} 읽기 실패: {e.pgerror or e}")
                    conn.rollback()   # 에러가 나면 다음 쿼리를 위해 되돌리기

            # 4. 쓰기가 막혀 있는지
            #    WHERE false 라서 postgres 계정이어도 실제로 지워지는 줄은 0개예요.
            try:
                cur.execute("DELETE FROM trade_sell WHERE false")
                print("⚠️ 삭제 권한이 있어요! 읽기 전용 계정이 아니에요.")
            except psycopg2.errors.InsufficientPrivilege:
                print("✅ 삭제는 막혀 있어요 (읽기 전용 계정 정상)")
            finally:
                conn.rollback()

    conn.close()


if __name__ == "__main__":
    main()