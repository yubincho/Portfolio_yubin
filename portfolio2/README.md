
 <img src="docs/logo.jpg" alt="BitAnalyzer" width="160" height="200">

# BitAnalyzer — 개인 암호화폐 거래 분석 시스템

빗썸 API로 개인 거래 데이터를 수집하고, 거래 내역을 정제·저장하는
데이터 파이프라인을 구축한 개인 프로젝트입니다.
Java Spring 백엔드와 Python 분석 서비스를 분리한
세미 마이크로서비스 구조로 설계했습니다.

<br>

## 프로젝트 목표
개인 거래 데이터를 수집·정제·저장하는 파이프라인을 만들고,
운영 DB(PostgreSQL)에 적재한 데이터를 분석용 웨어하우스(BigQuery)로
이관하는 흐름까지 구성하는 것을 목표로 합니다.

<br>

## 기술 스택
| 영역 | 기술 |
|------|------|
| Backend | Java, Spring Boot, Gradle |
| Database | PostgreSQL (운영/트랜잭션 데이터) |
| Data Warehouse | Google BigQuery (분석용, 이관 예정) |
| Analysis | Python |
| Data Source | 빗썸 API, 개인 거래 내역 파일 |

<br>

## 아키텍처
- `backend/` — Spring Boot 기반 API 서버 (데이터 수집·저장)
- `ml-service/` — Python 기반 데이터 정제 및 분석 서비스
- PostgreSQL — 수집·정제한 거래 데이터를 적재하는 운영 DB

<br>

## 현재까지 구현
- 빗썸 API 연동으로 개인 거래·자산 데이터 수집
- 거래 데이터 저장용 테이블 설계
- 거래 내역 파일 정제·표준화

<br>

## 진행 예정
- PostgreSQL → BigQuery 데이터 이관(마이그레이션) 배치 구성
- BigQuery 기반 거래 패턴 분석
- (검토 중) 분석 지표 대시보드

