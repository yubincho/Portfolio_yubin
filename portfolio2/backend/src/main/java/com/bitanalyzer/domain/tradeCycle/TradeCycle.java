package com.bitanalyzer.domain.tradeCycle;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.OffsetDateTime;


/**
 * 투자 기간 1회: 0개에서 사기 시작해서 다시 0개가 될 때까지
 * 보유 기간 분석과 "지금 보유 중인 코인"은 이 테이블에서 본다.
 */
@Entity
@Table(name = "trade_cycle", indexes = {
        @Index(name = "idx_trade_cycle_market", columnList = "market")
})
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class TradeCycle {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String market;
    private Integer cycleNo;            // 코인별 1, 2, 3...

    private OffsetDateTime startedAt;   // 처음 산 시각
    private OffsetDateTime endedAt;     // 다 판 시각 (보유 중이면 null)
    private Long holdSeconds;           // 보유 기간 (보유 중이면 null)

    private Integer buyCount;
    private Integer sellCount;

    @Column(precision = 30, scale = 2)
    private BigDecimal totalBuyAmount;

    @Column(precision = 30, scale = 2)
    private BigDecimal totalSellAmount;

    @Column(precision = 30, scale = 2)
    private BigDecimal realizedPnl;

    @Column(precision = 12, scale = 6)
    private BigDecimal returnRate;

    @Column(precision = 30, scale = 8)
    private BigDecimal remainingQuantity;   // 보유 중이면 남은 수량

    @Column(precision = 30, scale = 2)
    private BigDecimal avgBuyPrice;         // 보유 중이면 지금 평균 단가

    private Boolean closed;                 // 다 팔았으면 true
    private Boolean win;                    // 끝난 기간만 (보유 중이면 null)

    @Builder
    private TradeCycle(String market, Integer cycleNo, OffsetDateTime startedAt,
                       OffsetDateTime endedAt, Long holdSeconds, Integer buyCount,
                       Integer sellCount, BigDecimal totalBuyAmount, BigDecimal totalSellAmount,
                       BigDecimal realizedPnl, BigDecimal returnRate, BigDecimal remainingQuantity,
                       BigDecimal avgBuyPrice, Boolean closed, Boolean win) {
        this.market = market;
        this.cycleNo = cycleNo;
        this.startedAt = startedAt;
        this.endedAt = endedAt;
        this.holdSeconds = holdSeconds;
        this.buyCount = buyCount;
        this.sellCount = sellCount;
        this.totalBuyAmount = totalBuyAmount;
        this.totalSellAmount = totalSellAmount;
        this.realizedPnl = realizedPnl;
        this.returnRate = returnRate;
        this.remainingQuantity = remainingQuantity;
        this.avgBuyPrice = avgBuyPrice;
        this.closed = closed;
        this.win = win;
    }
}
