# ERD — Health Stack (복용 스택 · 스케줄 · 알림 · 리포트)

> **범위**: 사용자 복용 스택(약/건기식/음식) + 복용 시간표 + 복용 로그 + 푸시 토큰 + 리포트  
> **원칙**: 개인 데이터는 `user_id = auth.uid()` 기반 RLS로 보호  
> **소스**: [`schema.integrated.dbml`](./schema.integrated.dbml)  
> **최종 업데이트**: 2026-02-04

---

## 📊 ERD 이미지

![Core Tables ERD](./erd-core-tables.png)

---

## 🗂️ ERD 다이어그램 (Mermaid)

```mermaid
erDiagram
  AUTH_USERS {
    uuid id PK
  }

  USER_PROFILES {
    uuid user_id PK_FK
    text display_name
    text locale
    text timezone
    time wake_time
    time breakfast_time
    time lunch_time
    time dinner_time
    time bed_time
    timestamptz created_at
    timestamptz updated_at
  }

  USER_PREFERENCES {
    bigint id PK
    uuid user_id FK
    text_array preferred_categories
    text_array excluded_ingredients
    jsonb health_conditions
    boolean notification_enabled
    timestamptz created_at
    timestamptz updated_at
  }

  CATALOG_DRUGS {
    bigint id PK
    text name
    text generic_name
    text atc_code
    text source
    timestamptz updated_at
  }

  CATALOG_SUPPLEMENTS {
    bigint id PK
    text name
    text ingredient
    text category
    timestamptz updated_at
  }

  FOODS_MASTER {
    text rep_code PK
    text rep_name
    timestamptz created_at
  }

  USER_INTAKE_ITEMS {
    bigint id PK
    uuid user_id FK
    text item_type "drug | supplement | food"
    bigint catalog_drug_id FK
    bigint catalog_supplement_id FK
    text rep_code FK
    text display_name
    text dose_text
    text route
    boolean active
    timestamptz created_at
    timestamptz updated_at
  }

  INTAKE_SCHEDULES {
    bigint id PK
    uuid user_id FK
    bigint intake_item_id FK
    text pattern "daily | weekdays | weekend | custom"
    int_array days_of_week
    text time_anchor "wake | breakfast | lunch | dinner | bed | custom"
    time custom_time
    int offset_minutes
    jsonb rules
    boolean is_enabled
    timestamptz created_at
    timestamptz updated_at
  }

  INTAKE_LOGS {
    bigint id PK
    uuid user_id FK
    bigint schedule_id FK
    timestamptz scheduled_at
    timestamptz taken_at
    text status "taken | skipped | missed"
    text note
    timestamptz created_at
  }

  USER_PUSH_TOKENS {
    bigint id PK
    uuid user_id FK
    text platform "ios | android | web"
    text token
    boolean enabled
    timestamptz last_seen_at
    timestamptz created_at
  }

  REPORTS {
    bigint id PK
    uuid user_id FK
    text report_type "interaction | mealplan | intake_summary"
    text title
    jsonb inputs
    text content_md
    text pdf_path
    text status "pending | generating | done | failed"
    timestamptz created_at
    timestamptz updated_at
  }

  %% 관계 정의
  AUTH_USERS ||--|| USER_PROFILES : "1:1"
  AUTH_USERS ||--o{ USER_PREFERENCES : "1:N"
  AUTH_USERS ||--o{ USER_INTAKE_ITEMS : "1:N"
  USER_INTAKE_ITEMS ||--o{ INTAKE_SCHEDULES : "1:N"
  INTAKE_SCHEDULES ||--o{ INTAKE_LOGS : "1:N"
  AUTH_USERS ||--o{ USER_PUSH_TOKENS : "1:N"
  AUTH_USERS ||--o{ REPORTS : "1:N"

  CATALOG_DRUGS ||--o{ USER_INTAKE_ITEMS : "0:N (drug)"
  CATALOG_SUPPLEMENTS ||--o{ USER_INTAKE_ITEMS : "0:N (supplement)"
  FOODS_MASTER ||--o{ USER_INTAKE_ITEMS : "0:N (food/tea)"
```

---

## 📋 테이블 상세

### 1️⃣ 인증 & 프로필

| 테이블 | PK | 설명 |
|--------|-----|------|
| `auth_users` | uuid id | Supabase Auth 사용자 (참조용) |
| `user_profiles` | uuid user_id | 사용자 프로필, 시간대, 식사시간 설정 |
| `user_preferences` | bigint id | 선호 카테고리, 제외 재료, 건강상태 |
| `user_push_tokens` | bigint id | 푸시 알림 토큰 (iOS/Android/Web) |

---

### 2️⃣ 카탈로그 (마스터)

| 테이블 | PK | 설명 |
|--------|-----|------|
| `catalog_drugs` | bigint id | 의약품 카탈로그 (ATC 코드 포함) |
| `catalog_supplements` | bigint id | 건강기능식품 카탈로그 |
| `foods_master` | text rep_code | 식재료 대표코드 마스터 |

---

### 3️⃣ 복용 관리

| 테이블 | PK | 설명 |
|--------|-----|------|
| `user_intake_items` | bigint id | 사용자 복용 항목 (약/영양제/식품) |
| `intake_schedules` | bigint id | 복용 스케줄 (패턴, 요일, 시간) |
| `intake_logs` | bigint id | 복용 기록 (taken/skipped/missed) |

---

### 4️⃣ 리포트

| 테이블 | PK | 설명 |
|--------|-----|------|
| `reports` | bigint id | 리포트 생성 이력 (상호작용/식단/요약) |

---

## 🔗 핵심 관계

```
auth_users (1)
    │
    ├──── (1:1) ──── user_profiles
    │
    ├──── (1:N) ──── user_preferences
    │
    ├──── (1:N) ──── user_push_tokens
    │
    ├──── (1:N) ──── reports
    │
    └──── (1:N) ──── user_intake_items
                          │
                          ├── (0:N) ←── catalog_drugs
                          ├── (0:N) ←── catalog_supplements
                          ├── (0:N) ←── foods_master
                          │
                          └──── (1:N) ──── intake_schedules
                                                │
                                                └──── (1:N) ──── intake_logs
```

---

## 📝 주요 Enum 값

### `user_intake_items.item_type`
- `drug` - 의약품
- `supplement` - 건강기능식품
- `food` - 식품/차

### `intake_schedules.pattern`
- `daily` - 매일
- `weekdays` - 평일
- `weekend` - 주말
- `custom` - 사용자 정의

### `intake_schedules.time_anchor`
- `wake` - 기상 시
- `breakfast` - 아침 식후
- `lunch` - 점심 식후
- `dinner` - 저녁 식후
- `bed` - 취침 전
- `custom` - 사용자 정의

### `intake_logs.status`
- `taken` - 복용 완료
- `skipped` - 의도적 건너뜀
- `missed` - 미복용

### `reports.status`
- `pending` - 대기 중
- `generating` - 생성 중
- `done` - 완료
- `failed` - 실패
