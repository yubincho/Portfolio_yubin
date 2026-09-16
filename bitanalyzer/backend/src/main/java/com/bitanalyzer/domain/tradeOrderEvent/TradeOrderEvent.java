package com.bitanalyzer.domain.tradeOrderEvent;


import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;


/**
 * 웹소켓 -> "myOrder" 구독 신청 후 받은 메시지
 * "myOrder" 원본 이벤트 테이블 (WebSocket 으로 오는 걸 가공 없이 그대로 저장, 빗썸 필드와 1:1로 매칭)
 * OrderHistory & 임시 저장 테이블
 * 이 myOrder raw 데이터를(TradeOrderEvent 테이블) 가공해서 TradeJournal로 만듦
 * (예) 빗썸에서 지정가 매수/매도 "주문"을 취소하는 경우도 (웹소켓으로 받은 메시지를) 손익 없이 그대로 저장함
 * */
@Entity
@Table(name = "trade_order_event")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor
public class TradeOrderEvent {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true)
    private String tradeUuid;       // trade_uuid (체결 고유 ID) - 중복 방지용

    private String orderUuid;       // uuid (주문 고유 ID)
    private String code;            // KRW-XRP
    private String askBid;          // ASK(매도) / BID(매수)
    private String orderType;       // limit, price, market
    private String state;           // wait, trade, done, cancel

    @Column(precision = 20, scale = 8)
    private BigDecimal price;

    @Column(precision = 20, scale = 8)
    private BigDecimal volume;          // 주문량

    @Column(precision = 20, scale = 8)
    private BigDecimal remainingVolume;

    @Column(precision = 20, scale = 8)
    private BigDecimal executedVolume;  // 체결량

    @Column(precision = 20, scale = 8)
    private BigDecimal paidFee;

    private Long orderTimestamp;
    private Long tradeTimestamp;

    private String streamType;    // REALTIME / SNAPSHOT

    private LocalDateTime createdAt;

    private String source;      // websocket, excel

    // id, createdAt 제외하고 받음
    @Builder
    private TradeOrderEvent(String orderUuid, String tradeUuid, String code,
                            String askBid, String orderType, String state,
                            BigDecimal price, BigDecimal volume,
                            BigDecimal remainingVolume, BigDecimal executedVolume,
                            BigDecimal paidFee, Long orderTimestamp,
                            Long tradeTimestamp, String streamType) {
        this.orderUuid = orderUuid;
        this.tradeUuid = tradeUuid;
        this.code = code;
        this.askBid = askBid;
        this.orderType = orderType;
        this.state = state;
        this.price = price;
        this.volume = volume;
        this.remainingVolume = remainingVolume;
        this.executedVolume = executedVolume;
        this.paidFee = paidFee;
        this.orderTimestamp = orderTimestamp;
        this.tradeTimestamp = tradeTimestamp;
        this.streamType = streamType;
    }


    @PrePersist
    void onCreate() { this.createdAt = LocalDateTime.now(); }
}
