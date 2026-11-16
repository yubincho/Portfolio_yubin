package com.bitanalyzer.domain.tradeSell;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.OffsetDateTime;


/**
 * 매도 1건의 손익 (평균 단가 방식)
 * 승률, 코인별·요일별·월별 손익은 이 테이블에서 계산한다.
 */
@Entity
@Table(name = "trade_sell", indexes = {
        @Index(name = "idx_trade_sell_market", columnList = "market"),
        @Index(name = "idx_trade_sell_sold_at", columnList = "soldAt")
})
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class TradeSell {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String market;              // KRW-XRP
    private String sellOrderUuid;       // 빗썸 매도 주문 ID
    private Integer cycleNo;            // 몇 번째 투자 기간의 매도인지

    @Column(precision = 30, scale = 8)
    private BigDecimal quantity;

    @Column(precision = 30, scale = 2)
    private BigDecimal avgBuyPrice;     // 팔 때의 평균 단가 (수수료 포함)

    @Column(precision = 30, scale = 2)
    private BigDecimal sellPrice;       // 코인 1개당 받은 금액 (수수료 뺀 값)

    @Column(precision = 30, scale = 2)
    private BigDecimal costAmount;      // 판 수량의 원가

    @Column(precision = 30, scale = 2)
    private BigDecimal sellAmount;      // 받은 금액

    @Column(precision = 30, scale = 2)
    private BigDecimal feeKrw;          // 수수료 (원화 환산)

    @Column(precision = 30, scale = 2)
    private BigDecimal realizedPnl;     // 실현 손익

    @Column(precision = 12, scale = 6)
    private BigDecimal returnRate;      // 수익률 (0.1 = 10%)

    private OffsetDateTime soldAt;
    private Boolean win;

    @Builder
    private TradeSell(String market, String sellOrderUuid, Integer cycleNo, BigDecimal quantity,
                      BigDecimal avgBuyPrice, BigDecimal sellPrice, BigDecimal costAmount,
                      BigDecimal sellAmount, BigDecimal feeKrw, BigDecimal realizedPnl,
                      BigDecimal returnRate, OffsetDateTime soldAt, Boolean win) {
        this.market = market;
        this.sellOrderUuid = sellOrderUuid;
        this.cycleNo = cycleNo;
        this.quantity = quantity;
        this.avgBuyPrice = avgBuyPrice;
        this.sellPrice = sellPrice;
        this.costAmount = costAmount;
        this.sellAmount = sellAmount;
        this.feeKrw = feeKrw;
        this.realizedPnl = realizedPnl;
        this.returnRate = returnRate;
        this.soldAt = soldAt;
        this.win = win;
    }
}
