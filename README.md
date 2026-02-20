# Health Stack

> **내 몸에 들어가는 모든 것의 설명서**

약 · 건강기능식품 · 음식을 함께 보고, 이해하고, 관리합니다.

---

## 📌 서비스 한 문장 정의

> Health Stack은 사용자가 입력한 **증상과 처방전**을 바탕으로,  
> 약·건강정보·동의보감·음식·지역 식당·판매처를 하나의 맥락으로 연결해  
> **"내 몸에 지금 필요한 선택지"**를 설명해주는 서비스입니다.

- 치료 ❌
- 처방 변경 ❌
- 과장 ❌
- **이해 + 판단 보조 + 생활 선택 가이드 ⭕**

---

## 🎯 핵심 차별점

| 기존 서비스 | Health Stack |
|------------|--------------|
| 정보 나열 | 맥락 기반 설명 |
| 약 / 음식 분리 | 하나의 스택으로 통합 |
| 광고 중심 | 근거·출처 중심 |
| 단기 조회 | 누적 관리 |

---

## 📱 사용자 입력 방식

### A. 증상만 입력
```
"속이 더부룩해요" / "잠을 잘 못 자요" / "손발이 차요"
```
→ 생활 관리 관점의 정보 제공

### B. 처방전만 입력
```
처방전 사진 업로드 / 약 이름 직접 입력
```
→ 지금 먹는 약 이해

### C. 증상 + 처방전 함께 입력 (핵심)
```
"혈압약을 먹고 있는데 자꾸 어지러워요"
```
→ 약 정보 + 생활 선택을 함께 제시

---

## 🔄 처리 흐름

```
[사용자 입력]
     ↓
[입력 해석] → 증상 분류 / 처방약 인식
     ↓
[Health Stack 구성] → 현재 복용 약 / 증상 맥락 / 주의 조건
     ↓
[정보 레이어 결합] → 현대의학 정보 / 동의보감 생활 가이드
     ↓
[결과 제공] → 설명 / 추천 / 선택지
```

---

## 📋 제공 정보

### 기본 설명
1. 지금 상태 요약
2. 약 / 증상 이해 설명
3. 주의사항

### 동의보감 기반 식재료 추천
- 증상에 따라 도움이 될 수 있는 식재료 목록
- 왜 이 식재료가 권장되는지 (동의보감 근거)
- 피하면 좋은 음식 방향

### 확장 콘텐츠
4. 활용 방법 (요리 영상)
5. 주변 음식점 추천 (지도 API 연동)
6. 재료 구매 링크

---

## 🏗️ 기술 스택

| 영역 | 기술 |
|------|------|
| **Frontend** | React 19.2.4 + TypeScript + Vite |
| **스타일링** | Tailwind CSS + Pretendard Font |
| **Backend** | FastAPI + Uvicorn (Python 3.11+) |
| **Database** | PostgreSQL (Supabase) |
| **AI/ML** | OpenAI GPT-4o-mini (주), Google Gemini (보조) |
| **RAG** | PubMed + Tavily + 식약처 API |
| **OCR** | Naver Clova OCR |
| **공공 데이터** | 식약처 DrbEasyDrugInfo, DUR, 낱알식별 API |
| **비동기 처리** | AsyncIO + aiohttp |
| **캐싱** | JSON 파일 기반 (7일 TTL) |

---

## 📊 데이터베이스 구조

### 테이블 통계 (총 40개)

| 도메인 | 테이블 수 | 설명 |
|--------|----------|------|
| 사용자 인증 & 프로필 | 4 | auth_users, user_profiles, user_preferences, user_push_tokens |
| 마스터 데이터 | 4 | foods_master, disease_master, catalog_drugs, catalog_supplements |
| 복용 관리 | 3 | user_intake_items, intake_schedules, intake_logs |
| 콘텐츠 매핑 | 6 | symptom_ingredient_map, symptom_recipe_map, symptom_video_map 등 |
| 상호작용 & RAG | 3 | interaction_facts, pubmed_papers, pubmed_embeddings |
| 결제 & 구독 | 4 | plans, subscriptions, payments, reports |
| 입력 세션 레이어 | 5 | user_input_sessions, user_symptoms, user_prescriptions 등 |
| 레스토랑 추천 | 7 | restaurants, restaurant_menus, restaurant_search_results 등 |
| 카탈로그 코드 | 2 | catalog_major_codes, catalog_minor_codes |
| 캐시 테이블 | 2 | youtube_cache, commerce_cache |

