package com.bitanalyzer.domain.averageCostCalculator;

import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.time.Duration;
import java.time.OffsetDateTime;
import java.util.*;


/**
 * 평균 단가(이동평균법) 손익 계산기 — 빗썸 앱의 "매수평균가"와 같은 방식
 *
 *  매수: 평균 단가 = (기존 원가 합계 + 새로 산 금액) ÷ 전체 수량
 *  매도: 손익 = (판 가격 − 평균 단가) × 판 수량   ← 팔아도 평균 단가는 그대로
 *  출금: 손익 없이 수량만 줄어요 (판 게 아니라 다른 곳으로 옮긴 것) ← 평균 단가는 그대로
 *  수량이 0(또는 아주 조금)이 되면: 투자 기간(사이클) 1회 끝
 *
 * 출금은 side = "withdraw", executedVolume = 출금 수량 + 출금 수수료 로 넣으면 된다.
 *
 * Spring, DB와 상관없는 "순수 계산"이라 단위 테스트로 바로 검증할 수 있다.
 *
 * 수수료 처리:
 *  - 매수 수수료가 원화면 원가에 더하고, 코인이면 받은 수량에서 빼. (예전 빗썸 방식)
 *  - 매도 수수료는 원화로 바꿔서 판 금액에서 빼.
 */
public class AverageCostCalculator {

    private static final MathContext MC = new MathContext(20, RoundingMode.HALF_UP);
    private static final double TYPICAL_FEE_RATE = 0.0015;

    /** 남은 코인 가치가 이 금액(원)보다 작으면 "다 판 것"으로 본다. (수수료 때문에 남는 아주 작은 잔량) */
    static final BigDecimal DUST_KRW = new BigDecimal("1000");

    /** 계산에 넣는 주문 1건 */
    public record Fill(String orderUuid, String market, String side,
                       BigDecimal executedVolume, BigDecimal executedFunds,
                       BigDecimal paidFee, OffsetDateTime orderedAt) {}

    /** 매도 1건의 손익 */
    public record Sell(String market, String sellOrderUuid, int cycleNo,
                       BigDecimal quantity,
                       BigDecimal avgBuyPrice,   // 팔 때의 평균 단가 (수수료 포함)
                       BigDecimal sellPrice,     // 코인 1개당 받은 금액 (수수료 뺀 값)
                       BigDecimal costAmount,    // 판 수량의 원가 = 평균 단가 × 수량
                       BigDecimal sellAmount,    // 받은 금액 (수수료 뺀 값)
                       BigDecimal feeKrw,        // 이 매도에 들어간 수수료 (매수 몫 + 매도)
                       BigDecimal realizedPnl, BigDecimal returnRate,
                       OffsetDateTime soldAt, boolean win) {}

    /** 투자 기간 1회: 0개에서 사기 시작해서 다시 0개가 될 때까지 */
    public record Cycle(String market, int cycleNo,
                        OffsetDateTime startedAt, OffsetDateTime endedAt,   // 보유 중이면 endedAt = null
                        Long holdSeconds,
                        int buyCount, int sellCount,
                        int withdrawCount,              // 출금 횟수
                        BigDecimal withdrawnQuantity,   // 출금으로 빠져나간 수량 (수수료 포함)
                        BigDecimal totalBuyAmount,      // 이 기간에 산 금액 합계
                        BigDecimal totalSellAmount,     // 이 기간에 받은 금액 합계
                        BigDecimal realizedPnl,
                        BigDecimal returnRate,          // 실현 손익 ÷ 판 수량의 원가
                        BigDecimal remainingQuantity,   // 보유 중이면 남은 수량
                        BigDecimal avgBuyPrice,         // 보유 중이면 지금 평균 단가
                        boolean closed,
                        Boolean win) {}                 // 판 적이 없으면(출금만 했으면) null

    public record Result(List<Sell> sells, List<Cycle> cycles, List<String> warnings) {}

    /** 코인 하나의 현재 보유 상태 */
    private static class Position {
        BigDecimal qty = BigDecimal.ZERO;
        BigDecimal totalCost = BigDecimal.ZERO;   // 남은 수량의 원가 합계
        BigDecimal totalBuyFee = BigDecimal.ZERO; // 남은 수량에 들어간 매수 수수료 (원화)

        BigDecimal avgCost() {
            return qty.signum() == 0 ? BigDecimal.ZERO : totalCost.divide(qty, MC);
        }

        boolean isEmpty() {
            return qty.signum() <= 0 || qty.multiply(avgCost(), MC).compareTo(DUST_KRW) < 0;
        }
    }

