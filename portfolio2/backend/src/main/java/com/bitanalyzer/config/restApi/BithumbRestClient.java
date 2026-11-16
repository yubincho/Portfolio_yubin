package com.bitanalyzer.config.restApi;


import com.bitanalyzer.config.jwt.BithumbJwtProvider;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

import javax.print.DocFlavor;
import java.net.URI;

/**
 * 빗썸 REST API 호출 담당 ("다시보기")
 * 웹소켓(생중계)과 달리, 내가 요청할 때마다 과거 주문 목록을 받아옴.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class BithumbRestClient {

    private static final String BASE_URL = "https://api.bithumb.com";

    private final BithumbJwtProvider jwtProvider;
    private final RestClient restClient = RestClient.create();

    /**
     * 주문 목록 한 페이지 가져오기
     * @param market 예) KRW-XRP, null이면 모든 코인
     * @param state  done(완료), cancel(취소) 등
     * @param page   1부터 시작
     */
    public String getOrders(String market, String state, int page) {
        String query = "state=" + state
                + "&page=" + page
                + "&limit=100"
                + "&order_by=asc";   // 오래된 것부터

        if (market != null) {
            query = "market=" + market + "&" + query;
        }
        return get("/v1/orders", query);
    }

    /**
     * 코인 출금 목록 한 페이지 가져오기 (해외 거래소, 개인 지갑 등으로 보낸 기록)
     * @param state DONE(완료), PROCESSING(처리 중), CANCELLED(취소)
     * @param page  1부터 시작
     */
    public String getWithdraws(String state, int page) {
        String query = "state=" + state
                + "&page=" + page
                + "&limit=100"
                + "&order_by=asc";
        return get("/v1/withdraws", query);
    }

    /** 공통: 출입증(JWT)을 붙여서 GET 요청 */
    private String get(String path, String query) {
        // ⚠️ 출입증에 넣는 문자열과 실제로 보내는 주소의 조건이 "글자 하나까지" 똑같아야 해요
        String token = jwtProvider.createToken(query);

        try {
            return restClient.get()
                    .uri(URI.create(BASE_URL + path + "?" + query))
                    .header("Authorization", "Bearer " + token)
                    .retrieve()
                    .body(String.class);

        } catch (RestClientResponseException e) {
            // 빗썸이 에러를 주면 이유를 로그로 남겨요 (IP 미등록, 인증 실패, 권한 없음 등)
            log.error("빗썸 API 실패 | {} | 상태코드={} | 응답={}",
                    path, e.getStatusCode(), e.getResponseBodyAsString());
            throw e;
        }
    }
}
