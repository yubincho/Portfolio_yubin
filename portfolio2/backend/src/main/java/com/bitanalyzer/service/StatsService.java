package com.bitanalyzer.service;


import com.bitanalyzer.domain.tradeCycle.TradeCycle;
import com.bitanalyzer.domain.tradeCycle.repository.TradeCycleRepository;
import com.bitanalyzer.domain.tradeSell.TradeSell;
import com.bitanalyzer.domain.tradeSell.repository.TradeSellRepository;
import com.bitanalyzer.dto.StatsDto;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.util.List;

/**
 * 대시보드 통계
 *
 * 계산은 대부분 DB(SQL)가 하고, 여기서는
 *  1) 날짜를 한국 시간 기준 범위로 바꾸고
 *  2) 승률·수익률(%)을 계산하고 (0으로 나누기 방지)
 *  3) 화면 표시용 이름(월, 9시, XRP 등)을 붙여.
 */
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class StatsService {

    private static final ZoneId KST = ZoneId.of("Asia/Seoul");
    private static final LocalDate EARLIEST = LocalDate.of(2000, 1, 1);
    private static final String[] WEEKDAYS = {"", "월", "화", "수", "목", "금", "토", "일"};
    private static final String[] HOLD_LABELS = {"", "1일 미만", "1일~1주", "1주~1개월", "1개월 이상"};
    private static final int MAX_RECENT = 100;

    private final TradeSellRepository tradeSellRepository;
    private final TradeCycleRepository tradeCycleRepository;

    public StatsDto.Summary summary(LocalDate from, LocalDate to) {
        Period p = period(from, to);
        TradeSellRepository.SummaryRow s = tradeSellRepository.summarize(p.start(), p.end());
        TradeCycleRepository.CycleSummaryRow c = tradeCycleRepository.summarizeClosed(p.start(), p.end());

        BigDecimal avgHoldHours = c.getAvgHoldSeconds() == null ? null
                : c.getAvgHoldSeconds().divide(BigDecimal.valueOf(3600), 1, RoundingMode.HALF_UP);

        return new StatsDto.Summary(p.from(), p.to(),
                s.getSellCount(), s.getWinCount(),
                pct(BigDecimal.valueOf(s.getWinCount()), BigDecimal.valueOf(s.getSellCount())),
                s.getRealizedPnl(),
                pct(s.getRealizedPnl(), s.getCostAmount()),
                s.getFeeKrw(),
                c.getClosedCount(), avgHoldHours);
    }

    public List<StatsDto.GroupStat> byMarket(LocalDate from, LocalDate to) {
        Period p = period(from, to);
        return tradeSellRepository.groupByMarket(p.start(), p.end()).stream()
                .map(r -> toGroupStat(r, r.getGroupKey().replace("KRW-", "")))
                .toList();
    }

    public List<StatsDto.GroupStat> byMonth(LocalDate from, LocalDate to) {
        Period p = period(from, to);
        return tradeSellRepository.groupByMonth(p.start(), p.end()).stream()
                .map(r -> {
                    String[] ym = r.getGroupKey().split("-");   // 2026-03 → 2026년 3월
                    return toGroupStat(r, ym[0] + "년 " + Integer.parseInt(ym[1]) + "월");
                })
                .toList();
    }

    public List<StatsDto.GroupStat> byWeekday(LocalDate from, LocalDate to) {
        Period p = period(from, to);
        return tradeSellRepository.groupByWeekday(p.start(), p.end()).stream()
                .map(r -> toGroupStat(r, WEEKDAYS[r.getGroupKey()]))
                .toList();
    }

    public List<StatsDto.GroupStat> byHour(LocalDate from, LocalDate to) {
        Period p = period(from, to);
        return tradeSellRepository.groupByHour(p.start(), p.end()).stream()
                .map(r -> toGroupStat(r, r.getGroupKey() + "시"))
                .toList();
    }

    public List<StatsDto.HoldPeriodStat> byHoldPeriod(LocalDate from, LocalDate to) {
        Period p = period(from, to);
        return tradeCycleRepository.groupByHoldPeriod(p.start(), p.end()).stream()
                .map(r -> new StatsDto.HoldPeriodStat(
                        HOLD_LABELS[r.getBucket()],
                        r.getCycleCount(),
                        pct(BigDecimal.valueOf(r.getWinCount()), BigDecimal.valueOf(r.getCycleCount())),
                        r.getRealizedPnl(),
                        r.getAvgReturnRate().multiply(BigDecimal.valueOf(100)).setScale(2, RoundingMode.HALF_UP)))
                .toList();
    }

    public List<StatsDto.RecentTrade> recentTrades(int limit) {
        int size = Math.max(1, Math.min(limit, MAX_RECENT));   // 1 ~ 100건으로 제한
        return tradeSellRepository.findAllByOrderBySoldAtDesc(PageRequest.of(0, size)).stream()
                .map(this::toRecentTrade)
                .toList();
    }

    public List<StatsDto.Position> positions() {
        return tradeCycleRepository.findByClosedFalseOrderByMarketAsc().stream()
                .map(this::toPosition)
                .toList();
    }


    // ---------- 도우미 ----------

    /** 조회 기간: from ~ to (둘 다 포함, 한국 시간 기준). 비어 있으면 전체 기간 */
    private record Period(LocalDate from, LocalDate to, OffsetDateTime start, OffsetDateTime end) {}

    private Period period(LocalDate from, LocalDate to) {
        LocalDate f = (from != null) ? from : EARLIEST;
        LocalDate t = (to != null) ? to : LocalDate.now(KST);
        if (f.isAfter(t)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "from은 to보다 늦을 수 없어요");
        }
        return new Period(f, t,
                f.atStartOfDay(KST).toOffsetDateTime(),
                t.plusDays(1).atStartOfDay(KST).toOffsetDateTime());   // to 날짜의 끝까지 포함
    }

    /** 퍼센트 계산 (분모가 0이면 0) */
    private static BigDecimal pct(BigDecimal numerator, BigDecimal denominator) {
        if (denominator == null || denominator.signum() == 0) return BigDecimal.ZERO;
        return numerator.multiply(BigDecimal.valueOf(100)).divide(denominator, 2, RoundingMode.HALF_UP);
    }

    private StatsDto.GroupStat toGroupStat(TradeSellRepository.TextGroupRow r, String label) {
        return new StatsDto.GroupStat(r.getGroupKey(), label, r.getSellCount(),
                pct(BigDecimal.valueOf(r.getWinCount()), BigDecimal.valueOf(r.getSellCount())),
                r.getRealizedPnl(), pct(r.getRealizedPnl(), r.getCostAmount()));
    }

    private StatsDto.GroupStat toGroupStat(TradeSellRepository.NumberGroupRow r, String label) {
        return new StatsDto.GroupStat(String.valueOf(r.getGroupKey()), label, r.getSellCount(),
                pct(BigDecimal.valueOf(r.getWinCount()), BigDecimal.valueOf(r.getSellCount())),
                r.getRealizedPnl(), pct(r.getRealizedPnl(), r.getCostAmount()));
    }

    private StatsDto.RecentTrade toRecentTrade(TradeSell s) {
        return new StatsDto.RecentTrade(s.getMarket(), s.getSoldAt(), s.getQuantity(),
                s.getAvgBuyPrice(), s.getSellPrice(), s.getRealizedPnl(),
                s.getReturnRate() == null ? null
                        : s.getReturnRate().multiply(BigDecimal.valueOf(100)).setScale(2, RoundingMode.HALF_UP),
                s.getWin());
    }

    private StatsDto.Position toPosition(TradeCycle c) {
        return new StatsDto.Position(c.getMarket(), c.getRemainingQuantity(), c.getAvgBuyPrice(),
                c.getStartedAt(), c.getBuyCount() == null ? 0 : c.getBuyCount());
    }

}
