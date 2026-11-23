package com.bitanalyzer.web.controller;


import com.bitanalyzer.dto.StatsDto;
import com.bitanalyzer.service.StatsService;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.time.LocalDate;

/**
 * 대시보드 통계 API
 *
 * 모든 통계 API는 기간을 고를 수 있다. (둘 다 생략하면 전체 기간)
 *   예) /api/stats/summary?from=2026-01-01&to=2026-06-30
 */
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class StatsController {

    private final StatsService statsService;

    /** 요약 카드: 실현 손익, 승률, 수익률, 수수료, 평균 보유 시간 */
    @GetMapping("/stats/summary")
    public StatsDto.Summary summary(@RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
                                    @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        return statsService.summary(from, to);
    }

    /** 코인별 손익 (손익 큰 순) */
    @GetMapping("/stats/by-market")
    public List<StatsDto.GroupStat> byMarket(@RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
                                             @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        return statsService.byMarket(from, to);
    }

    /** 월별 손익 */
    @GetMapping("/stats/by-month")
    public List<StatsDto.GroupStat> byMonth(@RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
                                            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        return statsService.byMonth(from, to);
    }

    /** 요일별 손익 */
    @GetMapping("/stats/by-weekday")
    public List<StatsDto.GroupStat> byWeekday(@RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
                                              @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        return statsService.byWeekday(from, to);
    }

    /** 시간대별 손익 */
    @GetMapping("/stats/by-hour")
    public List<StatsDto.GroupStat> byHour(@RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
                                           @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        return statsService.byHour(from, to);
    }

    /** 보유 기간별 승률 */
    @GetMapping("/stats/by-hold-period")
    public List<StatsDto.HoldPeriodStat> byHoldPeriod(@RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
                                                      @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        return statsService.byHoldPeriod(from, to);
    }

    /** 최근 매도 (기본 10건, 최대 100건) */
    @GetMapping("/trades/recent")
    public List<StatsDto.RecentTrade> recentTrades(@RequestParam(defaultValue = "10") int limit) {
        return statsService.recentTrades(limit);
    }

    /** 지금 보유 중인 코인 */
    @GetMapping("/positions")
    public List<StatsDto.Position> positions() {
        return statsService.positions();
    }
}
