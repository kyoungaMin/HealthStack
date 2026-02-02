# Health Stack Agents 사용 가이드 (USAGE)

이 문서는 각 Agent를 **언제, 어떻게 호출해야 하는지** 바로 쓸 수 있는 입력 템플릿을 제공합니다.
복붙해서 바로 사용하세요.

---

## 1️⃣ product-philosophy-guard

### 언제 사용?
- 새 기능/화면/버튼/알림 문구를 만들었을 때 **항상 먼저**

### 입력 템플릿
```
다음 기능/문구가 의료행위(치료/처방/추천)처럼 보이는지 점검해줘.

[기능 설명]
- 기능 목적:
- 사용자 행동:
- 결과 화면:

[화면 문구]
- 제목:
- 설명:
- 버튼/알림 문구:
```

### 기대 출력
- 위험도 (LOW/MEDIUM/HIGH)
- 문제 문장 + 이유
- 안전한 대체 문장
- 면책/상담 권장 위치

---

## 2️⃣ interaction-analysis

### 언제 사용?
- “같이 먹어도 돼?” 핵심 기능 구현 시

### 입력 템플릿
```json
{
  "intake_items": [
    {"type": "drug", "name": "혈압약"},
    {"type": "supplement", "name": "마그네슘"},
    {"type": "food", "name": "자몽"}
  ],
  "user_conditions": ["고혈압"]
}
```

### 기대 출력
- 🟢🟡🔴 조합별 위험도
- 이유 / 관찰 포인트 / 근거 수준

---

## 3️⃣ intake-schedule-optimizer

### 언제 사용?
- 복용 시간표 자동 생성, 알림 구현 시

### 입력 템플릿
```json
{
  "items": [
    {"name": "혈압약", "timing_pref": "after_meal"},
    {"name": "마그네슘", "timing_pref": "bedtime", "interval_rules": [{"with": "철분", "hours": 2}]}
  ],
  "day_profile": {
    "wake": "07:00",
    "breakfast": "08:00",
    "lunch": "12:30",
    "dinner": "18:30",
    "sleep": "23:00"
  }
}
```

### 기대 출력
- 하루 타임라인(JSON)
- 충돌 항목 + 완화 안내

---

## 4️⃣ notification-tone

### 언제 사용?
- 푸시/앱 알림 문구 작성 시

### 입력 템플릿
```
알림 상황:
- 항목:
- 시간대:
- 이유:
- 위험도(있다면):
- 톤: 친근/중립/차분
```

### 기대 출력
- 알림 문구 3안
- 🔴 위험용 완곡 문장 2안