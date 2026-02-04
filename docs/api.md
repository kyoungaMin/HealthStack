# 🔌 API Design (FastAPI / Node)

이 문서는 Health Stack 서비스의 API 설계를 정의합니다.

> **소스**: [`schema.integrated.dbml`](./erd/schema.integrated.dbml)  
> **최종 업데이트**: 2026-02-04

---

## 0. 공통 규칙

### Base URL
```
/api/v1
```

### 인증
- 클라이언트: Supabase 세션 토큰 (`Authorization: Bearer <token>`)
- 서버: Supabase `service_role`로 운영 (웹훅/배치/RAG)

### 응답 규칙
```json
// 성공
{ "data": { ... }, "meta": { "total": 100, "page": 1 } }

// 오류
{ "error": { "code": "INVALID_INPUT", "message": "...", "details": [...] } }
```

### HTTP Status Codes
| Code | 설명 |
|------|------|
| 200 | 성공 |
| 201 | 생성됨 |
| 400 | 잘못된 요청 |
| 401 | 인증 필요 |
| 403 | 권한 없음 |
| 404 | 리소스 없음 |
| 429 | Rate Limit 초과 |
| 500 | 서버 오류 |

---

## 1. Auth / Profile

### 1.1 내 프로필 조회
```http
GET /me
```
**DB**: `user_profiles`, `user_preferences`

**Response**:
```json
{
  "data": {
    "user_id": "uuid",
    "display_name": "홍길동",
    "locale": "ko-KR",
    "timezone": "Asia/Seoul",
    "wake_time": "07:00",
    "breakfast_time": "08:00",
    "lunch_time": "12:30",
    "dinner_time": "19:00",
    "bed_time": "23:00",
    "preferences": {
      "preferred_categories": ["soup", "tea"],
      "excluded_ingredients": ["spicy"],
      "health_conditions": { "diabetes": false },
      "notification_enabled": true
    }
  }
}
```

---

### 1.2 프로필 설정 저장
```http
PATCH /me
```

**Body**:
```json
{
  "display_name": "홍길동",
  "wake_time": "07:00",
  "breakfast_time": "08:00",
  "lunch_time": "12:30",
  "dinner_time": "19:00",
  "bed_time": "23:00",
  "notification_enabled": true,
  "preferred_categories": ["soup"],
  "excluded_ingredients": ["spicy"]
}
```

---

### 1.3 푸시 토큰 등록
```http
POST /me/push-tokens
```

**Body**:
```json
{
  "platform": "ios",
  "token": "fcm_token_here"
}
```

**DB**: `user_push_tokens`

---

## 2. Intake Stack (복용 스택)

### 2.1 복용 항목 목록
```http
GET /intake-items
GET /intake-items?active=true
```

**DB**: `user_intake_items`

**Response**:
```json
{
  "data": [
    {
      "id": 101,
      "item_type": "drug",
      "display_name": "아스피린",
      "catalog_drug_id": 123,
      "dose_text": "100mg",
      "route": "oral",
      "active": true
    }
  ]
}
```

---

### 2.2 복용 항목 생성
```http
POST /intake-items
```

**Body**:
```json
{
  "item_type": "supplement",
  "display_name": "마그네슘",
  "catalog_supplement_id": 12,
  "dose_text": "1정",
  "route": "oral"
}
```

**item_type**: `drug` | `supplement` | `food`

---

### 2.3 복용 항목 수정
```http
PATCH /intake-items/{id}
```

**Body**:
```json
{
  "dose_text": "2정",
  "active": false
}
```

---

### 2.4 복용 항목 삭제
```http
DELETE /intake-items/{id}
```

---

## 3. Schedules (시간표/알림)

### 3.1 스케줄 목록
```http
GET /schedules
GET /schedules?intake_item_id=101
```

**DB**: `intake_schedules`

---

### 3.2 스케줄 생성
```http
POST /schedules
```

**Body**:
```json
{
  "intake_item_id": 101,
  "pattern": "daily",
  "days_of_week": [1, 2, 3, 4, 5],
  "time_anchor": "breakfast",
  "offset_minutes": 15,
  "rules": { "separate_by_minutes": 120 }
}
```

**Enum 값**:
- `pattern`: `daily` | `weekdays` | `weekend` | `custom`
- `time_anchor`: `wake` | `breakfast` | `lunch` | `dinner` | `bed` | `custom`

