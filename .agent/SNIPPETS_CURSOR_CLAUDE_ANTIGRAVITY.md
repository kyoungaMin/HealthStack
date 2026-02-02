# 범용 스니펫/매크로 (Cursor / Claude / Antigravity 공용)

아래 스니펫은 “어떤 도구에서도” 복붙으로 동작하도록 작성했습니다.
- **[SYSTEM]** 블록은 도구의 System/Instruction 영역에
- **[USER]** 블록은 대화 입력창에 붙여넣어 사용하세요.

---

## Snippet A — Guard Gate (문구/기능 리스크 점검)

### [SYSTEM] (product-philosophy-guard)
(agents/01_product-philosophy-guard.md 의 “시스템 프롬프트”를 붙여넣기)

### [USER] 템플릿
다음 기능/문구가 의료행위(치료/처방/추천)처럼 보이는지 점검해줘.

[기능 설명]
- 기능 목적:
- 사용자 행동:
- 결과 화면:

[화면 문구]
- 제목:
- 설명:
- 버튼/알림 문구:

---

## Snippet B — Interaction Check (조합 분석)

### [SYSTEM] (interaction-analysis)
(agents/03_interaction-analysis.md 의 “시스템 프롬프트”를 붙여넣기)

### [USER] JSON 템플릿
```json
{
  "intake_items": [
    {"type": "drug", "name": "약 이름/성분"},
    {"type": "supplement", "name": "건기식/성분"},
    {"type": "food", "name": "음식/재료"}
  ],
  "user_conditions": ["선택: 임신/고령/간질환/신장질환/질환키워드"]
}
```

---

## Snippet C — Schedule Builder (시간표 생성)

### [SYSTEM] (intake-schedule-optimizer)
(agents/06_intake-schedule-optimizer.md 의 “시스템 프롬프트”를 붙여넣기)

### [USER] JSON 템플릿
```json
{
  "items": [
    {
      "name": "항목명",
      "type": "drug|supplement",
      "timing_pref": "fasting|after_meal|bedtime|any",
      "interval_rules": [{"with": "상대 항목명", "hours": 2}]
    }
  ],
  "day_profile": {
    "wake": "07:00",
    "breakfast": "08:00",
    "lunch": "12:30",
    "dinner": "18:30",
    "sleep": "23:00"
  },
  "constraints": {"max_notifications_per_day": 6}
}
```

---

## Snippet D — Notification Copy (알림 문장)

### [SYSTEM] (notification-tone)
(agents/07_notification-tone.md 의 “시스템 프롬프트”를 붙여넣기)

### [USER] 템플릿
알림 상황:
- 항목:
- 시간대:
- 이유:
- 위험도(있다면 🟢🟡🔴):
- 톤: 친근/중립/차분

---

## Snippet E — Release Gate (릴리즈 전 QA)

### [SYSTEM] (qa-risk-audit)
(agents/11_qa-risk-audit.md 의 “시스템 프롬프트”를 붙여넣기)

### [USER] 템플릿
다음 릴리즈 후보의 화면/알림/리포트 문구를 의료·법적 리스크 관점에서 PASS/FAIL로 점검해줘.
특히 (치료/처방처럼 보이는 표현), (근거 표기 누락), (🔴 상담 권장 누락)을 최우선으로 봐줘.

[화면/플로우]
- ...

[문구 전체]
- ...
