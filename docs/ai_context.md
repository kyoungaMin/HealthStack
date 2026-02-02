# AI 공통 컨텍스트 (Donguibogam Project)

## 1. 프로젝트 목표
본 프로젝트는 동의보감(食藥同源) 데이터를 기반으로
다음 두 가지 핵심 기능을 제공한다.

A) 사용자 증상(자연어) → 음식/처방 추천  
B) 음식/재료 검색 → 효능/적응증 탐색

의료 행위를 대체하지 않으며, 모든 정보는 참고용이다.

---

## 2. 핵심 설계 원칙
- 임베딩은 "유니크 텍스트"만 생성한다 (캐시 기반)
- 동일 content는 content_hash + model 기준으로 1회만 임베딩
- row_full(행 전체 본문) 전수 임베딩 금지
- 검색은 벡터 검색 + 정확 검색(필터) 혼합 구조
- 비용 절감과 검색 품질을 동시에 고려한다

---

## 3. 기술 스택
- DB: Supabase (Postgres + pgvector)
- Embedding Model: text-embedding-3-small
- Language: Python
- 크롤링: Ulixee Hero
- UI: Streamlit (MVP), FastAPI 확장 가능

---

## 4. 데이터 규모
- traditional_foods 약 320,000 rows
- 임베딩은 엔티티/요약 중심으로 선별 적용

---

## 5. Embedding 전략
### 5.1 Embedding 캐시
- 테이블: embeddings
- 캐시 키: (content_hash, model)
- 동일 텍스트는 임베딩 재사용

### 5.2 content_type 표준
임베딩은 아래 content_type에 한해서만 생성한다.

- symptom_query        : 사용자 질의(실시간)
- indication           : 효능/적응증 요약
- food_entity          : 음식/식재료 엔티티
- prescription_entity  : 처방 엔티티
- ingredients_core     : 대표 재료(1~5개)

긴 원문/한문/동의어 나열은 임베딩 입력에서 제외한다.

---

## 6. 검색 플로우
### A) 증상 → 추천
1) 사용자 질의 임베딩
2) indication / disease_entity 벡터 검색
3) 연결된 음식/처방 후보 추출
4) 벡터 유사도 + 규칙 기반 재랭킹

### B) 음식/재료 → 효능
1) ingredients_norm 정확 검색으로 후보 축소
2) 선택적 질의 임베딩으로 재랭킹
3) 효능/적응증 결과 반환

---

## 7. 비용 관리 원칙
- 배치 임베딩은 캐시 조회 후 실행
- tokens_used 기록
- 월 자동충전 한도 설정 필수
- 유니크 content_hash 증가율로 비용 감시

---

## 8. Agent 사용 규칙
Cursor AI 작업 시,
모든 Agent는 이 문서를 공통 컨텍스트로 사용한다.

