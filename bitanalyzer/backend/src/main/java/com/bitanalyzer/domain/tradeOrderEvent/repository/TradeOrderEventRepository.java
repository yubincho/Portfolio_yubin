package com.bitanalyzer.domain.tradeOrderEvent.repository;

import com.bitanalyzer.domain.tradeOrderEvent.TradeOrderEvent;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;


public interface TradeOrderEventRepository extends JpaRepository<TradeOrderEvent, Long> {

    // 체결 중복 방지용: 이미 저장된 trade_uuid인지 확인
    boolean existsByTradeUuid(String tradeUuid);

    Optional<TradeOrderEvent> findByTradeUuid(String tradeUuid);
}
