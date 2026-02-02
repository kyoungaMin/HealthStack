## Agent-driven workflow (Cursor / Claude / Antigravity 공용)

이 프로젝트는 `agents/` 폴더의 역할 분리 프롬프트를 사용해 **기획 → 구현 → 리스크 검수**를 반복합니다.
Health Stack의 핵심 원칙(치료/처방/추천 금지, 정보 이해·판단 보조·생활 관리·알림 중심)을 유지하기 위해,
변경이 생길 때마다 아래 파이프라인을 최소 1회 통과시키는 것을 권장합니다.

### 폴더 구조
- `agents/00_AGENT_MAP.md` : 전체 에이전트 흐름
- `agents/USAGE.md` : 에이전트별 호출 템플릿(복붙용)
- `agents/PIPELINE_EXAMPLE.md` : 1인 유저 기준 파이프라인 예시
- 나머지 `agents/*.md` : 각 에이전트의 시스템 프롬프트/체크리스트

### 권장 파이프라인 (MVP)
1) `product-philosophy-guard` : 문구/UX가 의료행위처럼 보이지 않게 선제 차단  
2) `medical-info-summary` + `donguibogam-lifestyle` : 정보 레이어 생성(현대의학/생활가이드)  
3) `interaction-analysis` : 조합 위험도(🟢🟡🔴)  
4) `intake-schedule-optimizer` : 시간표 JSON + 충돌 리스트  
5) `notification-tone` : 알림 문장 톤 정리  
6) `frontend-ux` → `backend-api-architect` : 화면 설계 ↔ API 스키마 확정  
7) `pdf-report-generator` : 리포트 템플릿(근거/고지 포함)  
8) `qa-risk-audit` : PASS/FAIL 릴리즈 게이트  
9) `docs-policy-writer` : 약관/개인정보/면책 문구(릴리즈 전 필수)

### 사용 방법 (도구 무관 공통)
- Cursor/Claude/Antigravity 어디서든 동일하게:
  - 에이전트 파일을 열고 **“시스템 프롬프트” 섹션**을 해당 도구의 지시문(Instruction/System Prompt)에 붙여넣습니다.
  - 이후 입력은 `agents/USAGE.md`의 템플릿을 사용합니다.
- 기능/문구를 수정하면:
  - 최소 `product-philosophy-guard` → `qa-risk-audit`는 항상 실행합니다.

### PR/커밋 체크리스트
- [ ] 문구/버튼/알림 변경 시 `product-philosophy-guard` 통과
- [ ] 🔴 결과 화면에 “의료진 상담 권장” 포함(공포 조장 없이)
- [ ] 근거 수준(🟢🟡🔴) 표기 누락 없음
- [ ] 릴리즈 전 `qa-risk-audit` PASS
