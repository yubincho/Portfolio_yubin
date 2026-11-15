package com.bitanalyzer.temp.predictionLog;

import com.bitanalyzer.temp.socket.tradeJournal.TradeJournal;
import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;


/**
 * ML 예측 기록
 * **/
@Entity
@Getter @Setter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Table(name = "prediction_log")
public class PredictionLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "trade_journal_id")
    private TradeJournal tradeJournal;

    private BigDecimal predictedWinRate;

    private Boolean actualResult;        // true = 승, false = 패

    private LocalDateTime predictedAt;

    @PrePersist
    protected void onCreate() {
        this.predictedAt = LocalDateTime.now();
    }
}
