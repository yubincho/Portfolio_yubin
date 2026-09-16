package com.bitanalyzer.exception;


import lombok.Builder;
import lombok.Getter;


@Getter
@Builder
public class ErrorResponse {

    private final int status;
    private final String code;
    private final String message;
    private final String detail;
}
