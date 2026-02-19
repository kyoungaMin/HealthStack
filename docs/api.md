# 🔌 API Design (FastAPI / Node)

이 문서는 Health Stack 서비스의 API 설계를 정의합니다.

> **소스**: [`schema.integrated.dbml`](./erd/schema.integrated.dbml)
> **최종 업데이트**: 2026-02-20

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

## 6. Symptom & Prescription Analysis (Step-by-Step Pipeline)

### [Step 1] 증상/처방전 초기 인식 (Extraction)
사용자의 입력을 빠르게 인식하고 키워드를 추출합니다. (1차 필터링)

```http
POST /analyze/step1-extract
```

**Request Body (Symptom)**:
```json
{
  "search_type": "symptom",
  "text": "머리가 지끈거리고 소화가 안돼요"
}
```

**Request Body (Prescription)**:
```json
{
  "search_type": "prescription",
  "image_url": "https://storage.../rx_image.jpg"
}
```

**Response**:
```json
{
  "data": {
    "session_id": "uuid-1234",
    "detected_keywords": [
      { "keyword": "두통", "confidence": 0.95 },
      { "keyword": "소화불량", "confidence": 0.88 },
      { "keyword": "복부팽만", "confidence": 0.72 }
    ],
    "ocr_text": "타이레놀이알서방정..." // (처방전일 경우)
  }
}
```

---

### [Step 2] 검색 및 후보 선택 (Search & Select)
1단계에서 확인된 키워드를 바탕으로 DB/Vector 검색을 수행하여 후보군을 제공합니다.

```http
POST /analyze/step2-search
```

**Request Body**:
```json
{
  "session_id": "uuid-1234",
  "confirmed_keywords": ["두통", "소화불량"]
}
```

**Response**:
```json
{
  "data": {
    "candidates": {
      "tkm_symptoms": [
        {
          "id": 101,
          "name": "식적(Food Stagnation)",
          "description": "체기로 인한 두통과 복부 팽만감",
          "match_score": 0.92
        },
        {
          "id": 105,
          "name": "두풍증(Head Wind)",
          "description": "바람을 쐬면 머리가 아픈 증상",
          "match_score": 0.85
        }
      ],
      "modern_drugs": [
        {
          "id": 501,
          "name": "타이레놀",
          "efficacy": "해열 및 진통 완화",
          "category": "NSAID"
        },
        {
          "id": 505,
          "name": "베아제",
          "efficacy": "소화 불량 개선",
          "category": "Digestive"
        }
      ]
    }
  }
}
```

---

### [Step 3] 최종 리포트 생성 (Synthesize)
사용자가 선택한 후보를 바탕으로 최종 맞춤형 리포트를 생성합니다.

```http
POST /analyze/step3-report
```

**Request Body**:
```json
{
  "session_id": "uuid-1234",
  "selected_candidates": [
    { "type": "tkm_symptom", "id": 101 }, // 식적
    { "type": "modern_drug", "id": 501 }   // 타이레놀 (복용 중인 약)
  ]
}
```

**Response**:
```json
{
  "data": {
    "summary": "식적(체기)으로 인한 두통이 의심됩니다.",
    "medication_guide": {
      "drug_name": "타이레놀",
      "warning": "음주 전후 복용 금지 (간 손상 위험)",
      "usage": "식후 30분 복용 권장"
    },
    "food_therapy": {
      "recommended": [
        { "name": "무(Radish)", "reason": "소화를 돕고 두통 완화" },
        { "name": "생강차", "reason": "위장 운동 촉진" }
      ],
      "avoid": [
        { "name": "밀가루 음식", "reason": "소화 불량 유발" }
      ]
    },
    "lifestyle_advice": "식사 후 바로 눕지 마시고 가벼운 산책을 하세요."
  }
}
```

---

## 7. Symptom → Content (증상 콘텐츠)

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

---

## 6-B. Analysis Pipeline — 처방전 통합 분석 (구현 완료)

> Base URL: `/api/v1/analyze`
> **실제 구현된 FastAPI 엔드포인트** (2026-02-20 기준)

### [처방전 이미지 통합 분석]

```http
POST /api/v1/analyze/prescription
Content-Type: multipart/form-data
```

**파라미터**: `file` (이미지 파일 — jpg/png/webp)

**처리 파이프라인**:
```
Gemini Vision OCR → DUR 병용금기 → MFDS Level A
→ PubMed Level B → Tavily 웹 Level C → 동의보감 매핑 → 유사처방
```

**Response**:
```json
{
  "prescriptionSummary": {
    "drugList": ["타이레놀정", "아목시실린캡슐"],
    "warnings": "아목시실린 + 타이레놀: 간 부담 주의 (DUR)"
  },
  "drugDetails": [
    {
      "name": "타이레놀정",
      "efficacy": "해열 및 진통 완화",
      "sideEffects": "간 손상 (과다복용 시)"
    }
  ],
  "academicEvidence": {
    "summary": "식약처 공인 정보 + PubMed 논문 2편 분석 결과",
    "trustLevel": "A",
    "papers": [
      { "title": "...", "url": "https://pubmed.ncbi..." }
    ]
  },
  "lifestyleGuide": {
    "symptomTokens": ["통증", "발열"],
    "advice": "복약 중 음주 금지. 충분한 수분 섭취."
  },
  "donguibogam": {
    "foods": [
      { "name": "생강", "reason": "위장 기능 보호", "precaution": "" }
    ],
    "donguiSection": "두통 관련 동의보감 처방",
    "traditionalPrescriptions": [],
    "tkmPapers": []
  }
}
```

