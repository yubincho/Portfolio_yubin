package com.bitanalyzer.service;

import com.bitanalyzer.config.restApi.BithumbRestClient;
import com.bitanalyzer.domain.bithumbWithdraw.BithumbWithdraw;
import com.bitanalyzer.domain.bithumbWithdraw.repository.BithumbWithdrawRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.OffsetDateTime;



/**
 * 빗썸 코인 출금 기록(완료된 것)을 전부 가져와서 DB에 저장.
 * 주문 동기화와 같은 방식: 페이지를 넘기며 가져오고, 이미 있는 건 건너뛰어.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class BithumbWithdrawSyncService {

    private static final int MAX_PAGES = 1000;
    private static final long PAGE_DELAY_MS = 150;

    private final BithumbRestClient bithumbRestClient;
    private final BithumbWithdrawRepository bithumbWithdrawRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    /** @return 새로 저장한 출금 수 */
    public int syncWithdraws() throws Exception {
        int saved = 0;
        int skipped = 0;

        for (int page = 1; page <= MAX_PAGES; page++) {
            String body = bithumbRestClient.getWithdraws("DONE", page);
            JsonNode list = objectMapper.readTree(body);

            if (!list.isArray() || list.isEmpty()) {
                log.info("[출금] {}페이지가 비어 있어서 종료", page);
                break;
            }

            for (JsonNode node : list) {
                String uuid = textOrNull(node, "uuid");
                if (uuid == null || bithumbWithdrawRepository.existsByWithdrawUuid(uuid)) {
                    skipped++;
                    continue;
                }

                bithumbWithdrawRepository.save(BithumbWithdraw.builder()
                        .withdrawUuid(uuid)
                        .currency(textOrNull(node, "currency"))
                        .state(textOrNull(node, "state"))
                        .amount(decimalOrNull(node, "amount"))
                        .fee(decimalOrNull(node, "fee"))
                        .createdAt(dateOrNull(node, "created_at"))
                        .doneAt(dateOrNull(node, "done_at"))
                        .rawJson(node.toString())
                        .build());
                saved++;
            }

            log.info("[출금] {}페이지 처리 완료 ({}건)", page, list.size());
            Thread.sleep(PAGE_DELAY_MS);
        }

        log.info("⭕ 빗썸 출금 동기화 끝 — 새로 저장: {}건, 건너뜀: {}건", saved, skipped);
        return saved;
    }

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
            return OffsetDateTime.parse(text);
        } catch (Exception e) {
            log.warn("[출금] 시각 형식을 못 읽음: {} (원본 JSON에는 남아 있어요)", text);
            return null;
        }
    }
}
