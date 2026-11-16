//package com.bitanalyzer.config.restApi;
//
//
//import com.fasterxml.jackson.databind.JsonNode;
//import com.fasterxml.jackson.databind.ObjectMapper;
//import lombok.RequiredArgsConstructor;
//import lombok.extern.slf4j.Slf4j;
//import org.springframework.boot.CommandLineRunner;
//import org.springframework.stereotype.Component;
//
///**
// * [임시 확인용] 서버가 켜지면 완료된 주문 1페이지를 가져와서 로그로 보여줘요.
// * 응답 모양을 확인하고 나면 이 파일은 지우고, 진짜 저장 로직으로 바꾸면 됨.
// * 진짜 로직 : BithumbOrderSyncRunner
// */
//@Slf4j
//@Component
//@RequiredArgsConstructor
//public class BithumbOrderCheckRunner implements CommandLineRunner {
//
//    private final BithumbRestClient bithumbRestClient;
//    private final ObjectMapper objectMapper = new ObjectMapper();
//
//    @Override
//    public void run(String... args) {
//        try {
////            String body = bithumbRestClient.getDoneOrders("KRW-XRP", 1);
//            String body = bithumbRestClient.getDoneOrders(null, 1);
//            JsonNode orders = objectMapper.readTree(body);
//
//            log.info("=== 빗썸 완료 주문 조회 성공: {}건 ===", orders.size());
//
//            // 단건 일때
////            if (orders.size() > 0) {
////                // 전부 찍으면 너무 길어서 첫 번째 주문만 보기 좋게 출력
////                log.info("첫 번째 주문:\n{}",
////                        objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(orders.get(0)));
////            }
//
//            // 주문 마다 코인 이름만 한 줄씩 출력
//            for (JsonNode order : orders) {
//                log.info("코인: {} | 매수/매도: {} | 주문시각: {}",
//                        order.path("market").asText(),
//                        order.path("side").asText(),
//                        order.path("created_at").asText());
//            }
//        } catch (Exception e) {
//            log.error("빗썸 완료 주문 확인 실패", e);
//        }
//    }
//}
