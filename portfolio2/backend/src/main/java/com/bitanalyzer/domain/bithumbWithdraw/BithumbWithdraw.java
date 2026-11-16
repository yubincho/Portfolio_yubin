package com.bitanalyzer.domain.bithumbWithdraw;


import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;


/**
 * 빗썸 코인 출금 1건 (해외 거래소, 개인 지갑 등으로 보낸 기록)
 * 손익 계산에서 "판 게 아니라 다른 곳으로 옮긴 것"으로 처리.
 */
@Entity
@Table(name = "bithumb_withdraw")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class BithumbWithdraw {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** 빗썸 출금 고유 ID - 중복 저장 방지용 */
    @Column(nullable = false, unique = true)
    private String withdrawUuid;

    private String currency;            // USDT
    private String state;               // DONE

    @Column(precision = 30, scale = 8)
    private BigDecimal amount;          // 받는 쪽으로 간 수량

    @Column(precision = 30, scale = 8)
    private BigDecimal fee;             // 출금 수수료 (코인)

    private OffsetDateTime createdAt;   // 출금 요청 시각 (이때 잔고에서 빠져요)
    private OffsetDateTime doneAt;      // 출금 완료 시각

    @Column(columnDefinition = "text")
    private String rawJson;

    private LocalDateTime savedAt;

    @Builder
    private BithumbWithdraw(String withdrawUuid, String currency, String state,
                            BigDecimal amount, BigDecimal fee,
                            OffsetDateTime createdAt, OffsetDateTime doneAt, String rawJson) {
        this.withdrawUuid = withdrawUuid;
        this.currency = currency;
        this.state = state;
        this.amount = amount;
        this.fee = fee;
        this.createdAt = createdAt;
        this.doneAt = doneAt;
        this.rawJson = rawJson;
    }

    @PrePersist
    void onCreate() {
        this.savedAt = LocalDateTime.now();
    }
}