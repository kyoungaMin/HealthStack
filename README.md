# Health Stack v2

> **처방전 중심 약-근거-동의보감 연결 플랫폼**

"내가 먹는 약을 이해하면, 내 삶의 선택이 달라진다."

---

## 📌 서비스 비전

> Health Stack v2는 **처방전 중심 분석 플랫폼**입니다.
> 사용자가 처방전 사진을 업로드하면:

- **약 정보를 분석**하고
- **식약처 및 PubMed 근거**를 제공하며
- **효능·부작용 증상을 표준화**하고
- **해당 증상을 기반으로 동의보감 식재료 및 처방 정보를 연결**
- **음식 및 생활 가이드**를 제시합니다.

### 우리가 하지 않는 것
- 치료 ❌
- 처방 변경 ❌
- 과장 ❌

### 우리가 하는 것
- **이해**: 내가 먹는 약의 의미
- **연결**: 약 → 증상 → 음식 → 생활
- **선택**: 근거 기반 생활 가이드

---

## 🎯 핵심 차별점

| 기존 약 앱 | Health Stack v2 |
|-----------|-----------------|
| 단순 약 설명 | 약 → 증상 → 음식 연결 |
| 근거 분리 | 식약처 + PubMed 통합 |
| 전통의학 미연결 | 동의보감 RAG 연결 |
| 생활 가이드 부재 | 음식/생활 추천 제공 |
| 정보 나열 | 맥락 기반 설명 |
| 광고 중심 | 근거·출처 중심 |

---

## 🔄 핵심 처리 흐름

```
처방전 (사진/텍스트)
     ↓
약 정규화 (OCR + 성분 매칭)
     ↓
식약처 근거 (효능/용법/금기/이상반응)
     ↓
PubMed 근거 (임상연구/기전/부작용)
     ↓
효능/부작용 → 증상 토큰화
     ↓
동의보감 매핑 (증상 토큰 ↔ 동의보감 증)
     ↓
식재료/음식/생활 가이드
```

---

## 📊 데이터 소스 (4-Layer)

### 🇰🇷 Layer 1: 식약처 (신뢰도 Level A)
- 효능, 용법, 금기, 이상반응, 주의사항
- 공식 의약품 안전 정보
- `drug_label_sources` 테이블 연동

### 🔬 Layer 2: PubMed (신뢰도 Level A)
- 임상 연구, 기전 설명, 부작용 보고, 메타 분석
- 학술적 근거 제공
- `drug_pubmed_links` 테이블 연동

### 📜 Layer 3: 동의보감
- 증(證), 식재료, 처방, 음식 기록
- 전통 한의학 지혜
- `token_tkm_map` 브릿지 연결

### 🌐 Layer 4: 검색 API (Fallback, Level B/C)
- 조건: 식약처·PubMed·동의보감 데이터 부재
- 처리: 2개 이상 출처 교차 검증
- 신뢰도 표시 (A/B/C)

---

## 🔑 증상 토큰 브릿지 (핵심 기술)

약의 효능·부작용을 표준 토큰으로 변환하여 동의보감과 연결합니다.

**예시:**

| 약 | 부작용 | 토큰 | 동의보감 증 |
|----|--------|------|------------|
| 혈압약 | 어지러움 | dizziness | 현훈 |
| 항생제 | 설사 | diarrhea | 설사 |
| 스테로이드 | 부종 | edema | 수종 |

→ `drug_symptom_tokens` → `token_tkm_map` → `tkm_symptom_master` → `foods_master`

---

## 📱 사용자 경험 (5단계)

### Section 1 — 처방전 요약
- 약 목록
- 중복 성분 경고
- 상호작용 가능성

### Section 2 — 약 이해
- 효능 (식약처)
- 주의사항
- 부작용

### Section 3 — 학술 근거
- PubMed 요약 1~3개
- 신뢰도 표시

### Section 4 — 생활 가이드
- 주의 증상 안내
- 식습관 권장

### Section 5 — 동의보감 추천
- 식재료 3~5개
- 간단 이유
- 섭취 주의
- 활용 방법 (요리 영상)

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

### 핵심 엔티티 (v2)

**처방전 → 약 정규화**
- `user_prescriptions`: 처방전 정보
- `user_prescription_drugs`: 처방 약물 목록
- `catalog_drugs`: 약물 카탈로그

**약 → 근거 연결**
- `drug_label_sources`: 식약처 라벨 정보
- `drug_pubmed_links`: PubMed 근거 연결

**증상 토큰 브릿지** ⭐
- `symptom_tokens`: 표준 증상 토큰
- `drug_symptom_tokens`: 약 ↔ 증상 토큰 매핑
- `token_tkm_map`: 증상 토큰 ↔ 동의보감 증 브릿지

**동의보감 → 식재료**
- `tkm_symptom_master`: 동의보감 증(證) 마스터
- `foods_master`: 식재료 정보

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

