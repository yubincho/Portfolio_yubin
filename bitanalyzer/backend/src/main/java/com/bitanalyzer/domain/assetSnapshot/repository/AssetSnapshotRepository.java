package com.bitanalyzer.domain.assetSnapshot.repository;

import com.bitanalyzer.domain.assetSnapshot.AssetSnapshot;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;


public interface AssetSnapshotRepository extends JpaRepository<AssetSnapshot, Long> {

    Optional<AssetSnapshot> findTopByCurrencyOrderByCreatedAtDesc(String currency);

}
