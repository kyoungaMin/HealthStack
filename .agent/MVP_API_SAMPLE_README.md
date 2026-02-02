# MVP API 샘플 응답 사용법

`agents/MVP_API_SAMPLE_RESPONSES.json` 는 MVP 개발 시 프론트/백엔드가 **같은 형태의 응답 계약(contract)** 을 공유하기 위한 예시입니다.

## 사용 방법
- 프론트: 화면 목업/상태관리/컴포넌트 설계에 그대로 사용
- 백엔드: Pydantic 스키마/응답 모델을 만들 때 기준으로 사용
- QA: 🔴(상담 권장) / 근거 수준(🟢🟡🔴) / disclaimer 누락 여부 점검 기준으로 사용

## 주의
- 의료 문구는 단정 금지
- UI/리포트에는 disclaimer를 노출
- 실제 출처(source_keys)는 DB의 interaction_facts와 연결
