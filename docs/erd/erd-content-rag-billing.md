
---

## 2) `docs/erd/erd-content-rag-billing.md`

```md
# ERD — Content · RAG · Billing (콘텐츠/식단 · 근거검색 · 결제)

> 범위: 증상 기반 큐레이션(식재료/레시피/영상) + 커머스 링크 + 상호작용 지식베이스 + PubMed RAG + 결제/구독  
> 원칙: 공용 데이터는 읽기 허용, 쓰기는 서버(service_role)에서 관리 권장

```mermaid
erDiagram
  DISEASE_MASTER {
    bigint id PK
    text disease
    text modern_disease
  }

  FOODS_MASTER {
    text rep_code PK
    text rep_name
  }

  SYMPTOM_INGREDIENT_MAP {
    bigint id PK
    bigint symptom_id FK
    text rep_code FK
    text direction
    text rationale_ko
    int priority
    timestamptz created_at
  }

  RECIPES {
    bigint id PK
    text title
    text description
    jsonb ingredients
    jsonb steps
    text[] tags
    timestamptz created_at
    timestamptz updated_at
  }

  SYMPTOM_RECIPE_MAP {
    bigint id PK
    bigint symptom_id FK
    bigint recipe_id FK
    text meal_slot
    int priority
  }

  CONTENT_VIDEOS {
    bigint id PK
    text provider
    text video_id
    text title
    text channel
    text[] tags
    timestamptz created_at
  }

  SYMPTOM_VIDEO_MAP {
    bigint id PK
    bigint symptom_id FK
    bigint video_pk FK
    int priority
  }

  INGREDIENT_PRODUCT_LINKS {
    bigint id PK
    text rep_code FK
    text provider
    text query_template
    text disclaimer_ko
    timestamptz created_at
  }

  INTERACTION_FACTS {
    bigint id PK
    text a_type
    text a_ref
    text b_type
    text b_ref
    text severity
    text evidence_level
    text mechanism
    text summary_ko
    text action_ko
    jsonb sources
    text[] pmids
    timestamptz updated_at
  }

  PUBMED_PAPERS {
    text pmid PK
    text title
    text abstract
    text journal
    int pub_year
    text[] publication_types
    text[] mesh_terms
    text url
    timestamptz created_at
    timestamptz updated_at
  }

  PUBMED_EMBEDDINGS {
    text pmid FK
    int chunk_index PK
    text content
    vector embedding
    timestamptz created_at
  }

  PLANS {
    bigint id PK
    text code
    text name
    int price
    text currency
    jsonb features
    boolean is_active
  }

  SUBSCRIPTIONS {
    bigint id PK
    uuid user_id
    text plan_code FK
    text status
    timestamptz current_period_start
    timestamptz current_period_end
    text provider
    text provider_sub_id
    timestamptz created_at
    timestamptz updated_at
  }

  PAYMENTS {
    bigint id PK
    uuid user_id
    int amount
    text currency
    text provider
    text provider_payment_id
    text payment_type
    bigint reference_id
    text status
    timestamptz created_at
  }

  DISEASE_MASTER ||--o{ SYMPTOM_INGREDIENT_MAP : "1:N"
  FOODS_MASTER ||--o{ SYMPTOM_INGREDIENT_MAP : "1:N"
  DISEASE_MASTER ||--o{ SYMPTOM_RECIPE_MAP : "1:N"
  RECIPES ||--o{ SYMPTOM_RECIPE_MAP : "1:N"
  DISEASE_MASTER ||--o{ SYMPTOM_VIDEO_MAP : "1:N"
  CONTENT_VIDEOS ||--o{ SYMPTOM_VIDEO_MAP : "1:N"
  FOODS_MASTER ||--o{ INGREDIENT_PRODUCT_LINKS : "1:N"

  PUBMED_PAPERS ||--o{ PUBMED_EMBEDDINGS : "1:N"
  PLANS ||--o{ SUBSCRIPTIONS : "1:N (by code)"
