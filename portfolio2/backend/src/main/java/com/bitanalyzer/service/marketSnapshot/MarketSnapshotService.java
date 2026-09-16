package com.bitanalyzer.service.marketSnapshot;


import com.bitanalyzer.domain.marketSnapshot.MarketSnapshot;
import com.bitanalyzer.domain.marketSnapshot.repository.MarketSnapshotRepository;
import com.bitanalyzer.domain.tradeJournal.TradeJournal;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;


@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class MarketSnapshotService {

    private final MarketSnapshotRepository marketSnapshotRepository;

    @Transactional
    public MarketSnapshot save(MarketSnapshot marketSnapshot, TradeJournal tradeJournal) {
        if (tradeJournal != null) {
            marketSnapshot.setTradeJournal(tradeJournal);
            tradeJournal.setMarketSnapshot(marketSnapshot);   // 양방향 설정
        }
        return marketSnapshotRepository.save(marketSnapshot);
    }



}
