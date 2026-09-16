package com.bitanalyzer.exception.enums;


import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;


@Getter
@RequiredArgsConstructor
public enum ErrorCode {

    // 거래 관련
    TRADE_NOT_FOUND(HttpStatus.NOT_FOUND, "해당 거래를 찾을 수 없습니다."),
    TRADE_ALREADY_EXISTS(HttpStatus.CONFLICT, "이미 존재하는 거래입니다."),

    // 사용자 관련
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "사용자를 찾을 수 없습니다."),

    // 시장 스냅샷 관련
    MARKET_SNAPSHOT_NOT_FOUND(HttpStatus.NOT_FOUND, "시장 스냅샷 정보를 찾을 수 없습니다."),

    // ML 분석 관련
    PREDICTION_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "ML 예측 처리 중 오류가 발생했습니다."),

    // 웹소켓 관련
    WEBSOCKET_CONNECTION_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "웹소켓 연결에 실패했습니다."),

    // 공통 예외
    INVALID_INPUT_VALUE(HttpStatus.BAD_REQUEST, "올바르지 않은 입력값입니다."),
    INTERNAL_SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "서버 내부 오류가 발생했습니다."),
    UNAUTHORIZED_ACCESS(HttpStatus.FORBIDDEN, "접근 권한이 없습니다."),

    ;

    private final HttpStatus status;
    private final String message;
}
