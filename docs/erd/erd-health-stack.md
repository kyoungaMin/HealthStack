# ERD — Health Stack (복용 스택 · 스케줄 · 알림 · 리포트)

> 범위: 사용자 복용 스택(약/건기식/음식) + 복용 시간표 + 복용 로그 + 푸시 토큰 + 리포트  
> 원칙: 개인 데이터는 `user_id = auth.uid()` 기반 RLS로 보호

```mermaid
erDiagram
  AUTH_USERS {
    uuid id PK
  }

  USER_PROFILES {
    uuid user_id PK
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
    text[] preferred_categories
    text[] excluded_ingredients
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
  }

  USER_INTAKE_ITEMS {
    bigint id PK
    uuid user_id FK
    text item_type
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
    text pattern
    int[] days_of_week
    text time_anchor
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
    text status
    text note
    timestamptz created_at
  }

  USER_PUSH_TOKENS {
    bigint id PK
    uuid user_id FK
    text platform
    text token
    boolean enabled
    timestamptz last_seen_at
    timestamptz created_at
  }

  REPORTS {
    bigint id PK
    uuid user_id FK
    text report_type
    text title
    jsonb inputs
    text content_md
    text pdf_path
    text status
    timestamptz created_at
    timestamptz updated_at
  }

  AUTH_USERS ||--|| USER_PROFILES : "1:1"
  AUTH_USERS ||--o{ USER_PREFERENCES : "1:N"
  AUTH_USERS ||--o{ USER_INTAKE_ITEMS : "1:N"
  USER_INTAKE_ITEMS ||--o{ INTAKE_SCHEDULES : "1:N"
  INTAKE_SCHEDULES ||--o{ INTAKE_LOGS : "1:N"
  AUTH_USERS ||--o{ USER_PUSH_TOKENS : "1:N"
  AUTH_USERS ||--o{ REPORTS : "1:N"

  CATALOG_DRUGS ||--o{ USER_INTAKE_ITEMS : "0..N (drug)"
  CATALOG_SUPPLEMENTS ||--o{ USER_INTAKE_ITEMS : "0..N (supplement)"
  FOODS_MASTER ||--o{ USER_INTAKE_ITEMS : "0..N (food/tea)"
