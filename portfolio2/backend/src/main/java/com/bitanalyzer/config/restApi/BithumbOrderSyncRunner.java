package com.bitanalyzer.config.restApi;


import com.bitanalyzer.service.BithumbOrderSyncService;
import com.bitanalyzer.service.BithumbWithdrawSyncService;
import com.bitanalyzer.service.TradePnlService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;


/**
 * 서버가 켜질 때마다
 *  1) 빗썸 주문을 DB와 맞추고 (완료 + 부분 체결 후 취소)
 *  2) 빗썸 출금 기록을 DB와 맞추고
 *  3) 평균 단가 방식으로 손익을 다시 계산해요
 *
 * 1, 2가 실패해도 이미 저장된 데이터로 3은 할 수 있어요.
 *
 * ※ BithumbOrderCheckRunner(확인용) - 삭제해도 됨
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class BithumbOrderSyncRunner implements CommandLineRunner {

    private final BithumbOrderSyncService bithumbOrderSyncService;
    private final BithumbWithdrawSyncService bithumbWithdrawSyncService;
    private final TradePnlService tradePnlService;

    @Override
    public void run(String... args) {
        try {
            log.info("=== 빗썸 주문 동기화 시작 ===");
            bithumbOrderSyncService.syncOrders();
        } catch (Exception e) {
            log.error("빗썸 주문 동기화 실패", e);
        }

        try {
            log.info("=== 빗썸 출금 동기화 시작 ===");
            bithumbWithdrawSyncService.syncWithdraws();
        } catch (Exception e) {
            log.error("빗썸 출금 동기화 실패", e);
        }

        try {
            tradePnlService.rebuild();
        } catch (Exception e) {
            log.error("손익 계산 실패", e);
        }
    }
}
