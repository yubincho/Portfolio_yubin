# .env에서 DB 접속정보 읽기

import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일 로드

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

# Gemini (Google AI Studio에서 발급한 키)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# 무료로 쓸 수 있는 모델 이름은 바뀔 수 있어서 .env에서 바꿀 수 있게 함.
# GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# 쓸 모델 목록 (쉼표로 구분, 앞에서부터 시도)
# 앞 모델이 바쁘거나(503) 없거나(404) 한도 초과(429)면 다음 모델로 넘어가.
# 무료로 쓸 수 있는 모델 이름은 바뀔 수 있어서 .env에서 바꿀 수 있게.
GEMINI_MODELS = [
    m.strip()
    for m in os.getenv("GEMINI_MODELS", "gemini-3.8-flash,gemini-3.7-flash,gemini-3.5-flash-lite").split(",")
    if m.strip()
]






