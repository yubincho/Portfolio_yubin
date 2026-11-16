package com.bitanalyzer.service;

import com.bitanalyzer.domain.averageCostCalculator.AverageCostCalculator;
import com.bitanalyzer.domain.bithumOrder.BithumbOrder;
import com.bitanalyzer.domain.bithumOrder.repository.BithumbOrderRepository;
import com.bitanalyzer.domain.tradeCycle.TradeCycle;
import com.bitanalyzer.domain.tradeCycle.repository.TradeCycleRepository;
import com.bitanalyzer.domain.tradeSell.TradeSell;
import com.bitanalyzer.domain.tradeSell.repository.TradeSellRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;


/**
 * bithumb_order → (평균 단가 계산) → trade_sell, trade_cycle
 *
 * 매번 "전부 지우고 처음부터 다시 계산"한다.
 * 주문이 수백 건 정도라 금방 끝나고, 항상 정확한 결과가 나오게 됨.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class TradePnlService {

    private final BithumbOrderRepository bithumbOrderRepository;
    private final TradeSellRepository tradeSellRepository;
    private final TradeCycleRepository tradeCycleRepository;
    private final AverageCostCalculator calculator = new AverageCostCalculator();

    @Transactional
    public AverageCostCalculator.Result rebuild() {
        List<AverageCostCalculator.Fill> fills = bithumbOrderRepository.findAll().stream()
                .filter(o -> "done".equals(o.getState()))
                .map(this::toFill)
                .toList();

        AverageCostCalculator.Result result = calculator.calculate(fills);

        tradeSellRepository.deleteAllInBatch();
        tradeCycleRepository.deleteAllInBatch();
        tradeSellRepository.saveAll(result.sells().stream().map(this::toEntity).toList());
        tradeCycleRepository.saveAll(result.cycles().stream().map(this::toEntity).toList());

        result.warnings().forEach(w -> log.warn("⚠️ {}", w));
        log.info("⭕ 손익 계산 완료 — 매도: {}건, 투자 기간: {}건, 경고: {}건",
                result.sells().size(), result.cycles().size(), result.warnings().size());
        return result;
    }

    private AverageCostCalculator.Fill toFill(BithumbOrder o) {
        return new AverageCostCalculator.Fill(o.getOrderUuid(), o.getMarket(), o.getSide(),
                o.getExecutedVolume(), o.getExecutedFunds(), o.getPaidFee(), o.getOrderedAt());
    }

    private TradeSell toEntity(AverageCostCalculator.Sell s) {
        return TradeSell.builder()
                .market(s.market())
                .sellOrderUuid(s.sellOrderUuid())
                .cycleNo(s.cycleNo())
                .quantity(s.quantity())
                .avgBuyPrice(s.avgBuyPrice())
                .sellPrice(s.sellPrice())
                .costAmount(s.costAmount())
                .sellAmount(s.sellAmount())
                .feeKrw(s.feeKrw())
                .realizedPnl(s.realizedPnl())
                .returnRate(s.returnRate())
                .soldAt(s.soldAt())
                .win(s.win())
                .build();
    }

    private TradeCycle toEntity(AverageCostCalculator.Cycle c) {
        return TradeCycle.builder()
                .market(c.market())
                .cycleNo(c.cycleNo())
                .startedAt(c.startedAt())
                .endedAt(c.endedAt())
                .holdSeconds(c.holdSeconds())
                .buyCount(c.buyCount())
                .sellCount(c.sellCount())
                .totalBuyAmount(c.totalBuyAmount())
                .totalSellAmount(c.totalSellAmount())
                .realizedPnl(c.realizedPnl())
                .returnRate(c.returnRate())
                .remainingQuantity(c.remainingQuantity())
                .avgBuyPrice(c.avgBuyPrice())
                .closed(c.closed())
                .win(c.win())
                .build();
    }
}
