package com.bitanalyzer.service.bithumbMessageService;


import com.bitanalyzer.domain.assetSnapshot.AssetSnapshot;
import com.bitanalyzer.domain.assetSnapshot.repository.AssetSnapshotRepository;
import com.bitanalyzer.domain.tradeOrderEvent.TradeOrderEvent;
import com.bitanalyzer.domain.tradeOrderEvent.repository.TradeOrderEventRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;

/**
 * 빗썸 WebSocket 메시지를 받아서, 타입(myOrder/myAsset)별로 파싱하고, 적절한 곳에 저장하는 것
 *  "들어온 메시지를 처리/분배하는" 역할
 * */
@Slf4j
@Service
@RequiredArgsConstructor
public class BithumbMessageService {

    private final TradeOrderEventRepository repository;
    private final AssetSnapshotRepository assetSnapshotRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();


    @Transactional
    public void processWebSocketMessage(String payload) {
        // 엔티티 클래스에 @JsonProperty 붙여서 자동 매핑할 수도 있는데, 일부러 JsonNode로 수동 파싱
        // 이유 : 빗썸 필드가 상황마다 null 이거나 빠질 수 있어서(취소면 trade_uuid 없고 등등)
        try {
            JsonNode node = objectMapper.readTree(payload);

            // 에러 메시지면 무시
            if (node.has("error")) {
                log.warn("WebSocket 에러 메시지 수신: {}", node.get("error").toString());
                return;
            }

            String type = node.path("type").asText();

            switch (type) {
                case "myOrder" -> handleMyOrder(node);
                case "myAsset" -> handleMyAsset(node);
                default -> log.debug("처리하지 않는 타입: {}", type);
            }

        } catch (Exception e) {
            log.error("WebSocket 메시지 파싱/저장 실패. payload={}", payload, e);
        }
    }

    private void handleMyOrder(JsonNode node) {
        String tradeUuid = textOrNull(node, "trade_uuid");

        // 체결 이벤트(trade_uuid 존재)인데 이미 저장돼 있으면 중복이므로 스킵
        if (tradeUuid != null && repository.existsByTradeUuid(tradeUuid)) {
            log.debug("중복 체결 이벤트 스킵: {}", tradeUuid);
            return;
        }

        TradeOrderEvent event = TradeOrderEvent.builder()
                .orderUuid(textOrNull(node, "uuid"))
                .tradeUuid(tradeUuid)
                .code(textOrNull(node, "code"))
                .askBid(textOrNull(node, "ask_bid"))
                .orderType(textOrNull(node, "order_type"))
                .state(textOrNull(node, "state"))
                .price(decimalOrNull(node, "price"))
                .volume(decimalOrNull(node, "volume"))
                .remainingVolume(decimalOrNull(node, "remaining_volume"))
                .executedVolume(decimalOrNull(node, "executed_volume"))
                .paidFee(decimalOrNull(node, "paid_fee"))
                .orderTimestamp(longOrNull(node, "order_timestamp"))
                .tradeTimestamp(longOrNull(node, "trade_timestamp"))
                .streamType(textOrNull(node, "stream_type"))
                .build();

        repository.save(event);
        log.info("📡 주문 이벤트 저장 완료 | code={} state={} side={}",
                event.getCode(), event.getState(), event.getAskBid());
    }


    private void handleMyAsset(JsonNode node) {
        JsonNode assets = node.get("assets");   // 배열
        if (assets == null || !assets.isArray()) {
            log.warn("myAsset에 assets 배열이 없음: {}", node);
            return;
        }

        Long assetTimestamp = longOrNull(node, "asset_timestamp");
        String streamType = textOrNull(node, "stream_type");

        // ★ 배열을 돌면서 각 자산을 따로 저장
        for (JsonNode asset : assets) {
            String currency = textOrNull(asset, "currency");
            BigDecimal balance = decimalOrNull(asset, "balance");
            BigDecimal locked = decimalOrNull(asset, "locked");

            // 직전 저장값이랑 같으면 스킵 (변화 있을 때만 저장)
            AssetSnapshot latest = assetSnapshotRepository
                    .findTopByCurrencyOrderByCreatedAtDesc(currency)
                    .orElse(null);

            if (latest != null
                    && latest.getBalance().compareTo(balance) == 0
                    && latest.getLocked().compareTo(locked) == 0) {
                log.debug("자산 변화 없음, 스킵 | currency={}", currency);
                continue; // 변화 없음 → 저장 안 함
            }

            // 변화 있으면 저장
            AssetSnapshot snapshot = AssetSnapshot.builder()
                    .currency(currency)
                    .balance(balance)
                    .locked(locked)
                    .assetTimestamp(assetTimestamp)
                    .streamType(streamType)
                    .build();
            assetSnapshotRepository.save(snapshot);
            log.info("📡 자산 스냅샷 저장 | currency={} balance={} locked={}",
                    snapshot.getCurrency(), snapshot.getBalance(), snapshot.getLocked());
        }

    }


    // --- null 안전 헬퍼들 ---
    private String textOrNull(JsonNode node, String field) {
        JsonNode v = node.get(field);
        return (v == null || v.isNull()) ? null : v.asText();
    }

    private BigDecimal decimalOrNull(JsonNode node, String field) {
        JsonNode v = node.get(field);
        if (v == null || v.isNull()) return null;
        // decimalValue() 대신 asText()로 문자열 받아서 BigDecimal 생성
        String text = v.asText();
        if (text.isEmpty()) return null;
        return new BigDecimal(text);
    }

    private Long longOrNull(JsonNode node, String field) {
        JsonNode v = node.get(field);
        return (v == null || v.isNull()) ? null : v.asLong();
    }
}
