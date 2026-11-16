package com.bitanalyzer.domain.tradeSell.repository;

import com.bitanalyzer.domain.tradeSell.TradeSell;
import org.springframework.data.jpa.repository.JpaRepository;


public interface TradeSellRepository extends JpaRepository<TradeSell, Long> {
}