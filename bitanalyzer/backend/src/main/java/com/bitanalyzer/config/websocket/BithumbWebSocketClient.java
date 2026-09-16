package com.bitanalyzer.config.websocket;


import com.bitanalyzer.service.tradeJournal.TradeJournalService;
import com.bitanalyzer.service.bithumbMessageService.BithumbMessageService;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import org.springframework.web.socket.*;
import org.springframework.web.socket.client.standard.StandardWebSocketClient;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.UUID;


@Slf4j
@Component
@RequiredArgsConstructor
public class BithumbWebSocketClient {

    private final BithumbJwtProvider jwtProvider;
    private final TradeJournalService tradeJournalService;
    private final BithumbMessageService bithumbMessageService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    // Private 전용 엔드포인트
    private static final String WS_URL = "wss://ws-api.bithumb.com/websocket/v1/private";

    public void connect() {
        try {
            StandardWebSocketClient client = new StandardWebSocketClient();

            WebSocketHttpHeaders headers = new WebSocketHttpHeaders();
            headers.add("Authorization", "Bearer " + jwtProvider.createToken());

            client.execute(new BithumbWebSocketHandler(), headers, java.net.URI.create(WS_URL));

            log.info("Bithumb Private WebSocket 연결을 시도합니다...");
        } catch (Exception e) {
            log.error("WebSocket 연결 초기화 실패", e);
        }
    }

    private class BithumbWebSocketHandler extends TextWebSocketHandler {

        @Override
        public void afterConnectionEstablished(WebSocketSession session) throws Exception {
            log.info("*** Bithumb Private WebSocket 연결 성공 ^^!");

            // Private 데이터 구독 요청 (myOrder, myAsset, transaction 등)
            // 빗썸 Private WebSocket의 구독 형식
            // ticket 필드는 Private WebSocket 에서는 필수가 아님 (Public일 때만 주로 사용)
            // myOrder는 symbols 배열을 함께 보내는 것이 권장됨
            // myAsset은 별도 파라미터 없이 type만 보냄

            // 1) myOrder 구독 (내 주문/체결)
            // myOrder 먼저
//            var myOrderPayload = List.of(
//                    Map.of("ticket", UUID.randomUUID().toString()),
//                    Map.of("type", "myOrder", "codes", List.of("KRW-XRP"))
//            );
////            session.sendMessage(new TextMessage(objectMapper.writeValueAsString(myOrderPayload)));
//            String myOrderMessage = objectMapper.writeValueAsString(myOrderPayload);
//            session.sendMessage(new TextMessage(myOrderMessage));
//            log.info("📡 myOrder 구독 요청 전송");

//            Thread.sleep(1000); // ★ 0.5초 텀

            // myAsset 나중에
            // 2) myAsset 구독 (내 자산)
//            var myAssetPayload = List.of(
//                    Map.of("ticket", UUID.randomUUID().toString()),
//                    Map.of("type", "myAsset")
//            );
//            String myAssetMessage = objectMapper.writeValueAsString(myAssetPayload);
//            session.sendMessage(new TextMessage(myAssetMessage));
//            log.info("📡 myAsset 구독 요청 전송");

            // myOrder + myAsset 한 메시지에 함께 구독
            var subscribePayload = List.of(
                    Map.of("ticket", UUID.randomUUID().toString()),
                    Map.of("type", "myOrder", "codes", List.of("KRW-XRP")),  // ★ codes 추가!
                    Map.of("type", "myAsset")
            );
            session.sendMessage(new TextMessage(objectMapper.writeValueAsString(subscribePayload)));
            log.info("📡 myOrder + myAsset 구독 요청 전송");

            // ★ 추가: 주기적으로 핑 보내서 연결 유지 (30초마다)
            startPingScheduler(session);
        }

        private void startPingScheduler(WebSocketSession session) {
            Thread pingThread = new Thread(() -> {
                try {
                    while (session.isOpen()) {
                        Thread.sleep(30000); // 30초마다
                        if (session.isOpen()) {
                            // 핑 프레임 전송
                            session.sendMessage(new PingMessage());
                            log.debug("💓 핑 전송 (연결 유지)");
                        }
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } catch (Exception e) {
                    log.warn("핑 전송 실패: {}", e.getMessage());
                }
            });
            pingThread.setDaemon(true);
            pingThread.start();
        }

        //  Private 데이터 구독 요청 후 "메시지 수신 받는 방법"
        //  첫째, TextWebSocketHandler → AbstractWebSocketHandler로 바꿔서 텍스트랑 바이너리 둘 다 받을 수 있게 함
        //  둘째, handleBinaryMessage 메서드를 추가해서 바이너리로 들어온 걸 UTF-8 문자열로 디코딩한 다음, 기존이랑 똑같이 처리

        // 텍스트로 올 경우
        @Override
        protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
            String payload = message.getPayload();
            log.debug("WebSocket 메시지 수신 (Received) : {}", payload);

            handlePayload(payload);
        }

        // ★ 핵심: 바이너리로 올 경우 (빗썸은 여기로 옴)
        @Override
        protected void handleBinaryMessage(WebSocketSession session, BinaryMessage message) {
            // 바이너리 -> UTF-8 문자열로 변환
            String payload = StandardCharsets.UTF_8.decode(message.getPayload()).toString();

            handlePayload(payload);
        }

        // 공통 처리
        private void handlePayload(String payload) {
            log.debug("WebSocket 메시지 수신: {}", payload);
//            tradeJournalService.processWebSocketMessage(payload);
            bithumbMessageService.processWebSocketMessage(payload);
        }


//        @Override
//        protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
//            String payload = message.getPayload();
//            log.debug("WebSocket 메시지 수신 (Received) : {}", payload);
//
//            // TradeJournalService 에서 JSON 파싱 후 저장
//            tradeJournalService.processWebSocketMessage(payload);
//        }

        @Override
        public void handleTransportError(WebSocketSession session, Throwable exception) {
            log.error("WebSocket 전송 오류 발생", exception);
        }

        @Override
        public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
            log.warn("WebSocket 연결 종료됨. 코드: {}, 이유: {}", status.getCode(), status.getReason());

            // 10초 후 재연결 (선택)
            if (status.getCode() != 1000) {
                log.info("10초 후 재연결을 시도합니다...");
                new Thread(() -> {
                    try {
                        Thread.sleep(10000);
                        connect();
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    }
                }).start();
            }
        }
    }
}