### 🎯 v2 아키텍처 전환
- **처방전 중심 플랫폼**: 약 → 근거 → 동의보감 연결 구조
- **증상 토큰 브릿지**: 약 부작용을 표준 토큰으로 변환하여 동의보감 연결
- **4-tier 데이터 통합**: 식약처 + PubMed + 동의보감 + 웹검색

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
- **5단계 사용자 경험**: 처방전 요약 → 약 이해 → 학술 근거 → 생활 가이드 → 동의보감 추천

### 📊 문서화
- **SERVICE_PLAN2.md**: v2 통합 기획안
- **PPT 발표 자료**: 21개 슬라이드 (기술/비즈니스 포함)
- **개발일지**: 상세한 작업 내용 및 성능 분석
- **DB 마이그레이션**: 증상 토큰 브릿지 테이블

---

## 🗺️ 로드맵

### Phase 1: MVP ✅ (완료)

**포함 (Core)**
- [x] 처방전 OCR (Naver Clova)
- [x] 약 정규화 (성분 매칭 + 동의어 사전)
- [x] 식약처 라벨 매핑 (`drug_label_sources`)
- [x] PubMed 요약 (RAG 기반)
- [x] 동의보감 식재료 추천 (`token_tkm_map` 브릿지)
- [x] 검색 API fallback (Tavily)
- [x] 4-tier 데이터 신뢰도 (식약처/PubMed/동의보감/검색)
- [x] 증상 토큰화 시스템
- [x] DUR 약물 상호작용 검사
- [x] 성능 최적화 (70초 → 45초, 40% 개선)

### Phase 2: 고도화 🚧 (진행 중)
- [x] 캐싱 전략 (7일 TTL)
- [ ] 사용자 인증 시스템
- [ ] 처방전 이력 관리 (누적 분석)
- [ ] 개인 맞춤 PDF 리포트
- [ ] 가족 약 관리 기능
- [ ] AI 맞춤 식단 추천

### Phase 3: 사업화
- [ ] 모바일 앱 개발 (iOS/Android)
- [ ] 월 구독 모델 (가족 약 관리)
- [ ] 병원 API 연동
- [ ] 건강 콘텐츠 제휴
- [ ] 프리미엄 근거 분석
- [ ] B2B API 제공 (병원/약국)

### Phase 4: 글로벌 확장
- [ ] ATC 코드 기반 글로벌 확장
- [ ] RxNorm 연계 (미국)
- [ ] FDA / EMA 데이터 추가 (미국/유럽)
- [ ] 다국어 지원

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
| **서비스 기획안 (v2)** | [`docs/SERVICE_PLAN2.md`](./docs/SERVICE_PLAN2.md) ⭐ |
| 서비스 이해 (v1) | [`docs/SERVICE_PLAN.md`](./docs/SERVICE_PLAN.md) |
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
| 프로젝트명 | Health Stack v2 |
| 서비스명 | 내몸설명서 |
| 비전 | "내가 먹는 약을 이해하면, 내 삶의 선택이 달라진다." |
| 핵심 개념 | 처방전 중심 약-근거-동의보감 연결 플랫폼 |
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
- ✅ **4-tier 데이터 통합**: 식약처(A) → PubMed(A) → 동의보감 → 웹검색(B/C)
- ✅ **증상 토큰 브릿지**: 약 부작용 ↔ 동의보감 증 연결
- ✅ **RAG 기반 근거 제공**: OpenAI + PubMed 논문
- ✅ **동의보감 디지털화**: 전통 한의학 + 현대 의학 통합
- ✅ **실시간 약물 상호작용**: DUR API 연동
- ✅ **AI 맞춤 생활 가이드**: 식재료 + 음식 + 영상
- ✅ **성능 최적화**: 비동기 처리 + 스마트 캐싱 (40% 개선)

---

## ✨ 전략적 의미

이 구조는:

- ✅ **기술성**: NLP + RAG + 근거 통합
- ✅ **신뢰성**: 공공데이터 기반 (식약처 + PubMed)
- ✅ **차별성**: 전통의학 디지털 자산화 (동의보감 RAG)
- ✅ **확장성**: 글로벌 확장 가능 (ATC/RxNorm/FDA)
- ✅ **사업성**: 구독/API/제휴 수익 모델

---

## 🎯 비전

> **Health Stack v2는**
>
> "약을 이해하는 플랫폼"에서
> "약을 기반으로 삶을 관리하는 플랫폼"으로 확장합니다.

**모든 사람이 자신이 먹는 약의 의미를 이해하고,
근거 있는 선택으로 더 건강한 삶을 살 수 있도록 돕습니다.**

---

## 🔐 안전 정책

- ✅ 의료 진단/처방 변경 권고 금지
- ✅ "참고 정보" 명시
- ✅ 의사 상담 권장 문구 고정
- ✅ 출처 명확화 (신뢰도 Level A/B/C 표시)

---

**최종 업데이트**: 2026-02-20
**버전**: 2.0.0 (v2 MVP)
**다음 업데이트**: 사용자 인증 시스템 구축
