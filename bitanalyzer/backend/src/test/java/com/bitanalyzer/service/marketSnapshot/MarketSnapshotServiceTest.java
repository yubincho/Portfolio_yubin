package com.bitanalyzer.service.marketSnapshot;

import com.bitanalyzer.domain.enums.TradeSide;
import com.bitanalyzer.domain.marketSnapshot.MarketSnapshot;
import com.bitanalyzer.domain.tradeJournal.TradeJournal;
import com.bitanalyzer.domain.tradeJournal.repository.TradeJournalRepository;
import com.bitanalyzer.service.tradeJournal.TradeJournalService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assertions.*;
import static org.assertj.core.api.Assertions.assertThat;


@DataJpaTest
@Import({MarketSnapshotService.class, TradeJournalService.class})
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@ActiveProfiles("dev")
@Transactional
class MarketSnapshotServiceTest {

    @Autowired
    private MarketSnapshotService marketSnapshotService;

    @Autowired
    private TradeJournalService tradeJournalService;

    @Autowired
    private TradeJournalRepository tradeJournalRepository;

    @Test
    @DisplayName("MarketSnapshot을 정상적으로 저장하고 TradeJournal과 연관관계가 제대로 맺어져야 한다")
    void saveMarketSnapshot_Success() {
//        “TradeJournal은 Snapshot 없이 먼저 저장한 뒤,
//        MarketSnapshot을 별도로 저장하면서 TradeJournal과 연관관계를 맺었을 때,
//                양방향 연관관계(TradeJournal ↔ MarketSnapshot)가 제대로 설정되는가?”

        // given - 먼저 TradeJournal 저장
        // 매번 실행할 때마다 중복되지 않는(unique) 값을 만들어서 orderId를 생성 -> 타임스탬프를 붙임
        String uniqueOrderId = "snapshot-test-" + System.currentTimeMillis();

        TradeJournal trade = new TradeJournal();
//        trade.setOrderId("snapshot-test-" + System.currentTimeMillis());
        trade.setOrderId(uniqueOrderId);
        trade.setSymbol("BTC");
        trade.setSide(TradeSide.BUY);
        trade.setPrice(new BigDecimal("67000000"));
        trade.setQuantity(new BigDecimal("0.1"));
        trade.setRealizedPnl(new BigDecimal("320000"));
        trade.setIsWin(true);
        trade.setExecutedAt(LocalDateTime.now());
        trade.setReason("추세 매수");

        TradeJournal savedTrade = tradeJournalService.saveTradeWithSnapshot(trade, null);

        // ----------------------------------------------------------
        // hardcoding된 값과 비교
        BigDecimal expectedBtcDominance = new BigDecimal("55.3");
        BigDecimal expectedRsi = new BigDecimal("35.8");

        MarketSnapshot snapshot = new MarketSnapshot();
        snapshot.setRsi(expectedRsi);
        snapshot.setMacd(new BigDecimal("980.4"));
        snapshot.setBollingerUpper(new BigDecimal("71000000"));
        snapshot.setBollingerLower(new BigDecimal("64000000"));
        snapshot.setVolatility(new BigDecimal("4.75"));
        snapshot.setBtcDominance(expectedBtcDominance);
        snapshot.setBtcPriceAtTime(new BigDecimal("67780000"));
        snapshot.setMarketRegime("BULL");

        // when
        MarketSnapshot savedSnapshot = marketSnapshotService.save(snapshot, savedTrade);

        // then
        assertThat(savedSnapshot.getId()).isNotNull();
        assertThat(savedSnapshot.getRsi()).isEqualByComparingTo("35.8");
        assertThat(savedSnapshot.getBtcDominance()).isEqualByComparingTo("55.3");
        assertThat(savedSnapshot.getMarketRegime()).isEqualTo("BULL");

        // 양방향 연관관계 검증
        assertThat(savedSnapshot.getTradeJournal().getId()).isEqualTo(savedTrade.getId());
        assertThat(savedTrade.getMarketSnapshot()).isNotNull();
        assertThat(savedTrade.getMarketSnapshot().getId()).isEqualTo(savedSnapshot.getId());

        assertThat(savedSnapshot.getBtcDominance()).isEqualByComparingTo(expectedBtcDominance);
        assertThat(savedSnapshot.getRsi()).isEqualByComparingTo(expectedRsi);
        assertThat(savedSnapshot.getMarketRegime()).isEqualTo("BULL");
    }

}