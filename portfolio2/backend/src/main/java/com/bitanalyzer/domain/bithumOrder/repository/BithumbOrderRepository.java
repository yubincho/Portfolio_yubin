package com.bitanalyzer.domain.bithumOrder.repository;

import com.bitanalyzer.domain.bithumOrder.BithumbOrder;
import org.springframework.data.jpa.repository.JpaRepository;


public interface BithumbOrderRepository extends JpaRepository<BithumbOrder, Long> {

    /** 이미 저장된 주문인지 확인 (중복 저장 방지) */
    boolean existsByOrderUuid(String orderUuid);
}

