# 🧩 ERD Documentation

이 폴더는 **Health Stack 서비스의 데이터베이스 구조(ERD)**를 관리합니다.  
설계 의도, 도메인 분리, 실제 DB 기준 구조를 **명확하게 문서화**하는 것이 목적입니다.

> ⚠️ 주의  
> 이 ERD는 **의료 판단/처방 시스템이 아닌 "건강 판단 보조 & 관리 서비스"**를 전제로 설계되었습니다.

---

## 📁 폴더 구성

```
docs/erd/
├── readme.md                      ← 📍 현재 문서
├── schema.integrated.dbml         ← 🔑 통합 스키마 (Source of Truth)
│
├── erd-full.md                    ← 전체 통합 ERD
├── erd-health-stack.md            ← 복용 스택 / 스케줄 / 알림
├── erd-content-rag-billing.md     ← 콘텐츠 / RAG / 결제
├── erd-integrated.md              ← 통합 ERD (상세 버전)
│
├── erd-core-tables.png            ← 📊 핵심 테이블 이미지
└── erd-restaurant-session.png     ← 📊 레스토랑/세션 이미지
```

---

## 📌 파일별 역할 설명

### 🔑 `schema.integrated.dbml`
**(DBML / 실제 DB 기준 — Source of Truth)**

- **범위**: Supabase(PostgreSQL)에 적용된 **실제 스키마 전체**
- **테이블 수**: 40개
- **특징**:
  - PK / FK / 타입 정확하게 정의
  - 모든 ERD 문서의 기준
