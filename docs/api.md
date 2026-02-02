# 🔌 API Design (FastAPI / Node)

이 문서는 Health Stack 서비스의 API 설계를 정의합니다.
- 인증: Supabase Auth (Google/Kakao OAuth)
- 권한: Supabase RLS
- 서버 역할: 결제 웹훅, PubMed 수집/요약, RAG, PDF 생성, 고급 조합 분석

---

## 0. 공통 규칙

### Base URL
- `/api/v1`

### 인증
- 클라이언트는 Supabase 세션 토큰을 사용
- 서버는 Supabase service_role로 운영(웹훅/배치/RAG)

### 응답 규칙
- 성공: `{ "data": ... }`
- 오류: `{ "error": { "code": "...", "message": "...", "details": ... } }`

---

## 1. Auth / Profile

### 1.1 내 프로필 조회
- `GET /me`
- DB: `user_profiles`, `user_preferences`

### 1.2 생활시간/선호 설정 저장
- `PATCH /me`
- Body:
```json
{
  "wake_time": "07:00",
  "breakfast_time": "08:00",
  "lunch_time": "12:30",
  "dinner_time": "19:00",
  "bed_time": "23:00",
  "notification_enabled": true
}

## 2. Intake Stack (복용 스택)
### 2.1 복용 항목 목록

GET /intake-items

DB: user_intake_items

### 2.2 복용 항목 생성

POST /intake-items

## Body 예:
{
  "item_type": "supplement",
  "display_name": "마그네슘",
  "catalog_supplement_id": 12,
  "dose_text": "1정",
  "route": "oral"
}

2.3 복용 항목 수정/비활성

PATCH /intake-items/{id}

active=false로 soft off 권장

2.4 복용 항목 삭제

DELETE /intake-items/{id}

3. Schedules (시간표/알림)
3.1 스케줄 목록

GET /schedules

DB: intake_schedules

3.2 스케줄 생성

POST /schedules

Body 예:

{
  "intake_item_id": 101,
  "pattern": "daily",
  "time_anchor": "breakfast",
  "offset_minutes": 15,
  "rules": { "separate_by_minutes": 120 }
}

3.3 오늘 일정 생성(서버/클라이언트)

POST /schedule-generate/today

역할:

생활시간 + 스케줄 규칙으로 오늘 복용 타임라인 계산

필요 시 intake_logs에 scheduled row 생성

3.4 오늘 복용 타임라인 조회

GET /intake/today?date=YYYY-MM-DD

DB: intake_schedules, intake_logs, user_profiles

3.5 복용 체크

POST /intake/logs/{id}/take

DB: intake_logs (taken_at, status='taken')

3.6 스킵/스누즈

POST /intake/logs/{id}/skip

POST /intake/logs/{id}/snooze (minutes)

4. Interaction Check (조합 분석)
4.1 조합 체크

POST /interactions/check

Body:

{
  "items": [
    { "type": "drug", "ref": "123" },
    { "type": "supplement", "ref": "12" },
    { "type": "food", "ref": "100100" }
  ]
}


동작:

interaction_facts 조회(룰 기반)

없으면 RAG 경로로 보강(Optional)

5. Symptom → Meal / Content (증상 식단/콘텐츠)
5.1 증상 기반 번들 조회

GET /symptoms/{symptom_id}/bundle

반환:

helpful/avoid 재료

레시피

영상(큐레이션)

DB:

symptom_ingredient_map

symptom_recipe_map + recipes

symptom_video_map + content_videos

5.2 오늘 식단 추천

POST /mealplan/today

Body:

{
  "symptom_ids": [1, 2],
  "constraints": { "exclude": ["spicy"] }
}


동작:

증상 매핑 기반 큐레이션 + 사용자 제외 조건

6. PubMed RAG Search (근거 검색)
6.1 RAG 검색

POST /rag/pubmed

Body:

{ "query": "magnesium insomnia efficacy", "top_k": 5 }


DB:

pubmed_embeddings (vector search)

pubmed_papers

6.2 PubMed 수집 배치(서버)

POST /admin/pubmed/ingest

Server only (service_role)

7. Reports (PDF)
7.1 리포트 생성 요청

POST /reports

Body:

{
  "report_type": "stack_safety",
  "inputs": { "items": [ ... ], "notes": "..." }
}


동작:

서버가 reports.status='draft' 생성

비동기 생성 후 generated로 업데이트 + pdf_path

7.2 리포트 목록/조회

GET /reports

GET /reports/{id}

8. Billing (구독/결제)
8.1 플랜 조회

GET /plans

DB: plans

8.2 구독 생성(결제 페이지/세션 생성)

POST /billing/subscribe

Server only 추천

8.3 결제 웹훅(서버)

POST /billing/webhook

동작:

payments 기록

subscriptions 상태 반영

9. Rate Limit / Audit (옵션)

search_logs 기록 (검색/응답시간/cache_hit)

user_quota_monthly로 월간 제한 관리

user_request_dedupe로 중복 요청 캐시 가능


---

# 3) `docs/architecture.md`

```md
# 🧱 Architecture (Supabase + App + AI)