    /** 진행 중인 투자 기간의 누적값 */
    private static class CycleAcc {
        final int no;
        final OffsetDateTime startedAt;
        int buyCount, sellCount, withdrawCount;
        BigDecimal withdrawnQty = BigDecimal.ZERO;
        BigDecimal buyAmount = BigDecimal.ZERO;
        BigDecimal sellAmount = BigDecimal.ZERO;
        BigDecimal soldCost = BigDecimal.ZERO;
        BigDecimal pnl = BigDecimal.ZERO;

        CycleAcc(int no, OffsetDateTime startedAt) {
            this.no = no;
            this.startedAt = startedAt;
        }
    }

    public Result calculate(List<Fill> fills) {
        List<Sell> sells = new ArrayList<>();
        List<Cycle> cycles = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        // 코인별로 나누고 시간 순서대로 정렬
        Map<String, List<Fill>> byMarket = new TreeMap<>();
        for (Fill f : fills) {
            if (f.executedVolume() == null || f.executedVolume().signum() <= 0) continue;
            if (f.orderedAt() == null) {   // 시각이 없으면 순서를 정할 수 없다.
                warnings.add(f.market() + " " + f.orderUuid() + ": 시각 정보가 없어서 계산에서 제외");
                continue;
            }
            byMarket.computeIfAbsent(f.market(), k -> new ArrayList<>()).add(f);
        }

        for (Map.Entry<String, List<Fill>> entry : byMarket.entrySet()) {
            String market = entry.getKey();
            List<Fill> list = entry.getValue();
            list.sort(Comparator.comparing(Fill::orderedAt).thenComparing(Fill::orderUuid));

            Position pos = new Position();
            CycleAcc cycle = null;
            int cycleNo = 0;

            for (Fill f : list) {
                BigDecimal volume = f.executedVolume();
                BigDecimal funds = nz(f.executedFunds());
                BigDecimal fee = nz(f.paidFee());
                BigDecimal avgPrice = funds.divide(volume, MC);
                boolean coinFee = isCoinUnitFee(fee, volume, funds);
                BigDecimal feeKrw = coinFee ? fee.multiply(avgPrice, MC) : fee;

                if ("bid".equals(f.side())) {
                    // 비어 있던 상태에서 사면 새 투자 기간 시작
                    if (cycle == null) {
                        cycle = new CycleAcc(++cycleNo, f.orderedAt());
                    }
                    BigDecimal qty = coinFee ? volume.subtract(fee) : volume;
                    BigDecimal cost = coinFee ? funds : funds.add(fee);

                    pos.qty = pos.qty.add(qty);
                    pos.totalCost = pos.totalCost.add(cost);
                    pos.totalBuyFee = pos.totalBuyFee.add(feeKrw);

                    cycle.buyCount++;
                    cycle.buyAmount = cycle.buyAmount.add(cost);

                } else if ("ask".equals(f.side())) {
                    if (pos.qty.signum() <= 0) {
                        warnings.add(market + " 매도 " + f.orderUuid() + ": 보유 수량 없이 판 기록 " + plain(volume));
                        continue;
                    }
                    // cycle == null 인데 수량이 있으면: 끝난 투자 기간의 아주 작은 잔량을 판 경우
                    int sellCycleNo = (cycle != null) ? cycle.no : cycleNo;

                    BigDecimal q = pos.qty.min(volume);   // 가진 것보다 많이 팔았으면 가진 만큼만 계산
                    BigDecimal excess = volume.subtract(q);
                    if (excess.multiply(avgPrice, MC).compareTo(DUST_KRW) >= 0) {   // 1,000원 미만 차이는 무시
                        warnings.add(market + " 매도 " + f.orderUuid() + ": 매수 기록 없이 판 수량 " + plain(excess));
                    }

                    BigDecimal avgCost = pos.avgCost();
                    BigDecimal ratio = q.divide(volume, MC);               // 계산에 포함되는 비율
                    BigDecimal sellAmount = funds.subtract(feeKrw).multiply(ratio, MC);
                    BigDecimal costAmount = q.multiply(avgCost, MC);
                    BigDecimal pnl = sellAmount.subtract(costAmount);
                    BigDecimal buyFeeShare = pos.totalBuyFee.multiply(q.divide(pos.qty, MC), MC);
                    BigDecimal sellFeeShare = feeKrw.multiply(ratio, MC);

                    sells.add(new Sell(market, f.orderUuid(), sellCycleNo, q,
                            money(avgCost), money(sellAmount.divide(q, MC)),
                            money(costAmount), money(sellAmount),
                            money(buyFeeShare.add(sellFeeShare)),
                            money(pnl), rate(pnl, costAmount),
                            f.orderedAt(), pnl.signum() > 0));

                    // 평균 단가는 그대로, 수량과 원가만 줄어든다.
                    pos.qty = pos.qty.subtract(q);
                    pos.totalCost = pos.totalCost.subtract(costAmount);
                    pos.totalBuyFee = pos.totalBuyFee.subtract(buyFeeShare);

                    if (cycle == null) continue;   // 잔량 매도는 이미 끝난 투자 기간에 더하지 않음

                    cycle.sellCount++;
                    cycle.sellAmount = cycle.sellAmount.add(sellAmount);
                    cycle.soldCost = cycle.soldCost.add(costAmount);
                    cycle.pnl = cycle.pnl.add(pnl);

                    // 다 팔았으면(또는 아주 조금만 남았으면) 투자 기간 종료
                    if (pos.isEmpty()) {
                        cycles.add(closedCycle(market, cycle, f.orderedAt()));
                        cycle = null;
                        // 아주 작은 잔량은 버리지 않고 다음 투자 기간 원가에 그대로 남겨 둬.
                    }

                } else if ("withdraw".equals(f.side())) {
                    // 출금: 판 게 아니라 다른 곳으로 옮긴 것 → 손익 없이 수량과 원가만 줄인자.
                    if (pos.qty.signum() <= 0) {
                        warnings.add(market + " 출금 " + f.orderUuid() + ": 보유 수량 없이 출금한 기록 " + plain(volume));
                        continue;
                    }
                    BigDecimal q = pos.qty.min(volume);
                    if (volume.compareTo(q) > 0) {
                        warnings.add(market + " 출금 " + f.orderUuid() + ": 매수 기록보다 많이 출금한 수량 " + plain(volume.subtract(q)));
                    }

                    BigDecimal share = q.divide(pos.qty, MC);
                    pos.totalCost = pos.totalCost.subtract(pos.totalCost.multiply(share, MC));
                    pos.totalBuyFee = pos.totalBuyFee.subtract(pos.totalBuyFee.multiply(share, MC));
                    pos.qty = pos.qty.subtract(q);

                    if (cycle == null) continue;   // 끝난 투자 기간의 잔량을 출금한 경우

                    cycle.withdrawCount++;
                    cycle.withdrawnQty = cycle.withdrawnQty.add(q);

                    if (pos.isEmpty()) {
                        cycles.add(closedCycle(market, cycle, f.orderedAt()));
                        cycle = null;
                    }
                }
            }

            // 아직 보유 중인 투자 기간
            if (cycle != null) {
                cycles.add(new Cycle(market, cycle.no, cycle.startedAt, null, null,
                        cycle.buyCount, cycle.sellCount,
                        cycle.withdrawCount, cycle.withdrawnQty,
                        money(cycle.buyAmount), money(cycle.sellAmount),
                        money(cycle.pnl), rate(cycle.pnl, cycle.soldCost),
                        pos.qty, money(pos.avgCost()), false, null));
            }
        }

        return new Result(sells, cycles, warnings);
    }

