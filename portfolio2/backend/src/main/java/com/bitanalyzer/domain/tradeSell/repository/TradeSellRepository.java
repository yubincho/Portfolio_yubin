package com.bitanalyzer.domain.tradeSell.repository;

import com.bitanalyzer.domain.tradeSell.TradeSell;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;

/**
 * 매도 손익(trade_sell) 조회 + 통계 쿼리
 *
 * - 통계는 DB가 직접 계산하도록 SQL(GROUP BY)로 작성했다.
 * - sold_at은 UTC로 저장돼 있어서, 요일·시간·월을 뽑을 때는 한국 시간으로 바꿔줌. (AT TIME ZONE 'Asia/Seoul')
 * - 별칭에 큰따옴표("sellCount")를 붙인 이유: PostgreSQL은 따옴표가 없으면 별칭을 소문자(sellcount)로 바꿔서
 *   아래 인터페이스의 getSellCount()와 이름이 안 맞게 됨.
 */
public interface TradeSellRepository extends JpaRepository<TradeSell, Long> {

    /** 최근 매도 (최신순) */
    List<TradeSell> findAllByOrderBySoldAtDesc(Pageable pageable);


    // ---------- 쿼리 결과를 받는 모양 ----------

    interface SummaryRow {
        Long getSellCount();
        Long getWinCount();
        BigDecimal getRealizedPnl();
        BigDecimal getCostAmount();
        BigDecimal getFeeKrw();
    }

    /** 코인별, 월별처럼 "글자"로 묶는 통계 */
    interface TextGroupRow {
        String getGroupKey();
        Long getSellCount();
        Long getWinCount();
        BigDecimal getRealizedPnl();
        BigDecimal getCostAmount();
    }

    /** 요일별, 시간대별처럼 "숫자"로 묶는 통계 */
    interface NumberGroupRow {
        Integer getGroupKey();
        Long getSellCount();
        Long getWinCount();
        BigDecimal getRealizedPnl();
        BigDecimal getCostAmount();
    }


    // ---------- 통계 쿼리 ----------

    /** 전체 요약: 매도 수, 이긴 수, 실현 손익, 원가 합계, 수수료 */
    @Query(value = """
            SELECT COUNT(*)                                        AS "sellCount",
                   COALESCE(SUM(CASE WHEN win THEN 1 ELSE 0 END), 0) AS "winCount",
                   COALESCE(SUM(realized_pnl), 0)                  AS "realizedPnl",
                   COALESCE(SUM(cost_amount), 0)                   AS "costAmount",
                   COALESCE(SUM(fee_krw), 0)                       AS "feeKrw"
            FROM trade_sell
            WHERE sold_at >= :from AND sold_at < :to
            """, nativeQuery = true)
    SummaryRow summarize(@Param("from") OffsetDateTime from, @Param("to") OffsetDateTime to);

    /** 코인별 */
    @Query(value = """
            SELECT market                                          AS "groupKey",
                   COUNT(*)                                        AS "sellCount",
                   COALESCE(SUM(CASE WHEN win THEN 1 ELSE 0 END), 0) AS "winCount",
                   COALESCE(SUM(realized_pnl), 0)                  AS "realizedPnl",
                   COALESCE(SUM(cost_amount), 0)                   AS "costAmount"
            FROM trade_sell
            WHERE sold_at >= :from AND sold_at < :to
            GROUP BY market
            ORDER BY "realizedPnl" DESC
            """, nativeQuery = true)
    List<TextGroupRow> groupByMarket(@Param("from") OffsetDateTime from, @Param("to") OffsetDateTime to);

    /** 월별 (한국 시간 기준, 예: 2026-03) */
    @Query(value = """
            SELECT TO_CHAR(sold_at AT TIME ZONE 'Asia/Seoul', 'YYYY-MM') AS "groupKey",
                   COUNT(*)                                        AS "sellCount",
                   COALESCE(SUM(CASE WHEN win THEN 1 ELSE 0 END), 0) AS "winCount",
                   COALESCE(SUM(realized_pnl), 0)                  AS "realizedPnl",
                   COALESCE(SUM(cost_amount), 0)                   AS "costAmount"
            FROM trade_sell
            WHERE sold_at >= :from AND sold_at < :to
            GROUP BY 1
            ORDER BY 1
            """, nativeQuery = true)
    List<TextGroupRow> groupByMonth(@Param("from") OffsetDateTime from, @Param("to") OffsetDateTime to);

    /** 요일별 (한국 시간 기준, 1=월요일 ~ 7=일요일) */
    @Query(value = """
            SELECT CAST(EXTRACT(ISODOW FROM sold_at AT TIME ZONE 'Asia/Seoul') AS INTEGER) AS "groupKey",
                   COUNT(*)                                        AS "sellCount",
                   COALESCE(SUM(CASE WHEN win THEN 1 ELSE 0 END), 0) AS "winCount",
                   COALESCE(SUM(realized_pnl), 0)                  AS "realizedPnl",
                   COALESCE(SUM(cost_amount), 0)                   AS "costAmount"
            FROM trade_sell
            WHERE sold_at >= :from AND sold_at < :to
            GROUP BY 1
            ORDER BY 1
            """, nativeQuery = true)
    List<NumberGroupRow> groupByWeekday(@Param("from") OffsetDateTime from, @Param("to") OffsetDateTime to);

    /** 시간대별 (한국 시간 기준, 0 ~ 23시) */
    @Query(value = """
            SELECT CAST(EXTRACT(HOUR FROM sold_at AT TIME ZONE 'Asia/Seoul') AS INTEGER) AS "groupKey",
                   COUNT(*)                                        AS "sellCount",
                   COALESCE(SUM(CASE WHEN win THEN 1 ELSE 0 END), 0) AS "winCount",
                   COALESCE(SUM(realized_pnl), 0)                  AS "realizedPnl",
                   COALESCE(SUM(cost_amount), 0)                   AS "costAmount"
            FROM trade_sell
            WHERE sold_at >= :from AND sold_at < :to
            GROUP BY 1
            ORDER BY 1
            """, nativeQuery = true)
    List<NumberGroupRow> groupByHour(@Param("from") OffsetDateTime from, @Param("to") OffsetDateTime to);

}