package com.bitanalyzer.dto;


import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.OffsetDateTime;

/**
 * 통계 API 응답 모양 모음
 *
 * - record: 값을 담기만 하는 간단한 클래스 (Java 16+)
 * - 비율은 화면에서 바로 쓰기 쉽게 퍼센트(58.33 = 58.33%)로 준다. 이름 끝에 Pct가 붙은 것들.
 */
public class StatsDto {

    private StatsDto() {}

    /** 대시보드 위쪽 요약 카드 */
    public record Summary(
            LocalDate from,
            LocalDate to,
            long sellCount,              // 매도 횟수
            long winCount,               // 이긴 매도 횟수
            BigDecimal winRatePct,       // 승률 (%)
            BigDecimal realizedPnl,      // 실현 손익 (원)
            BigDecimal returnRatePct,    // 수익률 (%) = 실현 손익 ÷ 판 수량의 원가
            BigDecimal feeKrw,           // 낸 수수료 (원)
            long closedCycleCount,       // 끝난 투자 기간 수
            BigDecimal avgHoldHours      // 평균 보유 시간 (시간)
    ) {}

    /** 코인별·월별·요일별·시간대별 통계 한 줄 */
    public record GroupStat(
            String key,                  // KRW-XRP, 2026-03, 1(월요일), 9(9시)
            String label,                // 화면 표시용: XRP, 2026년 3월, 월, 9시
            long sellCount,
            BigDecimal winRatePct,
            BigDecimal realizedPnl,
            BigDecimal returnRatePct
    ) {}

    /** 보유 기간별 통계 한 줄 */
    public record HoldPeriodStat(
            String label,                // 1일 미만, 1일~1주, 1주~1개월, 1개월 이상
            long cycleCount,
            BigDecimal winRatePct,
            BigDecimal realizedPnl,
            BigDecimal avgReturnRatePct
    ) {}

    /** 최근 매도 한 건 */
    public record RecentTrade(
            String market,
            OffsetDateTime soldAt,
            BigDecimal quantity,
            BigDecimal avgBuyPrice,
            BigDecimal sellPrice,
            BigDecimal realizedPnl,
            BigDecimal returnRatePct,
            Boolean win
    ) {}

    /** 지금 보유 중인 코인 */
    public record Position(
            String market,
            BigDecimal quantity,
            BigDecimal avgBuyPrice,
            OffsetDateTime startedAt,
            int buyCount
    ) {}
}
