package com.bitanalyzer.service.tradeJournal;


import com.bitanalyzer.domain.marketSnapshot.MarketSnapshot;
import com.bitanalyzer.domain.marketSnapshot.repository.MarketSnapshotRepository;
import com.bitanalyzer.domain.tradeJournal.TradeJournal;
import com.bitanalyzer.domain.tradeJournal.repository.TradeJournalRepository;

import com.bitanalyzer.exception.BitAnalyzerException;
import com.bitanalyzer.exception.enums.ErrorCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;


@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class TradeJournalService {

    private final TradeJournalRepository tradeJournalRepository;
    private final MarketSnapshotRepository marketSnapshotRepository;

    @Transactional
    public TradeJournal saveTradeWithSnapshot(TradeJournal tradeJournal, MarketSnapshot marketSnapshot) {
        TradeJournal savedTrade = tradeJournalRepository.save(tradeJournal);

        if (marketSnapshot != null) {
            marketSnapshot.setTradeJournal(savedTrade);
            savedTrade.setMarketSnapshot(marketSnapshot);  // 양방향 연관관계
            marketSnapshotRepository.save(marketSnapshot);
        }

        return savedTrade;
    }

    public List<TradeJournal> getRecentTrades(Long userId, int limit) {
        return tradeJournalRepository.findTop30ByUserIdOrderByExecutedAtDesc(userId);
    }

    public TradeJournal findByOrderId(String orderId) {
        return tradeJournalRepository.findByOrderId(orderId)
                .orElseThrow(() -> new BitAnalyzerException(ErrorCode.TRADE_NOT_FOUND,
                        "orderId: " + orderId));
    }

    /** 승률 계산  (퍼센트) */
    public double getWinRate(Long userId) {
        Long wins = tradeJournalRepository.countWinTrades(userId);
        Long total = tradeJournalRepository.countTotalTrades(userId);
        return total == 0 ? 0.0 : Math.round((wins * 100.0 / total) * 100) / 100.0; // 소수점 2자리 반올림
    }

    /** 기간별 거래 조회 */
    public List<TradeJournal> getTradesByPeriod(Long userId, LocalDateTime from, LocalDateTime to) {
        return tradeJournalRepository.findByUserIdAndExecutedAtBetween(userId, from, to);
    }

    // websocket - 메시지 수신
    public void processWebSocketMessage(String payload) {
        // JSON 파싱 후 TradeJournal 생성 및 저장 로직
        //  JSON 파싱 → TradeJournal 변환 → 저장 로직을 나중에 구현
        log.info("WebSocket 메시지 수신: {}", payload);

        try {
            // 여기서 JSON 파싱 → TradeJournal 변환 → 저장 로직을 나중에 구현
            log.info("[WebSocket → Service] 메시지 수신 완료. 길이: {} bytes", payload.length());

            // 임시로 콘솔에 출력 (테스트용)
            System.out.println("=== WebSocket 데이터 ===");
            System.out.println(payload);
            System.out.println("========================");

        } catch (Exception e) {
            log.error("WebSocket 메시지 처리 실패", e);
        }
    }
}
