package com.bitanalyzer.domain.marketSnapshot.repository;


import com.bitanalyzer.domain.marketSnapshot.MarketSnapshot;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;


public interface MarketSnapshotRepository extends JpaRepository<MarketSnapshot, Long> {

    Optional<MarketSnapshot> findByTradeJournalId(Long tradeJournalId);
}
