package com.bitanalyzer.config.websocket;


import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.UUID;


@Component
public class BithumbJwtProvider {

    @Value("${bithumb.access-key}")
    private String accessKey;

    @Value("${bithumb.secret-key}")
    private String secretKey;

    public String createToken() {
        // 빗썸 공식 예제 algorithm="HS512"
        Algorithm algorithm = Algorithm.HMAC512(secretKey);

        return JWT.create()
                .withClaim("access_key", accessKey)
                .withClaim("nonce", UUID.randomUUID().toString())
                .withClaim("timestamp", System.currentTimeMillis())
                .sign(algorithm);
    }
}
