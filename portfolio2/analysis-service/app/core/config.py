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










