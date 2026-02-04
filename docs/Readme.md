# 📚 Health Stack Documentation

이 폴더는 **Health Stack 서비스의 설계 문서**를 관리합니다.  
Supabase 기반 DB 설계, ERD, 아키텍처, API 기준 문서를 포함합니다.

> **서비스 정의**: 사용자가 입력한 증상과 처방전을 바탕으로, 약·건강정보·동의보감·음식·지역 식당·판매처를 하나의 맥락으로 연결해 "내 몸에 지금 필요한 선택지"를 설명해주는 서비스

**최종 업데이트**: 2026-02-04

---

## 🧭 문서 구조

```
docs/
├── README.md                        ← 📍 현재 문서
├── SERVICE_PLAN.md                  ← 서비스 기획안 (핵심)
│
├── erd/                             ← 📊 ERD & 스키마
│   ├── readme.md                    ← ERD 문서 가이드
│   ├── schema.integrated.dbml      ← 🔑 통합 스키마 (Source of Truth)
│   ├── erd-full.md                  ← 전체 ERD (40개 테이블)
│   ├── erd-health-stack.md          ← 복용 스택 / 알림 / 리포트
│   ├── erd-content-rag-billing.md   ← 콘텐츠 / RAG / 결제
│   ├── erd-integrated.md            ← 상세 ERD
│   ├── erd-core-tables.png          ← 핵심 테이블 이미지
│   └── erd-restaurant-session.png   ← 레스토랑/세션 이미지
│
├── architecture/                    ← 🏗️ 아키텍처
│   ├── architecture.md              ← 시스템 아키텍처 개요
│   ├── one-page-concept.md          ← 서비스 컨셉 요약
│   └── report-pipeline.md           ← 리포트 생성 파이프라인
│
├── api.md                           ← 🔌 API 설계 (45개 엔드포인트)
├── database.md                      ← DB 설계 철학 & 규칙
├── design_guide.md                  ← UI/UX 디자인 가이드
├── WORKFLOW.md                      ← 서비스 워크플로우
│
├── ai_context.md                    ← AI 컨텍스트 설정
├── embedding_and_search_design.md   ← 임베딩 & 검색 설계
├── EMBEDDING_OPTIMIZATION.md        ← 임베딩 최적화
├── embeding_prompt.md               ← 임베딩 프롬프트
├── CRAWLING_DESIGN.md               ← 크롤링 설계
├── MVP_to_Deploy_Agent_Routine.md   ← MVP 배포 루틴
│
└── prompt/                          ← 프롬프트 템플릿
```

---

## � 핵심 문서 가이드

### 1️⃣ 서비스 기획

| 문서 | 설명 |
|------|------|
| [SERVICE_PLAN.md](./SERVICE_PLAN.md) | 서비스 정의, 입력 방식, 제공 정보 구조 |
| [WORKFLOW.md](./WORKFLOW.md) | 사용자 플로우, 시스템 처리 흐름 |

---

### 2️⃣ 데이터베이스 (ERD)

| 문서 | 설명 |
|------|------|
| [erd/readme.md](./erd/readme.md) | ERD 문서 가이드, 테이블 통계 |
| [erd/schema.integrated.dbml](./erd/schema.integrated.dbml) | **Source of Truth** - 40개 테이블 정의 |
| [erd/erd-full.md](./erd/erd-full.md) | 전체 통합 ERD |

**테이블 통계** (총 40개):

| 도메인 | 테이블 수 |
|--------|----------|
| 사용자 인증 & 프로필 | 4 |
| 마스터 데이터 | 4 |
| 복용 관리 | 3 |
| 콘텐츠 매핑 | 6 |
| 상호작용 & RAG | 3 |
| 결제 & 구독 | 4 |
| 입력 세션 레이어 | 5 |
| 레스토랑 추천 | 7 |
| 카탈로그 코드 | 2 |
| 캐시 테이블 | 2 |

---

### 3️⃣ 아키텍처

