package com.bitanalyzer.domain.assetSnapshot;


import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 웹소켓 -> "myAsset" 구독 신청 후 받은 메시지
 * "myAsset" 원본 이벤트 테이블 (WebSocket 으로 오는 걸 가공 없이 그대로 저장, 빗썸 필드와 1:1로 매칭)
 * 임시 저장 테이블
 * */
@Entity
@Table(name = "asset_snapshot")
@Getter @Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AssetSnapshot {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** 자산 종류 (심볼) - currency 필드에서 옴 (KRW, XRP, BTC...) */
    @Column(nullable = false)
    private String currency;

    /** 사용 가능 잔고 */
    @Column(precision = 30, scale = 8)
    private BigDecimal balance;

    /** 주문에 묶인 수량 */
    @Column(precision = 30, scale = 8)
    private BigDecimal locked;

    /** 빗썸이 준 자산 변동 시각 (ms) */
    private Long assetTimestamp;

    private String streamType;   // REALTIME / SNAPSHOT

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    // id, createdAt 제외하고 받음
    @Builder
    private AssetSnapshot(String currency, BigDecimal balance, BigDecimal locked,
                          Long assetTimestamp, String streamType) {
        this.currency = currency;
        this.balance = balance;
        this.locked = locked;
        this.assetTimestamp = assetTimestamp;
        this.streamType = streamType;
    }

    @PrePersist
    void onCreate() {
        this.createdAt = LocalDateTime.now();
    }

}