---

### 3.3 스케줄 수정
```http
PATCH /schedules/{id}
```

---

### 3.4 스케줄 삭제
```http
DELETE /schedules/{id}
```

---

### 3.5 오늘 일정 생성
```http
POST /schedule-generate/today
```

**동작**: 생활시간 + 스케줄 규칙으로 오늘 복용 타임라인 계산, `intake_logs`에 scheduled row 생성

---

### 3.6 오늘 복용 타임라인 조회
```http
GET /intake/today?date=2026-02-04
```

**DB**: `intake_schedules`, `intake_logs`, `user_profiles`

**Response**:
```json
{
  "data": [
    {
      "log_id": 501,
      "intake_item_id": 101,
      "display_name": "마그네슘",
      "scheduled_at": "2026-02-04T08:15:00+09:00",
      "taken_at": null,
      "status": "pending"
    }
  ]
}
```

---

### 3.7 복용 체크
```http
POST /intake/logs/{id}/take
```

**DB**: `intake_logs` → `taken_at`, `status='taken'`

---

### 3.8 스킵/스누즈
```http
POST /intake/logs/{id}/skip
POST /intake/logs/{id}/snooze
```

**Body (snooze)**:
```json
{ "minutes": 30 }
```

---

## 4. Input Sessions (입력 세션)

> **신규**: 증상/처방전 입력 세션 관리

### 4.1 세션 생성
```http
POST /sessions
```

**Body**:
```json
{
  "input_type": "combined",
  "input_summary": "혈압약 복용 중, 어지러움 증상"
}
```

**input_type**: `symptom` | `prescription` | `combined`

**DB**: `user_input_sessions`

---

### 4.2 세션에 증상 추가
```http
POST /sessions/{session_id}/symptoms
```

**Body**:
```json
{
  "symptom_id": 42,
  "symptom_text": "속이 더부룩해요"
}
```

**DB**: `user_symptoms`

---

### 4.3 세션에 처방전 추가
```http
POST /sessions/{session_id}/prescriptions
```

**Body**:
```json
{
  "prescription_image_url": "https://storage.../rx.jpg",
  "prescribed_at": "2026-01-15"
}
```

**DB**: `user_prescriptions`

---

### 4.4 처방전 약물 추가
```http
POST /prescriptions/{prescription_id}/drugs
```

**Body**:
```json
{
  "drug_name": "아스피린",
  "dosage": "100mg",
  "frequency": "1일 1회",
  "duration": "30일"
}
```

**DB**: `user_prescription_drugs`

---

### 4.5 세션 추천 결과 조회
```http
GET /sessions/{session_id}/recommendations
```

**DB**: `session_recommendation_results`

**Response**:
```json
{
  "data": [
    {
      "result_type": "ingredient",
      "ref_table": "foods_master",
      "ref_id": "100100",
      "reason": "소화에 도움되는 생강"
    },
    {
      "result_type": "restaurant",
      "ref_table": "restaurants",
      "ref_id": "501",
      "reason": "생강차 전문점"
    }
  ]
}
```

---

### 4.6 세션 기반 추천 생성
```http
POST /sessions/{session_id}/generate-recommendations
```

**동작**: 세션 내 증상/처방전 분석 → 추천 결과 생성

---

## 5. Interaction Check (조합 분석)

### 5.1 조합 체크
```http
POST /interactions/check
```

**Body**:
```json
{
  "items": [
    { "type": "drug", "ref": "123" },
    { "type": "supplement", "ref": "12" },
    { "type": "food", "ref": "100100" }
  ]
}
```

**DB**: `interaction_facts`

**Response**:
```json
{
  "data": {
    "interactions": [
      {
        "pair": ["drug:123", "supplement:12"],
        "severity": "moderate",
        "evidence_level": "high",
        "summary_ko": "흡수율이 감소할 수 있습니다",
        "action_ko": "2시간 간격을 두고 복용하세요",
        "pmids": ["12345678"]
      }
    ],
    "overall_risk": "moderate"
  }
}
```

**severity**: `none` | `mild` | `moderate` | `severe`

---

## 6. Symptom → Content (증상 콘텐츠)

### 6.1 증상 검색
```http
GET /symptoms?q=소화
```

**DB**: `disease_master`

---

### 6.2 증상 기반 번들 조회
```http
GET /symptoms/{symptom_id}/bundle
```