- **사용 도구**:
  - [dbdiagram.io](https://dbdiagram.io)
  - DBeaver / DataGrip

👉 **"DB 구조의 단일 진실(Source of Truth)"**

---

### 1️⃣ `erd-full.md`
**(Mermaid ER Diagram / 전체 통합)**

- **범위**: 전체 40개 테이블 통합
- **포함 도메인**:
  - 사용자 인증 & 프로필
  - 복용 관리
  - 콘텐츠 매핑
  - 상호작용 & RAG
  - 결제 & 구독
  - 입력 세션 레이어
  - 레스토랑 추천
  - 카탈로그 코드
  - 캐시 테이블
- **용도**:
  - 신규 개발자 온보딩
  - 아키텍처 리뷰
  - 전체 구조 빠른 이해

👉 **"한 장으로 보는 전체 그림"**

---

### 2️⃣ `erd-health-stack.md`
**(Mermaid ER Diagram / 개인 데이터 중심)**

- **범위**:
  - 사용자 복용 스택 (약 / 건강기능식품 / 음식)
  - 복용 스케줄 & 로그
  - 알림 토큰
  - 개인 리포트(PDF 등)
- **특징**:
  - 개인 데이터 중심
  - `user_id = auth.uid()` 기반 RLS 전제
  - Enum 값 문서화
- **용도**:
  - 서비스 핵심 기능 설명
  - 기획자·개발자 간 커뮤니케이션

👉 **"사용자가 실제로 쓰는 기능의 데이터 구조"**

---

### 3️⃣ `erd-content-rag-billing.md`
**(Mermaid ER Diagram / 공용 데이터 중심)**

- **범위**:
  - 증상 기반 식재료 / 레시피 / 영상 큐레이션
  - 동의보감 기반 식이 데이터
  - PubMed 기반 RAG (논문 + 임베딩)
  - 결제 / 구독 / 수익화 구조
  - 캐시 테이블 (YouTube / 커머스)
- **특징**:
  - 공용 데이터 중심
  - 읽기 위주(SELECT), 쓰기는 서버 권장
  - pgvector 설정 가이드 포함
- **용도**:
  - 콘텐츠·AI·수익화 구조 설명

👉 **"근거 + 콘텐츠 + 돈이 연결되는 영역"**

---

### 4️⃣ `erd-integrated.md`
**(Mermaid ER Diagram / 상세 버전)**

- **범위**: 전체 스키마 상세 ERD
- **특징**:
  - 모든 컬럼 포함
  - 도메인별 분류 표
  - 관계 요약 다이어그램
- **용도**:
  - 상세 구조 확인
  - 컬럼 레벨 참조

👉 **"컬럼까지 보고 싶을 때"**

---

### 📊 이미지 파일

| 파일 | 설명 |
|------|------|
| `erd-core-tables.png` | 핵심 테이블 ERD (사용자/복용/콘텐츠/결제) |
| `erd-restaurant-session.png` | 확장 테이블 ERD (세션/레스토랑/캐시) |

👉 **외부 공유/발표용 스냅샷**

---

## 📊 테이블 통계

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
| **총계** | **40** |

---

## 🧠 ERD 설계 원칙

### ✅ 1. 도메인 분리
- **Health Stack** (개인 관리) — 복용/스케줄/로그
- **Content / RAG** (공용 근거) — 증상/식재료/논문
- **Billing** (수익화) — 플랜/구독/결제
- **Session** (입력 처리) — 증상/처방전 입력
- **Restaurant** (외부 연동) — 지도 API 기반 추천

### ✅ 2. 개인 정보 최소화
- 민감 정보 저장 ❌
- 복용 정보는 "기록 & 관리" 수준
- 치료/처방 판단 로직 ❌

### ✅ 3. RLS 우선 설계

**개인 데이터** (`user_id = auth.uid()` RLS):
- `user_profiles`, `user_preferences`
- `user_intake_items`, `intake_schedules`, `intake_logs`
- `user_push_tokens`, `reports`
- `user_input_sessions`, `user_symptoms`, `user_prescriptions`
- `user_restaurant_favorites`, `user_restaurant_visit_logs`
- `subscriptions`, `payments`

**공용 데이터** (읽기 허용):
- `foods_master`, `disease_master`
- `catalog_drugs`, `catalog_supplements`
- `recipes`, `content_videos`
- `symptom_*_map`, `interaction_facts`
- `pubmed_papers`, `pubmed_embeddings`
- `restaurants`, `restaurant_menus`
- `catalog_*_codes`

---

## 🔁 ERD 유지·업데이트 규칙

### DB 구조 변경 시
1. Supabase 마이그레이션 SQL 적용
2. `schema.integrated.dbml` **반드시 업데이트** (Source of Truth)
3. 변경 영향이 있는 Mermaid ERD 수정
4. 필요시 이미지 재생성
5. 커밋 메시지에 `db:` prefix 권장  
   - 예: `db: add restaurant_search_requests table`

### 이미지 재생성
- AI 도구로 새 이미지 생성
- `docs/erd/` 폴더에 저장
- 관련 `.md` 파일에서 이미지 경로 확인

---

## 🧪 권장 활용 흐름

| 목적 | 사용 파일 |
|------|----------|
| 설계/설명 | Mermaid ERD (`.md`) |
| 정확한 구조 확인 | DBML (`schema.integrated.dbml`) |
| 외부 공유/발표 | 이미지 (`.png`) |
| 신규 온보딩 | `erd-full.md` |
| 특정 도메인 이해 | `erd-health-stack.md` 또는 `erd-content-rag-billing.md` |

---

## ✨ 한 줄 요약

> **Mermaid ERD는 "이해를 돕기 위한 지도"이고,  
> DBML은 "실제 지형도"다.**

---

## 📎 참고

- Supabase ERD는 콘솔에서 직접 제공되지 않음
- 실제 ERD 시각화는 외부 도구 사용 권장:
  - [dbdiagram.io](https://dbdiagram.io) — DBML 렌더링
  - [Mermaid Live Editor](https://mermaid.live/) — Mermaid 다이어그램
- 본 문서는 개발·기획·AI 설계를 연결하는 기준 문서임
- **최종 업데이트**: 2026-02-04
