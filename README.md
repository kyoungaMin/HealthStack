# Health Stack (내몸설명서)

> **전통 지식 × 현대 의학 × AI**를 결합한 개인 맞춤형 건강 이해·관리 플랫폼

---

## 1. 프로젝트 개요

**Health Stack (브랜드명: 내몸설명서)** 는 사용자가 자신의 몸 상태, 증상, 복용 중인 약·건강기능식품, 음식 섭취 정보를 **하나의 스택(Stack)** 으로 관리하고, 이를 기반으로 **이해 가능한 설명 + 실행 가능한 추천**을 제공하는 AI 헬스 인텔리전스 프로젝트입니다.

이 프로젝트는 단순 추천 앱이 아니라,

* 병원 진료 전·후 참고 가능한 **개인 건강 백서(Personal Health Whitepaper)**
* 약·영양제·음식·생활습관을 연결한 **의사결정 보조 시스템**
  을 목표로 합니다.

---

## 2. 문제 정의 (Why)

### 기존 헬스/영양 서비스의 한계

* ❌ 정보가 파편화됨 (약, 영양제, 음식, 논문, 영상이 따로 존재)
* ❌ 전문가 언어 위주 → 일반 사용자는 이해하기 어려움
* ❌ 개인의 실제 복용/섭취/증상 이력과 연결되지 않음
* ❌ "먹어도 되는지 / 같이 먹어도 되는지"에 대한 맥락 부족

### Health Stack의 관점

> **"몸을 이해하지 못하면, 관리도 할 수 없다"**

→ Health Stack은 **설명 가능한 건강 관리**를 핵심 가치로 둡니다.

---

## 3. 핵심 컨셉 (What)

### 🔹 Health Stack이란?

사용자의 건강과 관련된 모든 요소를 **시간축 기반의 스택 구조**로 관리합니다.

* 증상 (Symptoms)
* 질병 이력 (Conditions)
* 복용 약 (Drugs)
* 건강기능식품 (Supplements)
* 음식 / 식재료 (Foods)
* 콘텐츠 근거 (동의보감, PubMed, 논문, 영상)

이 스택을 기반으로 AI가 **연결·해석·설명**합니다.

---

## 4. 주요 기능 (Features)

### 4.1 증상 기반 이해 & 추천

* 사용자가 입력한 증상을 **현대어로 해석**
* 동의보감 + 현대 의학(RAG) 기반 설명
* 도움이 될 수 있는 음식 / 피해야 할 음식 제안

### 4.2 복용 스택 관리

* 현재 복용 중인 약·영양제 등록
* 복용 목적, 기간, 이행률 관리
* **같이 먹어도 되는지 / 피해야 하는 조합** 자동 안내

### 4.3 콘텐츠 큐레이션

* 증상·식재료 기반 추천 영상 (YouTube 등)
* 논문/근거 요약 (PubMed)
* 일반 사용자도 이해 가능한 언어로 재작성

### 4.4 개인 맞춤 PDF 리포트

* 월간/분기별 **내몸설명서 PDF 생성**
* 병원 방문 시 참고 자료로 활용 가능
* 복용 현황, 주요 이슈, 추천 요약 포함

---

## 5. 데이터 & 지식 구조 (How)

### 5.1 데이터 소스

* 📚 동의보감 원문 → 현대어 번역 DB
* 🧪 PubMed / 임상 논문 메타데이터
* 🍽️ 전통 식재료 / 음식 DB (traditional_foods)
* 💊 건강기능식품 / 성분 / 리뷰 데이터

### 5.2 RAG (Retrieval Augmented Generation)

* 증상/질문 → 벡터 검색
* 관련 지식 조합 후 LLM 응답 생성
* **근거 기반 답변 + 출처 유지**

---

## 6. 시스템 아키텍처

### 6.1 기술 스택

* **Frontend**: React + Tailwind
* **Backend**: FastAPI
* **DB**: PostgreSQL (Supabase)
* **Vector DB**: pgvector
* **Cache / Rate Limit**: Redis (Upstash)
* **AI**: LLM + Embedding 기반 RAG

### 6.2 주요 도메인

* User / Auth
* Health Stack (Symptoms, Drugs, Supplements)
* Food & Content
* Report / PDF

---

## 7. ERD & 문서 구조

```text
## 7. 문서 구조

### 7.1 아키텍처 다이어그램
- `docs/architecture/architecture.md` — 시스템 아키텍처 (React ↔ FastAPI ↔ Supabase ↔ pgvector ↔ Redis)
- `docs/architecture/report-pipeline.md` — PDF 리포트 생성 파이프라인
- `docs/architecture/one-page-concept.md` — IR/공모전용 한 장 개념도

### 7.2 ERD & 상세 문서

/docs
 ├─ erd/
 │   ├─ erd-health-stack.md
 │   ├─ erd-content-rag-billing.md
 │   ├─ erd-full.md
 │   └─ schema.dbml
 ├─ pdf/
 │   └─ pdf_generation_rules.v1.json
 └─ README.md
```

---

## 8. 차별점 (Why Health Stack)

* ✅ "추천"보다 **이해**에 집중
* ✅ 전통 의학 + 현대 의학의 구조적 결합
* ✅ 개인 데이터 중심 (내 기록이 핵심)
* ✅ 병원·전문가와 함께 쓰기 좋은 형태

---

## 9. 확장 로드맵

### Phase 1: MVP

* 증상 → 음식/콘텐츠 추천
* 기본 Health Stack 관리

### Phase 2: 고도화

* 복용 충돌 분석
* 개인 맞춤 리포트 자동화

### Phase 3: 비즈니스

* 구독형 리포트
* 전문가 협업 (약사/영양사)
* B2B / 헬스케어 연동

---

## 10. 비전

> **Health Stack은 "건강 정보를 소비하는 서비스"가 아니라
> "내 몸을 이해하는 인프라"를 만드는 프로젝트입니다.**

---

## 11. 프로젝트 네이밍

* 프로젝트 코드명: **Health Stack**
* 서비스명: **내몸설명서**
* 슬로건: *"내 몸을 이해하는 가장 쉬운 방법"*

---

## 12. 상태

* 🚧 현재 상태: 설계 및 MVP 개발 중
* 🧠 AI / 데이터 구조 지속 개선 중

---

필요 시:

* Investor Deck 버전 README
* 개발자 전용 README (Setup / ENV)
* 사용자용 소개 페이지

👉 언제든지 확장 가능
