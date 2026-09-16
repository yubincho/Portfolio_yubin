package com.bitanalyzer.domain.tradeJournal;


import com.bitanalyzer.domain.enums.TradeSide;
import com.bitanalyzer.domain.marketSnapshot.MarketSnapshot;
import com.bitanalyzer.domain.user.User;
import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;


@Entity
@Getter
@Setter
@NoArgsConstructor   // (access = AccessLevel.PROTECTED)  테스트를 위해 잠시 보류
@AllArgsConstructor
@Table(name = "trade_journal")
public class TradeJournal {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** 빗썸에서 내려오는 고유 값 */
    @Column(unique = true, nullable = false)
    private String orderId;                    // bithumb order_id 또는 uuid

    @Column(nullable = false)
    private String symbol;                     // BTC, ETH, SOL, XRP...

    @Column(nullable = false)
    @Enumerated(EnumType.STRING)
    private TradeSide side;                    // BUY, SELL

    @Column(nullable = false, precision = 20, scale = 8)
    private BigDecimal price;

    @Column(nullable = false, precision = 20, scale = 8)
    private BigDecimal quantity;

    @Column(precision = 20, scale = 8)
    private BigDecimal fee;

    @Column(precision = 20, scale = 2)
    private BigDecimal amount;                 // price * quantity (체결금액)

    /** 실현 손익 (가장 중요) */
    @Column(precision = 20, scale = 2)
    private BigDecimal realizedPnl;

    /** ML 관련 */
    @Column(precision = 6, scale = 4)
    private BigDecimal predictedWinRate;       // 0.0 ~ 1.0

    @Column(nullable = false)
    private Boolean isWin;                     // 실제 승패 (나중에 업데이트)

    /** 시간 정보 */
    @Column(nullable = false)
    private LocalDateTime executedAt;

    private LocalDateTime closedAt;            // 매도 완료 시간 (Hold Time 계산용)

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /** 분석용 필드 */
    @Column(length = 100)
    private String reason;                     // "저점 매수", "추세 추종" 등

    @Column(length = 500)
    private String memo;

    /** 전략 태그 **/
    @Column(length = 50)
    private String strategyTag;                // "scalping", "swing", "mean-reversion" 등

    /** Hold Time (초) */
    private Long holdTimeSeconds;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    @OneToOne(mappedBy = "tradeJournal", cascade = CascadeType.ALL)
    private MarketSnapshot marketSnapshot;

    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
        if (this.executedAt == null) {
            this.executedAt = LocalDateTime.now();
        }
    }
}
