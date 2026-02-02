# 🧩 ERD Documentation

이 폴더는 **Health Stack 서비스의 데이터베이스 구조(ERD)**를 관리합니다.  
설계 의도, 도메인 분리, 실제 DB 기준 구조를 **명확하게 문서화**하는 것이 목적입니다.

> ⚠️ 주의  
> 이 ERD는 **의료 판단/처방 시스템이 아닌 “건강 판단 보조 & 관리 서비스”**를 전제로 설계되었습니다.

---

## 📁 폴더 구성

docs/erd/
├─ erd-health-stack.md
├─ erd-content-rag-billing.md
├─ erd-full.md
└─ schema.dbml


---

## 📌 파일별 역할 설명

### 1️⃣ `erd-health-stack.md`
**(Mermaid ER Diagram / Markdown)**

- 범위
  - 사용자 복용 스택 (약 / 건강기능식품 / 음식)
  - 복용 스케줄 & 로그
  - 알림 토큰
  - 개인 리포트(PDF 등)
- 특징
  - 개인 데이터 중심
  - `user_id = auth.uid()` 기반 RLS 전제
- 용도
  - 서비스 핵심 기능 설명
  - 기획자·개발자 간 커뮤니케이션

👉 **“사용자가 실제로 쓰는 기능의 데이터 구조”**

---

### 2️⃣ `erd-content-rag-billing.md`
**(Mermaid ER Diagram / Markdown)**

- 범위
  - 증상 기반 식재료 / 레시피 / 영상 큐레이션
  - 동의보감 기반 식이 데이터
  - PubMed 기반 RAG (논문 + 임베딩)
  - 결제 / 구독 / 수익화 구조
- 특징
  - 공용 데이터 중심
  - 읽기 위주(SELECT), 쓰기는 서버 권장
- 용도
  - 콘텐츠·AI·수익화 구조 설명

👉 **“근거 + 콘텐츠 + 돈이 연결되는 영역”**

---

### 3️⃣ `erd-full.md`
**(Mermaid ER Diagram / Markdown)**

- 범위
  - 전체 도메인 통합 ERD
- 특징
  - 컬럼 최소화
  - 관계 중심 요약
- 용도
  - 신규 개발자 온보딩
  - 아키텍처 리뷰
  - 전체 구조 빠른 이해

👉 **“한 장으로 보는 전체 그림”**

---

### 4️⃣ `schema.dbml`
**(DBML / 실제 DB 기준)**

- 범위
  - Supabase(PostgreSQL)에 적용된 **실제 스키마**
- 특징
  - PK / FK / 타입 중심
  - Mermaid보다 정확도 우선
- 사용 도구
  - https://dbdiagram.io
  - DBeaver
  - DataGrip

👉 **“DB 구조의 단일 진실(Source of Truth)”**

---

## 🧠 ERD 설계 원칙

### ✅ 1. 도메인 분리
- Health Stack (개인 관리)
- Content / RAG (공용 근거)
- Billing (수익화)

### ✅ 2. 개인 정보 최소화
- 민감 정보 저장 ❌
- 복용 정보는 “기록 & 관리” 수준
- 치료/처방 판단 로직 ❌

### ✅ 3. RLS 우선 설계
- 개인 데이터:
  - `user_intake_items`
  - `intake_schedules`
  - `intake_logs`
  - `reports`
  - `subscriptions`
- 공용 데이터:
  - 식재료 / 증상 / 콘텐츠 / PubMed

---

## 🔁 ERD 유지·업데이트 규칙

### DB 구조 변경 시
1. Supabase 마이그레이션 SQL 적용
2. `schema.dbml` **반드시 업데이트**
3. 변경 영향이 있는 Mermaid ERD 수정
4. 커밋 메시지에 `db:` prefix 권장  
   - 예: `db: add intake_schedules rules json`

---

## 🧪 권장 활용 흐름

- **설계/설명** → Mermaid ERD (`.md`)
- **정확한 구조 확인** → DBML (`schema.dbml`)
- **외부 공유/발표** → ERD 스냅샷(PNG/SVG)

---

## ✨ 한 줄 요약

> **Mermaid ERD는 “이해를 돕기 위한 지도”이고,  
> DBML은 “실제 지형도”다.**

---

## 📎 참고

- Supabase ERD는 콘솔에서 직접 제공되지 않음
- 실제 ERD 시각화는 외부 도구 사용 권장
- 본 문서는 개발·기획·AI 설계를 연결하는 기준 문서임
