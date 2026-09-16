package com.bitanalyzer.exception;


import com.bitanalyzer.exception.enums.ErrorCode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.HashMap;
import java.util.Map;


@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * 커스텀 예외 처리 (BitAnalyzerException)
     */
    @ExceptionHandler(BitAnalyzerException.class)
    public ResponseEntity<ErrorResponse> handleBitAnalyzerException(BitAnalyzerException e) {
        log.error("BitAnalyzerException 발생: {}", e.getErrorCode(), e);

        ErrorResponse response = ErrorResponse.builder()
                .status(e.getErrorCode().getStatus().value())
                .code(e.getErrorCode().name())
                .message(e.getErrorCode().getMessage())
                .detail(e.getDetailMessage())
                .build();

        return ResponseEntity
                .status(e.getErrorCode().getStatus())
                .body(response);
    }

    /**
     * Validation 예외 처리 (@Valid 실패 시)
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationException(MethodArgumentNotValidException e) {
        Map<String, String> errors = new HashMap<>();
        e.getBindingResult().getFieldErrors().forEach(error ->
                errors.put(error.getField(), error.getDefaultMessage()));

        ErrorResponse response = ErrorResponse.builder()
                .status(HttpStatus.BAD_REQUEST.value())
                .code(ErrorCode.INVALID_INPUT_VALUE.name())
                .message(ErrorCode.INVALID_INPUT_VALUE.getMessage())
                .detail(errors.toString())
                .build();

        return ResponseEntity.badRequest().body(response);
    }

    /**
     * 모든 예외를 잡는 최종 핸들러
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGlobalException(Exception e) {
        log.error("Unhandled Exception 발생", e);

        ErrorResponse response = ErrorResponse.builder()
                .status(HttpStatus.INTERNAL_SERVER_ERROR.value())
                .code(ErrorCode.INTERNAL_SERVER_ERROR.name())
                .message(ErrorCode.INTERNAL_SERVER_ERROR.getMessage())
                .detail(e.getMessage())
                .build();

        return ResponseEntity.internalServerError().body(response);
    }
}
