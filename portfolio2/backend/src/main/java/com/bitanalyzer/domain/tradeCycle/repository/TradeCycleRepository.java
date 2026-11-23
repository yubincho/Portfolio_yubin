package com.bitanalyzer.domain.tradeCycle.repository;

import com.bitanalyzer.domain.tradeCycle.TradeCycle;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;


/**
 * 투자 기간(trade_cycle) 조회 + 통계 쿼리
 */
public interface TradeCycleRepository extends JpaRepository<TradeCycle, Long> {

    /** 지금 보유 중인 코인 */
    List<TradeCycle> findByClosedFalseOrderByMarketAsc();


    // ---------- 쿼리 결과를 받는 모양 ----------

    interface CycleSummaryRow {
        Long getClosedCount();
        BigDecimal getAvgHoldSeconds();
    }

    interface HoldPeriodRow {
        Integer getBucket();          // 1: 1일 미만, 2: 1일~1주, 3: 1주~1개월, 4: 1개월 이상
        Long getCycleCount();
        Long getWinCount();
        BigDecimal getRealizedPnl();
        BigDecimal getAvgReturnRate();
    }


    // ---------- 통계 쿼리 ----------
    // 승패가 있는(win IS NOT NULL) 끝난 투자 기간만 본다.
    // 출금만 하고 판 적이 없는 기간은 승패가 없으니까 뺀다.

    /** 끝난 투자 기간 수 + 평균 보유 시간(초) */
    @Query(value = """
            SELECT COUNT(*)          AS "closedCount",
                   AVG(hold_seconds) AS "avgHoldSeconds"
            FROM trade_cycle
            WHERE closed = true AND win IS NOT NULL
              AND ended_at >= :from AND ended_at < :to
            """, nativeQuery = true)
    CycleSummaryRow summarizeClosed(@Param("from") OffsetDateTime from, @Param("to") OffsetDateTime to);

    /** 보유 기간별 승률 */
    @Query(value = """
            SELECT CASE WHEN hold_seconds < 86400   THEN 1
                        WHEN hold_seconds < 604800  THEN 2
                        WHEN hold_seconds < 2592000 THEN 3
                        ELSE 4 END                                 AS "bucket",
                   COUNT(*)                                        AS "cycleCount",
                   COALESCE(SUM(CASE WHEN win THEN 1 ELSE 0 END), 0) AS "winCount",
                   COALESCE(SUM(realized_pnl), 0)                  AS "realizedPnl",
                   COALESCE(AVG(return_rate), 0)                   AS "avgReturnRate"
            FROM trade_cycle
            WHERE closed = true AND win IS NOT NULL
              AND ended_at >= :from AND ended_at < :to
            GROUP BY 1
            ORDER BY 1
            """, nativeQuery = true)
    List<HoldPeriodRow> groupByHoldPeriod(@Param("from") OffsetDateTime from, @Param("to") OffsetDateTime to);

}
