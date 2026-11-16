package com.bitanalyzer.domain.bithumOrder;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;


/**
 * 빗썸 REST API(/v1/orders)로 가져온 "완료된 주문" 1건
 *
 * - trade_order_event: 웹소켓으로 받은 "사건" 기록 (접수, 체결, 취소가 각각 한 줄)
 * - bithumb_order    : REST API로 받은 "주문" 기록 (주문 하나가 한 줄)
 */
@Entity
@Table(name = "bithumb_order")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class BithumbOrder {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** 빗썸 주문 고유 ID (uuid) - 중복 저장 방지용 */
    @Column(nullable = false, unique = true)
    private String orderUuid;

    private String market;          // KRW-XRP
    private String side;            // bid(매수) / ask(매도)
    private String orderType;       // limit(지정가), price(시장가 매수), market(시장가 매도)
    private String state;           // done

    @Column(precision = 30, scale = 8)
    private BigDecimal price;       // 주문 가격 (지정가) 또는 주문 총액 (시장가 매수)

    @Column(precision = 30, scale = 8)
    private BigDecimal volume;      // 주문 수량

    @Column(precision = 30, scale = 8)
    private BigDecimal remainingVolume;

    @Column(precision = 30, scale = 8)
    private BigDecimal executedVolume;  // 실제 체결된 수량

    @Column(precision = 30, scale = 8)
    private BigDecimal paidFee;     // 낸 수수료

    @Column(precision = 30, scale = 8)
    private BigDecimal executedFunds;   // 실제로 오간 금액 (원)

    private Integer tradesCount;    // 몇 번에 나눠 체결됐는지

    private OffsetDateTime orderedAt;   // 주문 시각 (빗썸 created_at)

    /** 빗썸이 준 원본 JSON 통째로 (나중에 필요한 필드가 생기면 여기서 꺼내 쓰기) */
    @Column(columnDefinition = "text")
    private String rawJson;

    private LocalDateTime savedAt;  // 우리 DB에 저장한 시각

    @Builder
    private BithumbOrder(String orderUuid, String market, String side, String orderType,
                         String state, BigDecimal price, BigDecimal volume,
                         BigDecimal remainingVolume, BigDecimal executedVolume,
                         BigDecimal executedFunds, BigDecimal paidFee, Integer tradesCount,
                         OffsetDateTime orderedAt, String rawJson) {
        this.orderUuid = orderUuid;
        this.market = market;
        this.side = side;
        this.orderType = orderType;
        this.state = state;
        this.price = price;
        this.volume = volume;
        this.remainingVolume = remainingVolume;
        this.executedVolume = executedVolume;
        this.executedFunds = executedFunds;
        this.paidFee = paidFee;
        this.tradesCount = tradesCount;
        this.orderedAt = orderedAt;
        this.rawJson = rawJson;
    }

    @PrePersist
    void onCreate() {
        this.savedAt = LocalDateTime.now();
    }
}
