package com.bitanalyzer.exception;


import com.bitanalyzer.exception.enums.ErrorCode;
import lombok.Getter;


@Getter
public class BitAnalyzerException extends RuntimeException {

    private final ErrorCode errorCode;
    private final String detailMessage;

    public BitAnalyzerException(ErrorCode errorCode) {
        this(errorCode, errorCode.getMessage());
    }

    public BitAnalyzerException(ErrorCode errorCode, String detailMessage) {
        super(detailMessage);
        this.errorCode = errorCode;
        this.detailMessage = detailMessage;
    }
}
