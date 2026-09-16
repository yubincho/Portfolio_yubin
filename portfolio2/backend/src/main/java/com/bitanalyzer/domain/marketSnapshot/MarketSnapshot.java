package com.bitanalyzer.domain.marketSnapshot;


import com.bitanalyzer.domain.tradeJournal.TradeJournal;
import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;


/**
 * 시장 상황 지표
 * **/
@Entity
@Table(name = "market_snapshot")
@Getter @Setter
@NoArgsConstructor  // // (access = AccessLevel.PROTECTED)  테스트를 위해 잠시 보류
@AllArgsConstructor
public class MarketSnapshot {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "trade_journal_id")
    private TradeJournal tradeJournal;

    // 시장 상황 지표
    private BigDecimal rsi;
    private BigDecimal macd;
    private BigDecimal bollingerUpper;
    private BigDecimal bollingerMiddle;
    private BigDecimal bollingerLower;
    private BigDecimal volatility;           // 최근 1시간 변동성 (%)
    private BigDecimal btcDominance;         // ← CoinGecko API 로 받기
    private BigDecimal fundingRate;          // 선물 시장일 경우

    private BigDecimal btcPriceAtTime;       // 당시 BTC 가격 (참조용)

    @Column(length = 30)
    private String marketRegime;             // BULL, BEAR, SIDEWAYS, VOLATILE

    private LocalDateTime snapshotAt;

    @PrePersist
    void onCreate() {
        this.snapshotAt = LocalDateTime.now();
    }

}
