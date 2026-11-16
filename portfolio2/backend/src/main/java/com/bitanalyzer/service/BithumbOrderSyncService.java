package com.bitanalyzer.service;

import com.bitanalyzer.config.restApi.BithumbRestClient;
import com.bitanalyzer.domain.bithumOrder.BithumbOrder;
import com.bitanalyzer.domain.bithumOrder.repository.BithumbOrderRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;


/**
 * 빗썸 완료 주문을 전부 가져와서 DB에 저장.
 *
 * 흐름: 1페이지 요청 → 저장 → 2페이지 요청 → 저장 → ... → 빈 페이지가 오면 끝
 * 이미 저장된 주문은 건너뛰어서, 여러 번 실행해도 중복이 생기지 않아요.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class BithumbOrderSyncService {

    private static final int MAX_PAGES = 1000;       // 혹시 모를 무한 반복 방지
    private static final long PAGE_DELAY_MS = 150;   // 빗썸에 너무 빨리 요청하지 않게

    private final BithumbRestClient bithumbRestClient;
    private final BithumbOrderRepository bithumbOrderRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();


    /**
     * 완료(done) 주문 + 부분 체결 후 취소(cancel)된 주문을 가져와요.
     * 취소된 주문은 하나라도 체결된 것만 저장해요. (체결 0개는 손익과 상관없으니까)
     * @return 새로 저장한 주문 수
     */
    public int syncOrders() throws Exception {
        int saved = 0;
        int skipped = 0;

        for (String state : List.of("done", "cancel")) {
            for (int page = 1; page <= MAX_PAGES; page++) {
                String body = bithumbRestClient.getOrders(null, state, page);  // null = 모든 코인
                JsonNode orders = objectMapper.readTree(body);

                if (!orders.isArray() || orders.isEmpty()) {
                    log.info("[{}] {}페이지가 비어 있어서 종료", state, page);
                    break;
                }

                for (JsonNode node : orders) {
                    String orderUuid = textOrNull(node, "uuid");
                    BigDecimal executed = decimalOrNull(node, "executed_volume");

                    if (orderUuid == null
                            || executed == null || executed.signum() == 0          // 체결 0개
                            || bithumbOrderRepository.existsByOrderUuid(orderUuid)) {
                        skipped++;
                        continue;
                    }

                    bithumbOrderRepository.save(toEntity(node));
                    saved++;
                }

                log.info("[{}] {}페이지 처리 완료 ({}건)", state, page, orders.size());
                Thread.sleep(PAGE_DELAY_MS);
            }
        }

        log.info("⭕ 빗썸 주문 동기화 끝 — 새로 저장: {}건, 건너뜀: {}건", saved, skipped);
        return saved;
    }

    /** 빗썸 JSON 한 건 → 엔티티 */
    private BithumbOrder toEntity(JsonNode node) {
        return BithumbOrder.builder()
                .orderUuid(textOrNull(node, "uuid"))
                .market(textOrNull(node, "market"))
                .side(textOrNull(node, "side"))
                .orderType(textOrNull(node, "ord_type"))
                .state(textOrNull(node, "state"))
                .price(decimalOrNull(node, "price"))
                .volume(decimalOrNull(node, "volume"))
                .remainingVolume(decimalOrNull(node, "remaining_volume"))
                .executedVolume(decimalOrNull(node, "executed_volume"))
                .executedFunds(decimalOrNull(node, "executed_funds"))
                .paidFee(decimalOrNull(node, "paid_fee"))
                .tradesCount(node.hasNonNull("trades_count") ? node.get("trades_count").asInt() : null)
                .orderedAt(dateOrNull(node, "created_at"))
                .rawJson(node.toString())
                .build();
    }

    // --- null 안전 헬퍼들 (BithumbMessageService와 같은 방식) ---
    private String textOrNull(JsonNode node, String field) {
        JsonNode v = node.get(field);
        return (v == null || v.isNull()) ? null : v.asText();
    }

    private BigDecimal decimalOrNull(JsonNode node, String field) {
        String text = textOrNull(node, field);
        return (text == null || text.isEmpty()) ? null : new BigDecimal(text);
    }

    private OffsetDateTime dateOrNull(JsonNode node, String field) {
        String text = textOrNull(node, field);
        if (text == null) return null;
        try {
            return OffsetDateTime.parse(text);   // 예) 2025-11-27T10:15:30+09:00
        } catch (Exception e) {
            log.warn("주문 시각 형식을 못 읽음: {} (원본 JSON에는 남아 있어요)", text);
            return null;
        }
    }

}