**trustLevel**: `"A"` (MFDS 있음) | `"B"` (PubMed만) | `"C"` (Tavily/AI)

---

### [Step-by-Step 분석]

```http
POST /api/v1/analyze/step1-extract    # 키워드 추출
POST /api/v1/analyze/step2-search     # DB/Vector 후보 검색
POST /api/v1/analyze/step3-report     # 최종 리포트 생성
```

---

## 6-C. 낱알 식별 (Pill Identification)

> Base URL: `/api/v1/analyze`
> 데이터: 식약처 MdcinGrnIdntfcInfoService03 (Level A)

### 약품명으로 낱알 조회

```http
POST /api/v1/analyze/pill-search/name
```

**Body**:
```json
{ "drug_name": "타이레놀정" }
```

**Response**:
```json
{
  "total": 3,
  "items": [
    {
      "itemSeq": "198601234",
      "itemName": "타이레놀정500밀리그람",
      "manufacturer": "한국얀센",
      "chart": "흰색의 장방형 필름코팅정",
      "imageUrl": "https://nedrug.mfds.go.kr/pbp/cmn/itemImageDownload/...",
      "printFront": "TYLENOL",
      "printBack": "",
      "drugShape": "장방형",
      "colorFront": "하양",
      "colorBack": "하양",
      "lineFront": "-",
      "lineBack": "",
      "lengLong": "19.1",
      "lengShort": "8.5",
      "thick": "5.2",
      "formName": "필름코팅정",
      "className": "해열.진통.소염제",
      "etcOtc": "일반의약품",
      "ediCode": "643500260",
      "source": "MFDS_A"
    }
  ]
}
```

---

### 외형으로 낱알 검색 (약 모양으로 식별)

```http
POST /api/v1/analyze/pill-search/appearance
```

**Body** (하나 이상 필수):
```json
{
  "drug_shape": "원형",
  "color_class1": "하양",
  "color_class2": "",
  "mark_front": "500",
  "mark_back": "",
  "leng_long": "",
  "leng_short": ""
}
```

**drug_shape 예시**: `원형` | `타원형` | `장방형` | `삼각형` | `사각형` | `오각형` | `육각형` | `팔각형` | `기타`

**color 예시**: `하양` | `노랑` | `주황` | `분홍` | `빨강` | `갈색` | `연두` | `초록` | `청록` | `파랑` | `남색` | `자주` | `보라` | `회색` | `검정` | `투명`

---

## 📊 API 요약표

> **최종 업데이트**: 2026-02-20

### 구현 완료 (FastAPI — `app/`)

| 엔드포인트 | 메서드 | 설명 | Level |
|-----------|--------|------|-------|
| `/api/v1/analyze/prescription` | POST | 처방전 이미지 통합 분석 | A/B/C |
| `/api/v1/analyze/step1-extract` | POST | 증상/처방전 키워드 추출 | — |
| `/api/v1/analyze/step2-search` | POST | DB/Vector 후보 검색 | — |
| `/api/v1/analyze/step3-report` | POST | 최종 리포트 생성 | — |
| `/api/v1/analyze/pill-search/name` | POST | 약품명으로 낱알 외형 조회 | A |
| `/api/v1/analyze/pill-search/appearance` | POST | 외형으로 약 식별 | A |

### 설계 명세 (docs/api.md — 구현 예정)

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
| **구현 완료 (Analyze)** | **6** | **처방전 분석 + 낱알 식별** |
| **총계** | **51** | |

---

## 🔌 통합 외부 API

| API | 용도 | Evidence | 엔드포인트 |
|-----|------|----------|-----------|
| Gemini 2.0 Flash | Vision OCR + 생성 | C | `generativelanguage.googleapis.com` |
| Naver Clova OCR | 처방전 OCR | — | `clovaocr.apigw.ntruss.com` |
| PubMed E-utilities | 임상 논문 검색 | B | `eutils.ncbi.nlm.nih.gov` |
| 식약처 DrbEasyDrugInfoService | 약물 라벨 | **A** | `apis.data.go.kr/1471000/DrbEasyDrugInfoService` |
| 식약처 MdcinGrnIdntfcInfoService03 | 낱알 외형 식별 | **A** | `apis.data.go.kr/1471000/MdcinGrnIdntfcInfoService03` |
| DUR 병용금기 (OdCloud) | 병용금기 | **A** | `api.odcloud.kr/api/15089525/v1/...` |
| 한국전통지식포털 SimPreInfoService | 유사처방 | TKM | `apis.data.go.kr/1430000/SimPreInfoService` |
| Tavily Search | 웹 검색 fallback | C | `api.tavily.com/search` |
| Supabase | DB + Auth + Vector | — | `*.supabase.co` |
| YouTube Data v3 | 영상 콘텐츠 | — | `youtube.googleapis.com` |

---

## 🔒 인증 요구사항

| 엔드포인트 | 인증 |
|------------|------|
| `GET /plans` | Public |
| `GET /catalog/*` | Public |
| `GET /symptoms` | Public |
| `POST /api/v1/analyze/*` | Public (현재) / User Token (예정) |
| `/me/*`, `/intake-items/*`, `/sessions/*` | User Token |
| `/admin/*` | Service Role |
| `/billing/webhook` | Webhook Signature |