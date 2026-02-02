# 🚀 MVP → 배포까지 Agent 자동 루틴

이 문서는 **동의보감(식약동원) 앱 프로젝트**를 기준으로,
아이디어 단계부터 실제 배포까지 **Agent를 활용해 혼자서 팀처럼 개발하는 표준 루틴**입니다.

---

## 🧭 전체 개요

> 목적: **막힘 없이 MVP를 완성하고 안정적으로 배포하기**

```text
기획 → UI 설계 → 구현 → 테스트 → 검증 → 정리 → 버그 점검 → 문서화 → 배포
```

---

## STEP 0. 문제 정의 & MVP 범위 고정

### 🎯 목표

* 이번 배포에서 **반드시 포함할 기능**과 **의도적으로 제외할 기능**을 명확히 구분

### 🧠 사용 Agent

**product-designer-critic**

```text
Use product-designer-critic.
동의보감 앱 MVP 범위를 정의해줘.
반드시 필요한 기능과 이번엔 제외해야 할 기능을 구분해줘.
```

### 📦 산출물

* MVP 기능 목록
* 제외 기능 목록 (Backlog)

---

## STEP 1. UI 방향 & 화면 설계

### 🎯 목표

* 디자인 방향 흔들림 방지
* 전체 화면 구조 선행 정의

### 🧠 사용 Agent

**donguibogam-smithery-ui-designer**

```text
Use donguibogam-smithery-ui-designer.
동의보감 앱 MVP 기준 홈/증상/식재료 화면 UI를 설계해줘.
```

### 📦 산출물

* 화면 구조
* 카드/섹션 구성
* 컬러 & 톤 기준

---

## STEP 2. 프론트엔드 구현 (실코드)

### 🎯 목표

* 바로 실행 가능한 UI 코드 확보

### 🧠 사용 Agent

**frontend-tailwind-engineer**

```text
Use frontend-tailwind-engineer.
STEP 1에서 설계한 홈 화면을 React + Tailwind로 구현해줘.
```

> Streamlit 사용 시

```text
Use frontend-tailwind-engineer.
동의보감 MVP를 Streamlit 기준으로 화면 구조 구현해줘.
```

### 📦 산출물

* 실행 가능한 컴포넌트
* 기본 레이아웃 완성

---

## STEP 3. 기능 테스트 & UX 검증

### 🎯 목표

* 실제 사용자 기준 문제 사전 발견

### 🧠 사용 Agent

**test-agent**

```text
Use test-agent.
현재 MVP 화면 기준으로
핵심 사용자 시나리오 테스트와 접근성 문제를 찾아줘.
```

### 📦 산출물

* 테스트 시나리오
* P0 / P1 수정 목록

---

## STEP 4. 제품 관점 최종 검증

### 🎯 목표

* "이 앱을 왜 써야 하는지"가 명확한지 점검

### 🧠 사용 Agent

**product-designer-critic**

```text
Use product-designer-critic.
이 MVP가 사용자에게 명확한 가치를 주는지
치명적인 문제 3가지를 지적해줘.
```

### 📦 산출물

* 출시 전 마지막 UX/제품 수정 포인트

---

## STEP 5. 코드 정리 (배포 전 필수)

### 🎯 목표

* 배포 실패 및 유지보수 리스크 제거

### 🧠 사용 Agent

**refactor-agent**

```text
Use refactor-agent.
배포 전에 최소한으로 필요한 리팩토링만 적용해줘.
기능 변경 없이 구조 정리 중심으로.
```

### 📦 산출물

* 정리된 코드 구조
* 잠재 리스크 제거

---

## STEP 6. 버그 탐지 & 배포 환경 점검

### 🎯 목표

* 배포 환경에서 터질 문제 사전 차단

### 🧠 사용 Agent

**bug-detective**

```text
Use bug-detective.
Streamlit Community Cloud 배포 기준으로
문제 될 수 있는 환경/의존성/설정 리스크를 점검해줘.
```

### 📦 산출물

* requirements / env / secrets 체크리스트

---

## STEP 7. 문서화 (배포 버튼 누르기 전)

### 🎯 목표

* 미래의 나와 협업자를 위한 최소 문서 확보

### 🧠 사용 Agent

**doc-writer**

```text
Use doc-writer.
현재 MVP 기준 README.md와 배포 가이드를 작성해줘.
```

### 📦 산출물

* README.md
* 실행/배포 가이드

---

## STEP 8. 🚢 배포

### 🎯 목표

* 실제 사용자에게 서비스 공개

### 실행

* GitHub push
* Streamlit Community Cloud / Vercel / Render 배포
* 배포 URL 확인

### ⚠️ 배포 실패 시 즉시 호출

```text
Use bug-detective.
이 배포 에러 로그를 보고 원인과 최소 수정안을 줘.
```

---

## 📌 한 장 요약 (Always-On 루틴)

```text
기획  → product-designer-critic
UI    → donguibogam-smithery-ui-designer
구현  → frontend-tailwind-engineer
테스트→ test-agent
검증  → product-designer-critic
정리  → refactor-agent
버그  → bug-detective
문서  → doc-writer
배포  → 🚀
```

---

## ✅ 사용 팁

* 막히면 **생각하지 말고 해당 Agent 호출**
* 한 번에 여러 Agent 쓰지 말고 **단계별로 하나씩**
* 이 문서는 프로젝트 루트에 두고 항상 참고

> 파일 추천 위치: `docs/MVP_to_Deploy_Agent_Routine.md`

---

### ✨ 이 루틴의 목표

**혼자 개발해도, 팀이 있는 것처럼 안정적으로 배포하기**
