package com.bitanalyzer.temp.socket.assetSnapshot.repository;

import com.bitanalyzer.temp.socket.assetSnapshot.AssetSnapshot;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;


public interface AssetSnapshotRepository extends JpaRepository<AssetSnapshot, Long> {

    Optional<AssetSnapshot> findTopByCurrencyOrderByCreatedAtDesc(String currency);

}
