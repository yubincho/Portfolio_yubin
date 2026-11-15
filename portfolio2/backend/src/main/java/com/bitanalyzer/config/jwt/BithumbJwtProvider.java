package com.bitanalyzer.config.jwt;


import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.UUID;


@Component
public class BithumbJwtProvider {

    @Value("${bithumb.access-key}")
    private String accessKey;

    @Value("${bithumb.secret-key}")
    private String secretKey;

    /** 웹소켓용 */
    public String createToken() {
        // 빗썸 공식 예제 algorithm="HS512"
        Algorithm algorithm = Algorithm.HMAC512(secretKey);

        return JWT.create()
                .withClaim("access_key", accessKey)
                .withClaim("nonce", UUID.randomUUID().toString())
                .withClaim("timestamp", System.currentTimeMillis())
                .sign(algorithm);
    }


    /**
     * REST API용
     * 조회 조건이 있으면 그 조건을 SHA-512로 요약한 값(query_hash)을 출입증에 같이 넣어야.
     * 빗썸이 "요청 내용이 중간에 바뀌지 않았는지" 확인하는 용도.
     */
    public String createToken(String queryString) {
        // 빗썸 공식 예제 algorithm="HS512"
        Algorithm algorithm = Algorithm.HMAC512(secretKey);

        var builder = JWT.create()
                .withClaim("access_key", accessKey)
                .withClaim("nonce", UUID.randomUUID().toString())
                .withClaim("timestamp", System.currentTimeMillis());

        if (queryString != null && !queryString.isEmpty()) {
            builder.withClaim("query_hash", sha512(queryString))
                    .withClaim("query_hash_alg", "SHA512");
        }

        return builder.sign(algorithm);
    }

    private String sha512(String text) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-512");
            byte[] hash = md.digest(text.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hash);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-512를 사용할 수 없어요", e);
        }
    }




}
