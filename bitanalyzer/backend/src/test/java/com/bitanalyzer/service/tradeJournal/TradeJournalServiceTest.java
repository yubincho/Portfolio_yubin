package com.bitanalyzer.service.tradeJournal;

import com.bitanalyzer.domain.enums.TradeSide;
import com.bitanalyzer.domain.marketSnapshot.MarketSnapshot;
import com.bitanalyzer.domain.tradeJournal.TradeJournal;
import com.bitanalyzer.domain.tradeJournal.repository.TradeJournalRepository;
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
@Import(TradeJournalService.class)  // Service를 테스트에 포함
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)  // @DataJpaTest + 테스트에서도 실제 PostgreSQL을 사용하도록 설정
@ActiveProfiles("dev")  // dev profile 사용 (PostgreSQL 연결)
@Transactional  // @DataJpaTest + 테스트가 끝난 후에 자동으로 Rollback
class TradeJournalServiceTest {

    @Autowired
    private TradeJournalService tradeJournalService;

    @Autowired
    private TradeJournalRepository tradeJournalRepository;


    @Test
    @DisplayName("거래와 시장 스냅샷을 함께 저장하면 정상적으로 저장되어야 한다")
    void saveTradeWithSnapshot_Success() {
        // given
        TradeJournal trade = new TradeJournal();
        trade.setOrderId("test-order-12345");
        trade.setSymbol("BTC");
        trade.setSide(TradeSide.BUY);
        trade.setPrice(new BigDecimal("65000000"));
        trade.setQuantity(new BigDecimal("0.15"));
        trade.setFee(new BigDecimal("9750"));
        trade.setAmount(new BigDecimal("9750000"));
        trade.setRealizedPnl(new BigDecimal("450000"));
        trade.setIsWin(true);
        trade.setExecutedAt(LocalDateTime.now());
        trade.setReason("저점 매수");
        trade.setStrategyTag("swing");

        MarketSnapshot snapshot = new MarketSnapshot();
        snapshot.setRsi(new BigDecimal("32.5"));
        snapshot.setMacd(new BigDecimal("1250.75"));
        snapshot.setBollingerUpper(new BigDecimal("68000000"));
        snapshot.setBollingerLower(new BigDecimal("62000000"));
        snapshot.setVolatility(new BigDecimal("3.85"));
        snapshot.setBtcDominance(new BigDecimal("54.8"));
        snapshot.setBtcPriceAtTime(new BigDecimal("65200000"));
        snapshot.setMarketRegime("BULL");

        // when
        TradeJournal savedTrade = tradeJournalService.saveTradeWithSnapshot(trade, snapshot);

        // then
        assertThat(savedTrade.getId()).isNotNull();
        assertThat(savedTrade.getOrderId()).isEqualTo("test-order-12345");
        assertThat(savedTrade.getRealizedPnl()).isEqualByComparingTo("450000");

        // MarketSnapshot도 함께 저장되었는지 확인
        assertThat(savedTrade.getMarketSnapshot()).isNotNull();
        assertThat(savedTrade.getMarketSnapshot().getBtcDominance())
                .isEqualByComparingTo("54.8");
        assertThat(savedTrade.getMarketSnapshot().getRsi())
                .isEqualByComparingTo("32.5");
        assertThat(savedTrade.getMarketSnapshot().getTradeJournal().getId())
                .isEqualTo(savedTrade.getId());   // 양방향 연관관계 검증
    }


    @Test
    @DisplayName("MarketSnapshot 없이 거래만 저장해도 정상 동작해야 한다")
    void saveTradeWithSnapshot_WithoutSnapshot() {
        // given
        TradeJournal trade = new TradeJournal();
        trade.setOrderId("test-order-67890");
        trade.setSymbol("ETH");
        trade.setSide(TradeSide.SELL);
        trade.setPrice(new BigDecimal("3200000"));
        trade.setQuantity(new BigDecimal("2.5"));
        trade.setRealizedPnl(new BigDecimal("-150000"));
        trade.setIsWin(false);
        trade.setExecutedAt(LocalDateTime.now());

        // when
        TradeJournal savedTrade = tradeJournalService.saveTradeWithSnapshot(trade, null);

        // then
        assertThat(savedTrade.getId()).isNotNull();
        assertThat(savedTrade.getMarketSnapshot()).isNull();
    }

}