-- 분기 유동인구 집계 테이블
CREATE TABLE agg_livingpop_dong_quarter (
  행정동코드 INT NOT NULL,
  기준분기 CHAR(5) NOT NULL,              -- 'YYYYQ' (예: 2024Q1)

  유동인구_분기평균 DOUBLE NULL,          -- 분기 평균(일별 대표값 기반)
  유동인구_분기최대 DOUBLE NULL,          -- 분기 중 일별 대표값 최대(옵션)

  관측일수 INT NULL,                      -- 분기 내 데이터가 존재한 일수
  시간대개수_평균 DOUBLE NULL,            -- 일별 시간대 row 수 평균(품질)
  시간대개수_최소 INT NULL,               -- 일별 시간대 row 수 최소(품질)

  load_ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (행정동코드, 기준분기),
  KEY idx_quarter (기준분기)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



-- 데이터 주입
INSERT INTO agg_livingpop_dong_quarter (
  행정동코드, 기준분기,
  유동인구_분기평균, 유동인구_분기최대,
  관측일수, 시간대개수_평균, 시간대개수_최소
)
WITH hourly AS (
  -- (1) 날짜×시간대×행정동 단위로 거주지유형을 합산(중복 제거)
  SELECT
    기준일ID,
    시간대구분,
    행정동코드,
    SUM(총생활인구수) AS 생활인구_시간대
  FROM stg_metro_people_snapshot
  GROUP BY 기준일ID, 시간대구분, 행정동코드
),
daily AS (
  -- (2) 날짜×행정동 단위 대표값(시간대 평균) + 시간대 개수
  SELECT
    기준일ID,
    행정동코드,
    AVG(생활인구_시간대) AS 일평균_생활인구,
    COUNT(*) AS 시간대개수
  FROM hourly
  GROUP BY 기준일ID, 행정동코드
),
quarterly AS (
  -- (3) 분기×행정동 집계
  SELECT
    행정동코드,
    CONCAT(
      SUBSTR(기준일ID, 1, 4),
      'Q',
      QUARTER(STR_TO_DATE(기준일ID, '%Y%m%d'))
    ) AS 기준분기,
    AVG(일평균_생활인구) AS 유동인구_분기평균,
    MAX(일평균_생활인구) AS 유동인구_분기최대,
    COUNT(*) AS 관측일수,
    AVG(시간대개수) AS 시간대개수_평균,
    MIN(시간대개수) AS 시간대개수_최소
  FROM daily
  GROUP BY 행정동코드,
    CONCAT(SUBSTR(기준일ID, 1, 4), 'Q', QUARTER(STR_TO_DATE(기준일ID, '%Y%m%d')))
)
SELECT
  행정동코드, 기준분기,
  유동인구_분기평균, 유동인구_분기최대,
  관측일수, 시간대개수_평균, 시간대개수_최소
FROM quarterly
ON DUPLICATE KEY UPDATE
  유동인구_분기평균 = VALUES(유동인구_분기평균),
  유동인구_분기최대 = VALUES(유동인구_분기최대),
  관측일수 = VALUES(관측일수),
  시간대개수_평균 = VALUES(시간대개수_평균),
  시간대개수_최소 = VALUES(시간대개수_최소),
  load_ts = CURRENT_TIMESTAMP;


-- 확인 
SELECT 기준분기,
       MIN(관측일수) AS min_days,
       AVG(관측일수) AS avg_days,
       MAX(관측일수) AS max_days
FROM agg_livingpop_dong_quarter
GROUP BY 기준분기
ORDER BY 기준분기;


