package com.bitanalyzer.domain.bithumbWithdraw.repository;


import com.bitanalyzer.domain.bithumbWithdraw.BithumbWithdraw;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;


public interface BithumbWithdrawRepository extends JpaRepository<BithumbWithdraw, Long> {

    boolean existsByWithdrawUuid(String withdrawUuid);

    List<BithumbWithdraw> findByState(String state);
}
