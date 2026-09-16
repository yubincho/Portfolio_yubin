package com.bitanalyzer.config.websocket;


import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class BithumbWebSocketConfig implements CommandLineRunner {

    private final BithumbWebSocketClient bithumbWebSocketClient;

    @Override
    public void run(String... args) {
        try {
            log.info("=== Bithumb Private WebSocket 초기화 시작 ===");
            bithumbWebSocketClient.connect();
        } catch (Exception e) {
            log.error("Bithumb WebSocket 연결 실패", e);
        }
    }
}

