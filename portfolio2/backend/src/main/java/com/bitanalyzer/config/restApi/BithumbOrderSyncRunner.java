package com.bitanalyzer.config.restApi;


import com.bitanalyzer.service.BithumbOrderSyncService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;


/**
 * 서버가 켜질 때마다 빗썸 완료 주문을 DB와 맞춰요.
 * - 처음 실행: 과거 주문 전부 저장 (백필)
 * - 그다음부터: 서버가 꺼져 있던 동안 생긴 주문만 새로 저장 (보정)
 *
 * ※ BithumbOrderCheckRunner(확인용)는 이제 지워도 돼요.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class BithumbOrderSyncRunner implements CommandLineRunner {

    private final BithumbOrderSyncService bithumbOrderSyncService;

    @Override
    public void run(String... args) {
        try {
            log.info("=== 빗썸 완료 주문 동기화 시작 ===");
            bithumbOrderSyncService.syncDoneOrders();
        } catch (Exception e) {
            // 동기화가 실패해도 서버(웹소켓 등)는 계속 돌아가게 해요
            log.error("빗썸 완료 주문 동기화 실패", e);
        }
    }
}