**Response**:
```json
{
  "data": {
    "symptom": { "id": 42, "disease": "소화불량" },
    "ingredients": {
      "helpful": [
        { "rep_code": "100100", "rep_name": "생강", "rationale_ko": "..." }
      ],
      "avoid": [
        { "rep_code": "200200", "rep_name": "고추", "rationale_ko": "..." }
      ]
    },
    "recipes": [
      { "id": 10, "title": "생강차", "meal_slot": "snack" }
    ],
    "videos": [
      { "id": 5, "title": "소화에 좋은 음식", "provider": "youtube", "video_id": "xxx" }
    ],
    "product_links": [
      { "rep_code": "100100", "provider": "naver_shopping", "query_template": "생강" }
    ]
  }
}
```

**DB**: `symptom_ingredient_map`, `symptom_recipe_map`, `symptom_video_map`, `ingredient_product_links`

---

### 6.3 오늘 식단 추천
```http
POST /mealplan/today
```

**Body**:
```json
{
  "symptom_ids": [42, 43],
  "constraints": { 
    "exclude_ingredients": ["spicy"],
    "meal_slots": ["breakfast", "lunch", "dinner"]
  }
}
```

---

## 7. Restaurant (음식점 추천)

> **신규**: 지역 음식점 추천 API

### 7.1 주변 음식점 검색
```http
GET /restaurants/search
```

**Query Parameters**:
| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `lat` | decimal | 위도 (필수) |
| `lng` | decimal | 경도 (필수) |
| `radius` | int | 반경 (미터, 기본 1000) |
| `rep_code` | string | 식재료 코드 |
| `symptom_id` | int | 증상 ID |
| `sort_by` | string | `distance` \| `rating` \| `relevance` |

**DB**: `restaurants`, `restaurant_search_requests`, `restaurant_search_results`

**Response**:
```json
{
  "data": [
    {
      "id": 501,
      "name": "생강나무",
      "category": "한식",
      "address": "서울시 강남구...",
      "distance_meters": 350,
      "rating_avg": 4.5,
      "review_count": 128,
      "matched_rep_codes": ["100100"],
      "matched_reason": "생강차 메뉴 제공"
    }
  ]
}
```

---

### 7.2 음식점 상세 조회
```http
GET /restaurants/{id}
```

**Response**:
```json
{
  "data": {
    "id": 501,
    "name": "생강나무",
    "category": "한식",
    "address_full": "서울시 강남구 역삼동 123-4",
    "phone": "02-1234-5678",
    "website_url": "https://...",
    "rating_avg": 4.5,
    "menus": [
      { "menu_name": "생강차", "price": 5000, "is_signature": true }
    ]
  }
}
```

---

### 7.3 음식점 즐겨찾기
```http
POST /restaurants/{id}/favorite
DELETE /restaurants/{id}/favorite
```

**DB**: `user_restaurant_favorites`

---

### 7.4 음식점 방문 로그
```http
POST /restaurants/{id}/visit-log
```

**Body**:
```json
{
  "action_type": "navigate",
  "search_request_id": 1001,
  "symptom_id": 42
}
```

**action_type**: `view` | `call` | `navigate` | `favorite` | `visit_confirm`

**DB**: `user_restaurant_visit_logs`

---

### 7.5 내 즐겨찾기 목록
```http
GET /me/restaurant-favorites
```

---

## 8. PubMed RAG Search (근거 검색)

### 8.1 RAG 검색
```http
POST /rag/pubmed
```

**Body**:
```json
{
  "query": "magnesium insomnia efficacy",
  "top_k": 5
}
```

**DB**: `pubmed_embeddings` (vector search), `pubmed_papers`

**Response**:
```json
{
  "data": {
    "results": [
      {
        "pmid": "12345678",
        "title": "Effect of Magnesium on Sleep",
        "abstract": "...",
        "relevance_score": 0.92,
        "journal": "Sleep Medicine",
        "pub_year": 2023
      }
    ]
  }
}
```

---

### 8.2 PubMed 수집 배치 (서버)
```http
POST /admin/pubmed/ingest
```

**Auth**: `service_role` only

---

## 9. Reports (PDF)

### 9.1 리포트 생성 요청
```http
POST /reports
```

**Body**:
```json
{
  "report_type": "interaction",
  "title": "내 복용 조합 안전성 리포트",
  "inputs": {
    "intake_item_ids": [101, 102, 103],
    "symptom_ids": [42]
  }
}
```

