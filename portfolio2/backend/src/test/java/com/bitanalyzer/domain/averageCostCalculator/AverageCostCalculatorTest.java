package com.bitanalyzer.domain.averageCostCalculator;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;


/**
 * 평균 단가 손익 계산기 단위 테스트
 * Spring을 띄우지 않아서 아주 빨라. (DB, 빗썸 연결 필요 없음)
 */
class AverageCostCalculatorTest {

    private final AverageCostCalculator calculator = new AverageCostCalculator();

    @Test
    @DisplayName("평균 단가로 손익 계산: 500원 100개 + 600원 100개 → 평균 550원")
    void averageCost() {
        AverageCostCalculator.Result r = calculator.calculate(List.of(
                fill("A", "bid", "100", "50000", "0", 1),
                fill("B", "bid", "100", "60000", "0", 3),
                fill("S1", "ask", "150", "105000", "0", 5),   // 700원에 150개
                fill("S2", "ask", "50", "35000", "0", 7)      // 700원에 50개
        ));

        AverageCostCalculator.Sell first = r.sells().get(0);
        assertThat(first.avgBuyPrice()).isEqualByComparingTo("550");
        assertThat(first.realizedPnl()).isEqualByComparingTo("22500");

        AverageCostCalculator.Sell second = r.sells().get(1);
        assertThat(second.avgBuyPrice()).isEqualByComparingTo("550");   // 팔아도 평균 단가는 그대로
        assertThat(second.realizedPnl()).isEqualByComparingTo("7500");
    }

    @Test
    @DisplayName("다 팔면 투자 기간 1회 종료: 총 손익과 보유 기간 계산")
    void cycleCloses() {
        AverageCostCalculator.Result r = calculator.calculate(List.of(
                fill("A", "bid", "100", "50000", "0", 1),
                fill("B", "bid", "100", "60000", "0", 3),
                fill("S1", "ask", "150", "105000", "0", 5),
                fill("S2", "ask", "50", "35000", "0", 7)
        ));

        assertThat(r.cycles()).hasSize(1);
        AverageCostCalculator.Cycle c = r.cycles().get(0);
        assertThat(c.closed()).isTrue();
        assertThat(c.realizedPnl()).isEqualByComparingTo("30000");
        assertThat(c.holdSeconds()).isEqualTo(6 * 24 * 3600);   // 1일 → 7일
        assertThat(c.buyCount()).isEqualTo(2);
        assertThat(c.sellCount()).isEqualTo(2);
        assertThat(c.win()).isTrue();
    }

    @Test
    @DisplayName("다 판 뒤 다시 사면 새 투자 기간이 시작되고, 보유 중으로 남는다")
    void newCycleAfterClose() {
        AverageCostCalculator.Result r = calculator.calculate(List.of(
                fill("A", "bid", "10", "10000", "0", 1),
                fill("S", "ask", "10", "8000", "0", 2),     // 손해
                fill("B", "bid", "10", "9000", "0", 4)
        ));

        assertThat(r.cycles()).hasSize(2);

        AverageCostCalculator.Cycle first = r.cycles().get(0);
        assertThat(first.realizedPnl()).isEqualByComparingTo("-2000");
        assertThat(first.win()).isFalse();

        AverageCostCalculator.Cycle second = r.cycles().get(1);
        assertThat(second.cycleNo()).isEqualTo(2);
        assertThat(second.closed()).isFalse();
        assertThat(second.remainingQuantity()).isEqualByComparingTo("10");
        assertThat(second.avgBuyPrice()).isEqualByComparingTo("900");   // 새 기간은 새 평균 단가
    }

    @Test
    @DisplayName("원화 수수료: 매수는 원가에 더하고, 매도는 받은 금액에서 뺀다")
    void krwFee() {
        AverageCostCalculator.Result r = calculator.calculate(List.of(
                fill("A", "bid", "100", "100000", "150", 1),
                fill("S", "ask", "100", "110000", "165", 2)
        ));

        AverageCostCalculator.Sell s = r.sells().get(0);
        assertThat(s.costAmount()).isEqualByComparingTo("100150");
        assertThat(s.sellAmount()).isEqualByComparingTo("109835");
        assertThat(s.realizedPnl()).isEqualByComparingTo("9685");
        assertThat(s.feeKrw()).isEqualByComparingTo("315");
    }

    @Test
    @DisplayName("코인 수수료(예전 빗썸): 받은 코인 수량에서 수수료만큼 빠진다")
    void coinFee() {
        // 실제 데이터: 0.0003 BTC를 861원에 사고 수수료 0.00000045 BTC
        AverageCostCalculator.Result r = calculator.calculate(List.of(
                fill("A", "bid", "0.0003", "861", "0.00000045", 1),
                fill("S", "ask", "0.00029955", "900", "0", 2)
        ));

        AverageCostCalculator.Sell s = r.sells().get(0);
        assertThat(s.quantity()).isEqualByComparingTo("0.00029955");
        assertThat(s.costAmount()).isEqualByComparingTo("861");
        assertThat(r.warnings()).isEmpty();
    }

    @Test
    @DisplayName("산 기록보다 더 팔면 가진 만큼만 계산하고 경고를 남긴다")
    void sellMoreThanHeld() {
        AverageCostCalculator.Result r = calculator.calculate(List.of(
                fill("A", "bid", "10", "10000", "0", 1),
                fill("S", "ask", "15", "15000", "0", 2)
        ));

        assertThat(r.sells().get(0).quantity()).isEqualByComparingTo("10");
        assertThat(r.sells().get(0).sellAmount()).isEqualByComparingTo("10000");   // 15000원 중 10개 몫
        assertThat(r.warnings()).hasSize(1);
    }

    // --- 테스트용  ---
    private AverageCostCalculator.Fill fill(String uuid, String side, String volume, String funds, String fee, int day) {
        return new AverageCostCalculator.Fill(uuid, "KRW-XRP", side, new BigDecimal(volume), new BigDecimal(funds),
                new BigDecimal(fee), OffsetDateTime.parse(String.format("2025-01-%02dT10:00:00+09:00", day)));
    }
}