
---

## 3) `docs/erd/erd-full.md`

```md
# ERD — Full (전체)

> 범위: Health Stack + Content/RAG/Billing 전체를 한 장으로 통합한 ERD  
> 용도: 전체 구조 이해(온보딩/아키텍처 리뷰). 세부 컬럼은 `schema.dbml`을 기준으로 함.

```mermaid
erDiagram
  AUTH_USERS { uuid id PK }

  %% USER
  USER_PROFILES { uuid user_id PK }
  USER_PREFERENCES { bigint id PK }

  %% MASTERS
  FOODS_MASTER { text rep_code PK }
  DISEASE_MASTER { bigint id PK }

  %% HEALTH STACK
  CATALOG_DRUGS { bigint id PK }
  CATALOG_SUPPLEMENTS { bigint id PK }
  USER_INTAKE_ITEMS { bigint id PK }
  INTAKE_SCHEDULES { bigint id PK }
  INTAKE_LOGS { bigint id PK }
  USER_PUSH_TOKENS { bigint id PK }
  REPORTS { bigint id PK }

  %% CONTENT / CURATION
  SYMPTOM_INGREDIENT_MAP { bigint id PK }
  RECIPES { bigint id PK }
  SYMPTOM_RECIPE_MAP { bigint id PK }
  CONTENT_VIDEOS { bigint id PK }
  SYMPTOM_VIDEO_MAP { bigint id PK }
  INGREDIENT_PRODUCT_LINKS { bigint id PK }

  %% INTERACTION / RAG
  INTERACTION_FACTS { bigint id PK }
  PUBMED_PAPERS { text pmid PK }
  PUBMED_EMBEDDINGS { text pmid FK }

  %% BILLING
  PLANS { bigint id PK }
  SUBSCRIPTIONS { bigint id PK }
  PAYMENTS { bigint id PK }

  %% RELATIONSHIPS (핵심만)
  AUTH_USERS ||--|| USER_PROFILES : "1:1"
  AUTH_USERS ||--o{ USER_PREFERENCES : "1:N"

  AUTH_USERS ||--o{ USER_INTAKE_ITEMS : "1:N"
  USER_INTAKE_ITEMS ||--o{ INTAKE_SCHEDULES : "1:N"
  INTAKE_SCHEDULES ||--o{ INTAKE_LOGS : "1:N"
  AUTH_USERS ||--o{ USER_PUSH_TOKENS : "1:N"
  AUTH_USERS ||--o{ REPORTS : "1:N"

  CATALOG_DRUGS ||--o{ USER_INTAKE_ITEMS : "0..N"
  CATALOG_SUPPLEMENTS ||--o{ USER_INTAKE_ITEMS : "0..N"
  FOODS_MASTER ||--o{ USER_INTAKE_ITEMS : "0..N"
  DISEASE_MASTER ||--o{ SYMPTOM_INGREDIENT_MAP : "1:N"
  FOODS_MASTER ||--o{ SYMPTOM_INGREDIENT_MAP : "1:N"
  DISEASE_MASTER ||--o{ SYMPTOM_RECIPE_MAP : "1:N"
  RECIPES ||--o{ SYMPTOM_RECIPE_MAP : "1:N"
  DISEASE_MASTER ||--o{ SYMPTOM_VIDEO_MAP : "1:N"
  CONTENT_VIDEOS ||--o{ SYMPTOM_VIDEO_MAP : "1:N"
  FOODS_MASTER ||--o{ INGREDIENT_PRODUCT_LINKS : "1:N"

  PUBMED_PAPERS ||--o{ PUBMED_EMBEDDINGS : "1:N"
  PLANS ||--o{ SUBSCRIPTIONS : "1:N"