---

## 🔌 API 현황

### 총 45개 엔드포인트

| 도메인 | 엔드포인트 | 주요 기능 |
|--------|-----------|----------|
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

---

## 📁 프로젝트 구조

```
health-stack/
├── README.md                      ← 📍 현재 문서
│
├── docs/                          ← 📚 설계 문서
│   ├── SERVICE_PLAN.md            ← 서비스 기획안
│   ├── api.md                     ← API 설계 (45개)
│   ├── database.md                ← DB 설계 철학
│   ├── WORKFLOW.md                ← 서비스 워크플로우
│   │
│   ├── erd/                       ← ERD & 스키마
│   │   ├── schema.integrated.dbml ← 🔑 Source of Truth
│   │   ├── erd-full.md            ← 전체 ERD
│   │   └── *.png                  ← ERD 이미지
│   │
│   └── architecture/              ← 아키텍처
│       ├── architecture.md
│       └── report-pipeline.md
│
├── src/                           ← 소스 코드
└── .agent/                        ← AI Agent 설정
```

---

## 🎉 최근 업데이트 (2026-02-20)

### ⚡ 성능 최적화
- **Gemini API 스킵 → OpenAI 직접 사용**: 약물당 3-5초 절감
- **PubMed 검색 간소화**: max_results 2→1로 약물당 1-2초 절감
- **비동기 병렬 처리 유지**: asyncio.gather 활용
- **총 성능 향상**: 70-80초 → 45초 (약 40% 개선)

### 🎥 영상 검색 개선
- **2-tier fallback 전략**: 구체적 검색 → 일반 검색
- **검색 성공률**: 거의 100% 보장
- **상세 에러 피드백**: 사용자 친화적 메시지

### 🎨 UI/UX 개선
- **Pretendard 폰트 적용**: 한글 최적화, 가독성 향상
- **Anti-aliasing**: 부드러운 렌더링
- **깔끔한 디자인**: 현대적이고 전문적인 느낌

### 📊 문서화
- **PPT 발표 자료**: 21개 슬라이드 (기술/비즈니스 포함)
- **개발일지**: 상세한 작업 내용 및 성능 분석
- **DB 마이그레이션**: 약물 번역 캐시 테이블

---

## 🗺️ 로드맵

### Phase 1: MVP ✅ (완료)
- [x] DB 스키마 설계 (40개 테이블)
- [x] API 설계 (45개 엔드포인트)
- [x] 처방전 OCR 분석 (Naver Clova)
- [x] 약물 정보 제공 (3-tier 신뢰도)
- [x] 동의보감 기반 식재료 추천
- [x] AI 맞춤 레시피 생성
- [x] YouTube 영상 연동
- [x] DUR 약물 상호작용 검사

### Phase 2: 고도화 🚧 (진행 중)
- [x] 성능 최적화 (40% 향상, 70초 → 45초)
- [x] RAG 기반 약물 정보 (PubMed + OpenAI)
- [x] 3-tier 데이터 신뢰도 평가
- [x] 캐싱 전략 (7일 TTL)
- [ ] 사용자 인증 시스템
- [ ] 처방전 이력 관리
- [ ] 개인 맞춤 PDF 리포트

### Phase 3: 비즈니스
- [ ] 모바일 앱 개발
- [ ] 음식점 추천 (지도 API 연동)
- [ ] 구독형 서비스
- [ ] B2B API 제공
- [ ] 전문가 협업 (약사/영양사)

---

## 🔐 보안 설계

