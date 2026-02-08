# Health Stack Agent Map (v2 - DB Schema & Feature Aligned)

# AGENT MAP (운영 관문)

이 폴더의 에이전트들은 "개발 운영체계"처럼 사용한다.
원칙:
- 한 번에 한 agent만 호출 → 결과물(Output)을 다음 agent의 Context로 넘긴다.
- 형식(Output)은 SNIPPETS를 기준으로 고정한다.
- API 변경은 문서보다 API_MOCK.json을 먼저 갱신한다(SSOT).

---

## 공통 입력 계약 (모든 agent 요청에 사용)
아래 템플릿을 복사해 요청한다.

- Goal: (이번 요청의 최종 결과 1줄)
- Context:
  - (기존 결정/제약 3~5줄)
  - (연관 파일: API_MOCK.json / SNIPPETS.json / README 등)
- Output:
  - (원하는 산출물 형식: md/json/sql/ts)
  - (섹션 구성/길이/표현 톤/제약)

---

## SSOT(단일 진실 소스)
- API: API_MOCK.json
- 문서/템플릿: SNIPPETS.json, AGENT_SNIPPETS.txt
- DB Schema: docs/erd/schema.integrated.dbml
- 운영 가이드: README_AGENT_GUIDE.md, USAGE.md

---

## Agent Directory (언제/무엇/다음 단계)

### 01_product-philosophy-guard.md
- When to use: 기능/정책/제품원칙을 먼저 잡아야 할 때(범위, 금지, 성공지표)
- Output: PRD 1페이지(문제/대상/가치/범위/비범위/지표/리스크)
- Handoff: → 09_backend-api-architect / 08_frontend-ux / 12_docs-policy-writer

### 02_medical-info-summary.md
- When to use: 의학/영양 정보 요약(근거 수준, 주의/금기 포함), 질병-영양소 매핑 근거
- Output: 근거 요약 + 주의사항 + 표현 가드레일(과장 금지 문구 포함)
- Handoff: → 04_donguibogam-lifestyle / 07_notification-tone / 12_docs-policy-writer / 10_pdf-report-generator

### 03_interaction-analysis.md
- When to use: 사용자 흐름/행동 설계, 입력-출력 UX, 실수 패턴 분석
- Output: 사용자 여정/실패 케이스/마찰 포인트/개선안
- Handoff: → 08_frontend-ux / 11_qa-risk-audit

### 04_donguibogam-lifestyle.md
- When to use: 동의보감 기반 현대 해석, 라이프스타일 톤/서사, `tkm_symptom_master` 활용
- Output: 콘텐츠 초안 + 금기/주의(TKM 매핑 근거 포함)
- Handoff: → 02_medical-info-summary(검증) / 07_notification-tone / 10_pdf-report-generator

### 05_meal-plan.md
- When to use: 식단 추천(메뉴 구성, 장보기 리스트, 대체식), `recipes` 테이블 활용
- Output: 3~7일 식단 + 레시피 요약 + 구매 리스트
- Handoff: → 06_intake-schedule-optimizer / 10_pdf-report-generator / 11_qa-risk-audit

### 06_intake-schedule-optimizer.md
- When to use: 복용 스케줄/섭취 타이밍 최적화(상호작용, 커피/약/영양제 등), `intake_schedules` 관리
- Output: 시간표 + 주의사항 + 예외 처리 규칙
- Handoff: → 07_notification-tone / 10_pdf-report-generator / 11_qa-risk-audit

### 07_notification-tone.md
- When to use: 푸시/메일/인앱 알림 카피 통일(친근/중립/엄숙)
- Output: 길이별(60/120/메일) 문구 + 변수 템플릿
- Handoff: → 12_docs-policy-writer / 11_qa-risk-audit / 08_frontend-ux

### 08_frontend-ux.md
- When to use: 화면 구조/섹션 설계, 컴포넌트 리스트, 정보 위계
- Output: IA + 화면별 섹션 + 컴포넌트/상태(loading/empty/error)
- Handoff: → 09_backend-api-architect(API 요구사항 명확화) / 11_qa-risk-audit

### 09_backend-api-architect.md
- When to use: DB/API 설계, RLS, 캐시/큐(Upstash/Redis), 스키마 마이그레이션 전략
- Output: API_SPEC + DB 스키마(DBML) + 에러 규격 + API_MOCK.json 업데이트안
- Handoff: → 08_frontend-ux / 10_pdf-report-generator / 11_qa-risk-audit

### 10_pdf-report-generator.md
- When to use: PDF 리포트 구조/데이터 계약/렌더 규칙 확정, `reports` 테이블 활용
- Output: 섹션별 입력 JSON 스키마 + 렌더 규칙 + 샘플 데이터
- Handoff: → 09_backend-api-architect(데이터 수집 보완) / 11_qa-risk-audit / 12_docs-policy-writer

### 11_qa-risk-audit.md
- When to use: 엣지케이스/정책 리스크/테스트케이스 작성
- Output: Given-When-Then 테스트케이스 + 위험도 라벨 + 체크리스트
- Handoff: → 09_backend-api-architect / 08_frontend-ux / 12_docs-policy-writer

### 12_docs-policy-writer.md
- When to use: 면책/고지/약관/표현 가이드(특히 의료/건강)
- Output: 정책 문구 세트 + UI 삽입 위치 가이드 + 금지 표현 리스트
- Handoff: → 07_notification-tone / 10_pdf-report-generator / 11_qa-risk-audit

### 13_medication-analyzer.md (NEW)
- When to use: 처방전 OCR 분석, 약물 상호작용 체크, `user_prescriptions` 처리 로직
- Output: OCR 파싱 규칙 + 약물 매핑 로직 + 주의사항/부작용 경고 문구
- Handoff: → 02_medical-info-summary / 09_backend-api-architect

### 14_local-search-agent.md (NEW)
- When to use: 지도/식당 검색 전략, `restaurants` 테이블 및 캐싱(`restaurant_search_requests`) 전략
- Output: 검색 쿼리 템플릿 + 필터링 규칙 + 결과 랭킹 로직
- Handoff: → 05_meal-plan / 09_backend-api-architect

### 15_knowledge-curator.md (NEW)
- When to use: FAQ(Golden Questions) 관리, RAG 지식 베이스 업데이트, `tkm_symptom_master` 정제
- Output: FAQ 리스트 + 지식 베이스(Chunk) 가이드 + 검색 키워드 최적화
- Handoff: → 09_backend-api-architect / 08_frontend-ux

---

## 표준 개발 루틴 (권장 순서)
1) 01_product-philosophy-guard
2) 09_backend-api-architect (API_MOCK.json & DBML 먼저 갱신)
3) 08_frontend-ux
4) 15_knowledge-curator (FAQ/Data 준비)
5) 13_medication-analyzer & 14_local-search-agent (핵심 기능 로직)
6) 10_pdf-report-generator
7) 11_qa-risk-audit
8) 07_notification-tone
9) 12_docs-policy-writer
