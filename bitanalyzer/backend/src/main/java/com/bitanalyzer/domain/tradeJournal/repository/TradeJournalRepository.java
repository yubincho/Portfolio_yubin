package com.bitanalyzer.domain.tradeJournal.repository;


import com.bitanalyzer.domain.tradeJournal.TradeJournal;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.List;


public interface TradeJournalRepository extends JpaRepository<TradeJournal, Long> {

    Optional<TradeJournal> findByOrderId(String orderId);

    List<TradeJournal> findByUserIdOrderByExecutedAtDesc(Long userId);

    List<TradeJournal> findTop30ByUserIdOrderByExecutedAtDesc(Long userId);

    List<TradeJournal> findBySymbolAndExecutedAtBetween(
            String symbol, LocalDateTime from, LocalDateTime to);

    /** 승률 계산용 */
    @Query("SELECT COUNT(t) FROM TradeJournal t WHERE t.user.id = :userId AND t.isWin = true")
    Long countWinTrades(@Param("userId") Long userId);

    @Query("SELECT COUNT(t) FROM TradeJournal t WHERE t.user.id = :userId")
    Long countTotalTrades(@Param("userId") Long userId);

    /** 기간별 조회 */
    List<TradeJournal> findByUserIdAndExecutedAtBetween(Long userId, LocalDateTime from, LocalDateTime to);
}
