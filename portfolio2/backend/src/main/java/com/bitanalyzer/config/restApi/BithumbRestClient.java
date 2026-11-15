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
     * 완료된(done) 주문 목록 한 페이지 가져오기
     * @param market 예) KRW-XRP, null이면 모든 코인
     * @param page   1부터 시작
     * @return 빗썸이 준 JSON 그대로 (일단 모양을 보려고 문자열로 받아)
     */
    public String getDoneOrders(String market, int page) {
        // ⚠️ 출입증에 넣는 문자열과 실제로 보내는 주소의 조건이 "글자 하나까지" 똑같아야.

        // 단건 일때
//        String query = "market=" + market
//                + "&state=done"
//                + "&page=" + page
//                + "&limit=100"
//                + "&order_by=asc";   // 오래된 주문부터

        // 다건 조회
        String query = "state=done"
                + "&page=" + page
                + "&limit=100"
                + "&order_by=asc";

        if (market != null) {
            query = "market=" + market + "&" + query;
        }

        String token = jwtProvider.createToken(query);

        try {
            return restClient.get()
                    .uri(URI.create(BASE_URL + "/v1/orders?" + query))
                    .header("Authorization", "Bearer " + token)
                    .retrieve()
                    .body(String.class);
        } catch(RestClientResponseException e) {
            log.error("빗썸 주문 조회 실패 | 상태코드={} | 응답={}",
                    e.getStatusCode(), e.getResponseBodyAsString());
            throw e;
        }
    }


}