이 문서는 Health Stack 서비스의 전체 아키텍처를 설명합니다.

---

## 1. 목표

- 사용자가 복용 중인 **약/건기식/음식 스택**을 관리
- **복용 시간표 + 알림**으로 실행을 돕고
- **상호작용/부작용/주의**를 근거 기반으로 요약
- 증상 기반 **식단/레시피/영상/판매 링크** 제공
- **PDF 리포트 + 구독 결제**로 수익화
- PubMed 기반 **RAG 근거 검색**으로 신뢰 강화

---

## 2. 구성 요소

### 2.1 Frontend (Web/Mobile)
- 기능
  - 복용 스택 입력/관리
  - 복용 체크(오늘)
  - 증상 선택 → 식단/콘텐츠
  - 리포트 구매/구독
- 인증
  - Supabase Auth (Google/Kakao)

### 2.2 Supabase
- Postgres + RLS
- Storage (PDF/이미지)
- Auth (OAuth)
- Edge Functions(선택) 또는 서버 API

### 2.3 Backend API (FastAPI or Node)
- 역할(서버만 하는 것)
  - 결제 웹훅 처리
  - PubMed 수집/요약/임베딩 배치
  - RAG 검색 엔드포인트
  - PDF 리포트 생성(비동기)
  - 고급 상호작용 분석(룰+RAG 혼합)

### 2.4 AI Layer
- 임베딩:
  - PubMed abstract chunking → `pubmed_embeddings`
- RAG:
  - vector search → 근거 선택 → 요약/충돌 설명
- 안전장치:
  - 단정 금지
  - 근거 수준 표시
  - 의료진 상담 권고 문구

---

## 3. 데이터 흐름(주요 시나리오)

### 3.1 복용 스택 등록 → 시간표 생성
1) 사용자: 복용 항목 등록 (`user_intake_items`)
2) 사용자: 스케줄 등록 (`intake_schedules`)
3) 서버/앱: 오늘 타임라인 생성
4) DB: `intake_logs`에 scheduled row 생성
5) 앱: 푸시 알림 발송(토큰: `user_push_tokens`)

### 3.2 복용 체크
1) 사용자: “복용 완료”
2) DB: `intake_logs.taken_at`, `status='taken'`
3) 통계: `user_daily_stats` 갱신(선택)

### 3.3 증상 기반 식단/콘텐츠
1) 사용자: 증상 선택 (`disease_master`)
2) DB:
   - 재료: `symptom_ingredient_map`
   - 레시피: `symptom_recipe_map` + `recipes`
   - 영상: `symptom_video_map` + `content_videos`
3) 앱: 레시피/영상/판매 링크 노출 (`ingredient_product_links`)

### 3.4 조합 분석(룰 + RAG)
1) 앱: 조합 체크 요청
2) 1차: `interaction_facts` 룰 조회
3) 2차(Optional): `pubmed_embeddings` 기반 RAG 검색
4) 결과: severity/evidence_level + 요약 + 근거(pmids)

### 3.5 리포트 생성(PDF)
1) 앱: 리포트 요청 → `reports(draft)`
2) 서버: 비동기 작업(Queue/cron/worker)
3) 생성 완료:
   - Storage에 PDF 업로드
   - `reports.status='generated'`, `pdf_path` 업데이트

### 3.6 결제/구독
1) 앱: 구독 요청
2) 서버: 결제 세션 생성
3) PG 웹훅 → 서버 수신
4) DB:
   - `payments` 기록
   - `subscriptions` 상태 업데이트
5) 앱: 구독 상태 UI 반영

---

## 4. 보안 설계

### 4.1 RLS (핵심)
- 개인 데이터: 본인만 접근
- 공용 데이터: 읽기 허용, 쓰기 제한

### 4.2 결제 데이터
- 클라이언트가 결제 레코드를 직접 쓰지 않도록 설계
- 웹훅 기반으로 `payments`, `subscriptions`만 서버가 갱신

### 4.3 의료 리스크 대응
- 진단/처방/복약 지시 표현 금지
- 불확실성 그대로 표현
- 위험 조합은 상담 권고

---

## 5. 운영/확장 로드맵

### MVP
- 복용 스택 + 시간표 + 체크
- 기본 조합 체크(룰 기반)
- 증상 기반 식단/콘텐츠
- 구독 없이 Free로 런칭 가능(리포트는 후순위)

### v1
- PDF 리포트 + 결제
- PubMed RAG 검색
- 상호작용 지식베이스 확장

### v2
- 가족 계정/공유
- 개인화 강화(루틴/체크 기반)
- B2B API(콘텐츠/근거/리포트)

---

## 6. 다이어그램(텍스트)



[Client]
| Supabase Auth (OAuth)
v
[Supabase Postgres + RLS] <-----> [Backend API(service_role)]
| |
| Storage (PDF) | PubMed ingest + embeddings
| | RAG search
| | Billing webhook
v v
[Push Provider] [AI Models]