# 📚 Documentation

이 폴더는 **Health Stack 서비스의 설계 문서**를 관리합니다.  
Supabase 기반 DB 설계, ERD, 아키텍처, API 기준 문서를 포함합니다.

---

## 🧭 문서 구조

docs/
├─ erd/
│ ├─ erd-health-stack.md # 복용 스택 / 알림 / 리포트 ERD (Mermaid)
│ ├─ erd-content-rag-billing.md # 콘텐츠 / RAG / 결제 ERD (Mermaid)
│ ├─ erd-full.md # 전체 ERD (Mermaid)
│ └─ schema.dbml # 실제 DB 기준 ERD (dbdiagram.io)
│
├─ architecture.md # 시스템 아키텍처 개요
├─ database.md # DB 설계 철학 & 규칙
├─ api.md # API 엔드포인트 설계
└─ README.md 


---

## 🗂 ERD 사용 가이드

### 1. Mermaid ERD (`.md`)
- **용도**: 설계 설명 / 문서 / 커뮤니케이션
- GitHub, Notion, Obsidian에서 자동 렌더링
- 도메인 개념 이해에 최적

### 2. DBML (`schema.dbml`)
- **용도**: 실제 DB 구조 시각화
- 사용 도구:
  - https://dbdiagram.io
  - DBeaver
  - DataGrip
- FK 기반 자동 ERD 생성

---

## 🧠 DB 설계 철학 요약

- 치료/처방 ❌
- 판단 보조 + 관리 ⭕
- 개인 데이터 최소 수집
- 모든 개인 데이터는 `user_id = auth.uid()` 기준으로 보호 (RLS)
- PubMed 기반 근거 검색은 **RAG 구조로 분리**

---

## 🔐 보안 및 권한

- Supabase RLS 활성화
- 개인 데이터 테이블:
  - `user_intake_items`
  - `intake_schedules`
  - `intake_logs`
  - `reports`
  - `subscriptions`
- 공용 데이터:
  - 식재료 / 증상 / 콘텐츠 / PubMed

---

## 🧪 참고

- DB 변경 시:
  1. 마이그레이션 SQL 적용
  2. `schema.dbml` 업데이트
  3. Mermaid ERD 반영

---

## ✨ 한 줄 요약

> **이 문서들은 “왜 이렇게 설계했는지”를 남기기 위한 기록이다.**
