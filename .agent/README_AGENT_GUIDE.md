## 🤖 Agent 기반 개발 방식 (Health Stack)

이 프로젝트는 Cursor / Claude / Antigravity 등 **특정 툴에 종속되지 않는 범용 Agent 구조**를 사용합니다.

### 개발 원칙
- 기능 구현 전: `product-philosophy-guard`
- 핵심 로직: `interaction-analysis`, `intake-schedule-optimizer`
- UI/알림: `notification-tone`, `frontend-ux`
- 배포 전 필수: `qa-risk-audit`

### 권장 개발 흐름
```
아이디어/기획
 → Guard 점검
 → 분석/로직 Agent
 → UI/API Agent
 → QA Agent
 → 배포
```

각 Agent는 **프롬프트 + 입력 템플릿**만 있으면 어디서든 호출 가능합니다.