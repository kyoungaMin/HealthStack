# 🗄️ Database Design (Supabase / PostgreSQL)

이 문서는 Health Stack 서비스의 DB 설계 원칙, 보안(RLS), 네이밍 규칙, 마이그레이션 운영 전략을 정의합니다.

---

## 1. 설계 철학

### 1) 의료 행위가 아닌 “관리 & 판단 보조”
- 처방/치료/진단 ❌
- 복용 정보 이해 + 일정 관리 + 근거 기반 정보 제공 ⭕

### 2) 개인정보 최소 수집
- 실명/주소/전화번호/주민번호 저장 ❌
- 이메일도 선택(영수증/결제 목적)

### 3) 개인 데이터는 완전 분리
- 모든 개인 데이터 테이블은 `user_id` 필드 포함
- RLS로 `user_id = auth.uid()`만 접근 가능

---

## 2. 스키마 구성(도메인)

### A. Health Stack (개인화/핵심 기능)
- `user_intake_items`
- `intake_schedules`
- `intake_logs`
- `user_push_tokens`
- `reports`

### B. Content / Curation (공용 콘텐츠)
- `symptom_ingredient_map`
- `recipes`
- `symptom_recipe_map`
- `content_videos`
- `symptom_video_map`
- `ingredient_product_links`

### C. Evidence / RAG (근거 검색)
- `interaction_facts`
- `pubmed_papers`
- `pubmed_embeddings`

### D. Billing
- `plans`
- `subscriptions`
- `payments`

---

## 3. RLS 정책 기준

### 3.1 개인 데이터 테이블 (본인만 CRUD)
정책 패턴:
- SELECT: `user_id = auth.uid()`
- INSERT: `user_id = auth.uid()`
- UPDATE: `user_id = auth.uid()`
- DELETE: `user_id = auth.uid()`

대상:
- `user_profiles`
- `user_intake_items`
- `intake_schedules`
- `intake_logs`
- `user_push_tokens`
- `reports`
- `subscriptions`

### 3.2 결제 테이블 (`payments`)
원칙:
- 웹훅/서버에서만 INSERT/UPDATE (service_role)
- 사용자(클라이언트)는 SELECT만 가능(본인 결제내역 조회)

### 3.3 공용 데이터 테이블 (SELECT 공개)
대상:
- `catalog_drugs`, `catalog_supplements`
- `symptom_ingredient_map`, `recipes`, `content_videos` 등
- `interaction_facts`, `pubmed_*`
- `plans`

원칙:
- anon/authenticated SELECT 허용
- INSERT/UPDATE/DELETE 정책 없음(= service_role만 수행)

---

## 4. 데이터 무결성(Integrity)

### 4.1 주요 FK 관계
- `user_intake_items.user_id → auth.users.id`
- `intake_schedules.intake_item_id → user_intake_items.id`
- `intake_logs.schedule_id → intake_schedules.id`
- `symptom_*_map.symptom_id → disease_master.id`
- `symptom_ingredient_map.rep_code → foods_master.rep_code`
- `subscriptions.plan_code → plans.code`
- `pubmed_embeddings.pmid → pubmed_papers.pmid`

### 4.2 삭제 정책
- 사용자 탈퇴/삭제 시:
  - `ON DELETE CASCADE`로 개인 데이터 연쇄 삭제
- 결제 데이터:
  - `payments.user_id ON DELETE SET NULL`도 고려 가능(정책에 따라)

---

## 5. 네이밍 규칙

### 5.1 테이블
- `snake_case` + 복수형 선호
- 매핑 테이블은 `{domain}_{domain}_map` 패턴
  - 예: `symptom_recipe_map`

### 5.2 컬럼
- `user_id`, `created_at`, `updated_at` 표준화
- 상태값은 `status` + 체크 제약으로 관리
- JSON은 `rules`, `inputs`, `sources` 등 목적 드러내기

### 5.3 인덱스
- `idx_{table}_{cols}` (일반)
- `uq_{table}_{purpose}` (부분 유니크)

---

## 6. pgvector 운영(임베딩)

### 6.1 차원(dimension)
- `pubmed_embeddings.embedding vector(1536)` (현재 기준)
- 임베딩 모델 변경 시 차원도 함께 변경 필요

### 6.2 인덱스
- `ivfflat` + `vector_cosine_ops`
- `lists` 값은 데이터 규모에 맞춰 조정

---

## 7. 마이그레이션 운영 전략

### 7.1 원칙
- DB 변경은 반드시 마이그레이션 SQL로 관리
- RLS/Policy도 마이그레이션에 포함
- 문서 업데이트 필수:
  - `docs/erd/schema.dbml`
  - `docs/erd/*.md` (Mermaid ERD)

### 7.2 권장 폴더 구조(예)
supabase/migrations/
0001_init.sql
0002_health_stack.sql
0003_rag_pubmed.sql
0004_rls_policies.sql


### 7.3 커밋 컨벤션
- `db:` prefix 권장
  - 예: `db: add intake_logs indexes`

---

## 8. 데이터 삭제/보존 정책

- 사용자 요청 시:
  - 복용 스택/스케줄/로그/리포트 즉시 삭제 가능
- 리포트(PDF):
  - 생성 시점 스냅샷
  - 사용자가 삭제하면 storage 파일도 함께 제거(서버 처리 권장)

---

## 9. 체크리스트

- [ ] 개인 테이블에 RLS 적용 여부 확인
- [ ] FK / CASCADE 정상 동작 확인
- [ ] pubmed_embeddings 인덱스 생성 확인
- [ ] schema.dbml 업데이트
- [ ] ERD 문서 업데이트