**report_type**: `interaction` | `mealplan` | `intake_summary`

**DB**: `reports` → `status='pending'`

---

### 9.2 리포트 목록/조회
```http
GET /reports
GET /reports/{id}
```

**Response**:
```json
{
  "data": {
    "id": 201,
    "report_type": "interaction",
    "title": "내 복용 조합 안전성 리포트",
    "status": "done",
    "pdf_path": "https://storage.../report_201.pdf",
    "created_at": "2026-02-04T10:00:00Z"
  }
}
```

**status**: `pending` | `generating` | `done` | `failed`

---

## 10. Billing (구독/결제)

### 10.1 플랜 조회
```http
GET /plans
```

**DB**: `plans`

**Response**:
```json
{
  "data": [
    {
      "id": 1,
      "code": "free",
      "name": "Free",
      "price": 0,
      "features": { "intake_items_limit": 5 }
    },
    {
      "id": 2,
      "code": "premium",
      "name": "Premium",
      "price": 9900,
      "features": { "intake_items_limit": -1, "pdf_discount": 50 }
    }
  ]
}
```

---

### 10.2 내 구독 상태
```http
GET /me/subscription
```

**DB**: `subscriptions`

---

### 10.3 구독 생성
```http
POST /billing/subscribe
```

**Body**:
```json
{
  "plan_code": "premium",
  "provider": "stripe"
}
```

**Response**:
```json
{
  "data": {
    "checkout_url": "https://checkout.stripe.com/..."
  }
}
```

---

### 10.4 결제 웹훅 (서버)
```http
POST /billing/webhook
```

**동작**:
- `payments` 기록
- `subscriptions` 상태 반영

**Auth**: Webhook signature 검증

---

## 11. Catalog (카탈로그)

### 11.1 의약품 검색
```http
GET /catalog/drugs?q=아스피린
```

**DB**: `catalog_drugs`

---

### 11.2 건강기능식품 검색
```http
GET /catalog/supplements?q=마그네슘
```

**DB**: `catalog_supplements`

---

### 11.3 식재료 검색
```http
GET /catalog/foods?q=생강
```

**DB**: `foods_master`

---

### 11.4 코드 조회
```http
GET /catalog/codes/{major_code}
```

**DB**: `catalog_major_codes`, `catalog_minor_codes`

---

## 12. Admin (서버 전용)

> 모든 Admin API는 `service_role` 인증 필요

### 12.1 YouTube 캐시 조회/삭제
```http
GET /admin/cache/youtube
DELETE /admin/cache/youtube/{query_hash}
```

**DB**: `youtube_cache`

---

### 12.2 Commerce 캐시 조회/삭제
```http
GET /admin/cache/commerce
DELETE /admin/cache/commerce/{query_hash}
```

**DB**: `commerce_cache`

---

### 12.3 레스토랑 동기화
```http
POST /admin/restaurants/sync
```

**Body**:
```json
{
  "provider": "kakao",
  "region": "서울"
}
```

**DB**: `restaurants`, `restaurant_menus`

---

## 📊 API 요약표

| 도메인 | 엔드포인트 수 | 주요 기능 |
|--------|--------------|----------|
| Auth/Profile | 3 | 프로필 조회/수정, 푸시 토큰 |
| Intake Stack | 4 | 복용 항목 CRUD |
| Schedules | 8 | 스케줄 CRUD, 복용 체크 |
| Input Sessions | 6 | 증상/처방전 세션 관리 |
| Interaction | 1 | 조합 분석 |
| Symptom Content | 3 | 증상 기반 콘텐츠 |
| Restaurant | 5 | 음식점 검색/즐겨찾기 |
| PubMed RAG | 2 | 근거 검색 |
| Reports | 2 | 리포트 생성/조회 |
| Billing | 4 | 구독/결제 |
| Catalog | 4 | 카탈로그 검색 |
| Admin | 3 | 캐시/동기화 관리 |
| **총계** | **45** | |

---

## 🔒 인증 요구사항

| 엔드포인트 | 인증 |
|------------|------|
| `GET /plans` | Public |
| `GET /catalog/*` | Public |
| `GET /symptoms` | Public |
| `/me/*`, `/intake-items/*`, `/sessions/*` | User Token |
| `/admin/*` | Service Role |
| `/billing/webhook` | Webhook Signature |