    private Cycle closedCycle(String market, CycleAcc c, OffsetDateTime endedAt) {
        return new Cycle(market, c.no, c.startedAt, endedAt,
                Duration.between(c.startedAt, endedAt).getSeconds(),
                c.buyCount, c.sellCount,
                c.withdrawCount, c.withdrawnQty,
                money(c.buyAmount), money(c.sellAmount),
                money(c.pnl), rate(c.pnl, c.soldCost),
                BigDecimal.ZERO, null, true,
                c.sellCount > 0 ? c.pnl.signum() > 0 : null);   // 판 적 없이 출금만 했으면 승패 없음
    }

    /**
     * 수수료가 원화인지 코인인지 추측해요.
     * 수수료 ÷ 금액, 수수료 ÷ 수량 중에서 보통 수수료율(0.15%)에 더 가까운 쪽을 골라요.
     */
    static boolean isCoinUnitFee(BigDecimal fee, BigDecimal volume, BigDecimal funds) {
        if (fee.signum() == 0 || funds.signum() == 0) return false;
        double rKrw = fee.doubleValue() / funds.doubleValue();
        double rCoin = fee.doubleValue() / volume.doubleValue();
        return distance(rCoin) < distance(rKrw);
    }

    private static double distance(double rate) {
        return Math.abs(Math.log(rate / TYPICAL_FEE_RATE));
    }

    private static BigDecimal rate(BigDecimal pnl, BigDecimal base) {
        return base.signum() == 0 ? BigDecimal.ZERO : pnl.divide(base, MC).setScale(6, RoundingMode.HALF_UP);
    }

    private static BigDecimal nz(BigDecimal v) {
        return v == null ? BigDecimal.ZERO : v;
    }

    private static BigDecimal money(BigDecimal v) {
        return v.setScale(2, RoundingMode.HALF_UP);
    }

    private static String plain(BigDecimal v) {
        return v.stripTrailingZeros().toPlainString();
    }
}