| 문서 | 설명 |
|------|------|
| [architecture/architecture.md](./architecture/architecture.md) | 시스템 구성, 데이터 흐름 |
| [architecture/one-page-concept.md](./architecture/one-page-concept.md) | 서비스 컨셉 한 장 요약 |
| [architecture/report-pipeline.md](./architecture/report-pipeline.md) | PDF 리포트 생성 파이프라인 |

---

### 4️⃣ API 설계

| 문서 | 설명 |
|------|------|
| [api.md](./api.md) | API 엔드포인트 설계 (45개) |

**API 도메인 요약**:

| 도메인 | 엔드포인트 | 주요 기능 |
|--------|-----------|----------|
| Auth/Profile | 3 | 프로필 조회/수정, 푸시 토큰 |
| Intake Stack | 4 | 복용 항목 CRUD |
| Schedules | 8 | 스케줄 CRUD, 복용 체크 |
| Input Sessions | 6 | 증상/처방전 세션 관리 |
| Interaction | 1 | 조합 분석 |
| Symptom Content | 3 | 증상 기반 콘텐츠 |
| Restaurant | 5 | 음식점 검색/즐겨찾기 |
| PubMed RAG | 2 | 근거 검색 |
| Reports | 2 | 리포트 생성/조회 |
| Billing | 4 | 구독/결제 |
| Catalog | 4 | 카탈로그 검색 |
| Admin | 3 | 캐시/동기화 관리 |

---

## 🧠 설계 철학 요약

### 서비스 원칙
- 치료 ❌ / 처방 변경 ❌ / 과장 ❌
- **이해 + 판단 보조 + 생활 선택 가이드 ⭕**

### DB 설계 원칙
- 개인 데이터 최소 수집
- 모든 개인 데이터는 `user_id = auth.uid()` 기준으로 보호 (RLS)
- PubMed 기반 근거 검색은 **RAG 구조로 분리**
- 외부 API 응답은 **캐시 테이블**로 비용 절감

---

## 🔐 보안 및 권한 (RLS)

### 개인 데이터 (본인만 접근)
- `user_profiles`, `user_preferences`
- `user_intake_items`, `intake_schedules`, `intake_logs`
- `user_push_tokens`, `reports`
- `user_input_sessions`, `user_symptoms`, `user_prescriptions`
- `user_restaurant_favorites`, `user_restaurant_visit_logs`
- `subscriptions`, `payments`

### 공용 데이터 (읽기 허용)
- `foods_master`, `disease_master`
- `catalog_drugs`, `catalog_supplements`
- `recipes`, `content_videos`
- `symptom_*_map`, `interaction_facts`
- `pubmed_papers`, `pubmed_embeddings`
- `restaurants`, `restaurant_menus`
- `plans`

---

## 🔁 문서 유지·업데이트 규칙

### DB 구조 변경 시
1. Supabase 마이그레이션 SQL 적용
2. `schema.integrated.dbml` 업데이트 (Source of Truth)
3. 관련 Mermaid ERD 반영
4. 필요시 API 문서 수정
5. 커밋 메시지에 `db:` prefix 권장

### API 변경 시
1. `api.md` 업데이트
2. 관련 DB 테이블 확인
3. 커밋 메시지에 `api:` prefix 권장

---

## 🧪 권장 활용 흐름

| 목적 | 사용 문서 |
|------|----------|
| 서비스 이해 | `SERVICE_PLAN.md` |
| DB 구조 파악 | `erd/erd-full.md` → `schema.integrated.dbml` |
| API 개발 | `api.md` |
| 아키텍처 리뷰 | `architecture/architecture.md` |
| 신규 온보딩 | 이 README → 각 문서 순서대로 |

---

## ✨ 한 줄 요약

> **이 문서들은 "왜 이렇게 설계했는지"를 남기기 위한 기록이다.**

---

## 📎 외부 도구 링크

- [dbdiagram.io](https://dbdiagram.io) - DBML 렌더링
- [Mermaid Live Editor](https://mermaid.live/) - Mermaid 다이어그램
- [Supabase](https://supabase.com) - Backend 플랫폼