### RLS (Row Level Security)
- 모든 개인 데이터: `user_id = auth.uid()` 기반 보호
- 공용 데이터: 읽기 허용, 쓰기는 서버 권한

### 의료 리스크 대응
- 진단/처방/복약 지시 표현 금지
- 불확실성 그대로 표현
- 위험 조합 시 의료진 상담 권고

---

## 📖 문서 가이드

| 목적 | 문서 |
|------|------|
| 서비스 이해 | [`docs/SERVICE_PLAN.md`](./docs/SERVICE_PLAN.md) |
| DB 구조 파악 | [`docs/erd/erd-full.md`](./docs/erd/erd-full.md) |
| API 개발 | [`docs/api.md`](./docs/api.md) |
| 아키텍처 리뷰 | [`docs/architecture/architecture.md`](./docs/architecture/architecture.md) |
| **PPT 발표 자료** | [`docs/HealthStack_PPT_자료.md`](./docs/HealthStack_PPT_자료.md) |
| **개발일지** | [`docs/개발일지_2026-02-20.md`](./docs/개발일지_2026-02-20.md) |
| DB 마이그레이션 | [`docs/erd/migration_drug_translation.sql`](./docs/erd/migration_drug_translation.sql) |

---

## 🚀 시작하기

### 1. 저장소 클론
```bash
git clone https://github.com/kyoungaMin/HealthStack.git
cd HealthStack
```

### 2. 환경 설정
```bash
# 환경변수 파일 생성
cp .env.example .env
# .env 파일에 API 키 설정 필요:
# - OPENAI_API_KEY
# - NAVER_OCR_SECRET_KEY
# - YOUTUBE_API_KEY
# - KOREA_DRUG_API_KEY
# 등
```

### 3. 백엔드 실행
```bash
# Python 의존성 설치
pip install fastapi uvicorn openai supabase aiohttp python-multipart

# 서버 실행
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 프론트엔드 실행
```bash
cd app/healthstack

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
# → http://localhost:3002
```

### 5. 서비스 접속
- **프론트엔드**: http://localhost:3002
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

---

## 📌 프로젝트 정보

| 항목 | 내용 |
|------|------|
| 프로젝트명 | Health Stack |
| 서비스명 | 내몸설명서 |
| 슬로건 | 내 몸에 들어가는 모든 것의 설명서 |
| 상태 | ✅ **MVP 완성 / 성능 최적화 완료** |
| 저장소 | https://github.com/kyoungaMin/HealthStack |
| 프론트엔드 | http://localhost:3002 |
| 백엔드 API | http://localhost:8000 |

---

## 📊 성능 지표

| 항목 | 수치 |
|------|------|
| 처방전 분석 속도 | 45초 (이전 70-80초) |
| 성능 개선율 | 40% ↑ |
| 캐시 히트 시 | 5초 이내 |
| OCR 정확도 | 95% 이상 |
| API 통합 | 10+ 외부 API |
| 코드 품질 | TypeScript + Python Type Hints |

---

## 🏆 주요 성과

- ✅ **처방전 OCR 자동 분석**: Naver Clova 활용
- ✅ **3-tier 신뢰도 평가**: 식약처(A) → PubMed(B) → 웹검색(C)
- ✅ **RAG 기반 약물 정보**: OpenAI + PubMed 논문
- ✅ **동의보감 DB 통합**: 전통 한의학 + 현대 의학
- ✅ **실시간 약물 상호작용**: DUR API 연동
- ✅ **AI 레시피 생성**: 맞춤형 건강 요리법
- ✅ **성능 최적화**: 비동기 처리 + 스마트 캐싱

---

## ✨ 비전

> **Health Stack은 "건강 정보를 소비하는 서비스"가 아니라
> "내 몸을 이해하는 인프라"를 만드는 프로젝트입니다.**

**모든 사람이 자신의 건강을 쉽게 이해하고 관리할 수 있는 세상을 만듭니다.**

---

**최종 업데이트**: 2026-02-20
**버전**: 1.0.0 (MVP)
**다음 업데이트**: 사용자 인증 시스템 구축
