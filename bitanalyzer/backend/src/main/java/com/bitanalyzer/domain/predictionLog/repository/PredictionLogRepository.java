package com.bitanalyzer.domain.predictionLog.repository;

import com.bitanalyzer.domain.predictionLog.PredictionLog;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;


public interface PredictionLogRepository extends JpaRepository<PredictionLog, Long> {

    List<PredictionLog> findByTradeJournalId(Long tradeJournalId);
}
