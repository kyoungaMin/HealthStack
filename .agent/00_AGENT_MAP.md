# Health Stack Agent Map (오늘 기획서 기준)

이 폴더의 에이전트들은 **Health Stack** 서비스 기획서의 원칙(치료/처방 금지, 정보 이해·판단 보조·생활 관리·알림 중심)을 그대로 따릅니다.  
각 에이전트는 **하나의 책임(Single Responsibility)** 만 갖도록 분리되어 있습니다.

## 전체 흐름

1. **product-philosophy-guard**: 서비스 철학/문구/기능이 의료행위처럼 보이지 않게 수문장 역할
2. **medical-info-summary**: 처방약 정보를 쉬운 언어로 요약 + 근거 수준 표시
3. **interaction-analysis**: 약×약/약×건기식/약×음식(주의 수준) 상호작용 위험도 산정
4. **donguibogam-lifestyle**: 동의보감 레이어를 '생활 선택 가이드'로 번역(치료/대체 금지)
5. **meal-plan**: 증상 기반 식단 방향성/구성(약 고려 문구 포함)
6. **intake-schedule-optimizer**: 공복/식후/취침/간격 조건 기반 시간표 자동 생성
7. **notification-tone**: 알림 문장 톤 가이드(명령/불안 유발 금지)
8. **frontend-ux**: 정보 밀도/가독성/위험도 UI 표현 설계
9. **backend-api-architect**: FastAPI + (DB/RLS 전제) API 설계
10. **pdf-report-generator**: 개인화 PDF 리포트 생성(근거 출처/스냅샷)
11. **qa-risk-audit**: 문구·흐름·데이터/근거/면책 누락 검사
12. **docs-policy-writer**: 약관/개인정보/의료면책/고정 고지 문구 작성

## 파일 규칙

- 각 에이전트 문서에는 다음 섹션이 포함됩니다.
  - 목적 / 금지사항 / 입력 / 출력 / 작업 절차
  - 시스템 프롬프트(바로 복붙용)
  - 체크리스트
  - 예시 요청/응답(짧게)

## 운영 팁

- 제품/문구 변경 시: `product-philosophy-guard` → `qa-risk-audit` 순서로 우선 검증
- 데이터 소스 변경 시: `medical-info-summary`, `interaction-analysis`, `pdf-report-generator`에 근거/출처 필드 반드시 반영
