# Health Stack 개발일지

> **프로젝트**: Health Stack v2 — 처방전 중심 약·근거·동의보감 연결 플랫폼
> **스택**: FastAPI · Supabase · Gemini · PubMed · 식약처 공공데이터
> **저장소**: `c:/AI/dev5`

---

## 2026-02-02

### 프로젝트 착수

- Health Stack 프로젝트 개요 문서화 (`docs/Readme.md`)
- ERD 다이어그램 초안 작성 — 9개 섹션 (`docs/erd/sections/`)
- 핵심 비전 확정:
  > "내가 먹는 약을 이해하면, 내 삶의 선택이 달라진다."
- 데이터 흐름 설계:
  ```
  처방전 → 약 정규화 → 식약처 근거 → PubMed 근거
        → 효능/부작용 토큰화 → 동의보감 매핑 → 식재료/생활 가이드
  ```

---

## 2026-02-04

### 아키텍처 & API 설계 확정

- `docs/api.md` 초안 완성 — 12개 도메인, 45개 엔드포인트 명세
- `schema.integrated.dbml` 통합 ERD 작성
- Supabase 인증 + `service_role` 운영 구조 결정
- Base URL `/api/v1` 확정

---

## 2026-02-06

### DB 스키마 확장

- `symptom_pubmed_map`, `ingredient_pubmed_map` 테이블 추가
  - 증상 ↔ PubMed 논문 연결 인덱스
  - 식재료 ↔ PubMed 논문 연결 인덱스
- Supabase 마이그레이션 파일 관리 체계 수립

---

## 2026-02-07

### 핵심 서비스 구현 (1차)

**Supabase 마이그레이션**
- 동의보감 테이블 생성 (`20260213194500`)
- master 테이블 populate (`20260214110000` ~ `110300`)
- Embeddings 테이블 생성 (`20260214113000`)

**서비스 구현**
- `AnalyzeService` — 증상 분석 → 동의보감 식재료 추천, 3단계 Fallback
- `MedicationService` — PubMed RAG + Gemini 생성 (약물 정보)
- Step-by-Step 분석 파이프라인 (`StepByStepAnalysisService`)
  - Step 1: 키워드 추출
  - Step 2: DB/Vector 검색
  - Step 3: 리포트 생성

**Golden Q&A 통합**
- `docs/test/golden_questions_v1.md` — 표준 테스트 케이스 작성
- 분석 결과 검증 파이프라인 구축

---

## 2026-02-08

### OCR 파이프라인 개선

**Naver Clova OCR 연동**
- `naver_ocr_service.py` 구현
- 처방전 이미지 → 텍스트 추출

**Gemini Vision OCR 통합**
- `PrescriptionService._extract_drugs_from_image()` 구현
- Gemini 2.0 Flash Vision으로 처방전 약물 목록 JSON 추출
- JSON 파싱 안정화 (마크다운 코드블록 처리)

**DUR 병용금기 서비스**
- `DurService` 구현 — 식약처 병용금기약물 공공데이터 API
- API: `api.odcloud.kr/api/15089525/v1/uddi:3f2efdac...`
- 심각도 분류: `CONTRAINDICATED` / `CAUTION`

---

## 2026-02-11

### 처방전 분석 통합 파이프라인 완성

**`PrescriptionService` 구현** (처방전 이미지 → 5섹션 리포트)
```
Step 1  Gemini Vision OCR         → drugList 추출
Step 2  DUR API                   → 병용금기 경고
Step 3  MFDS (식약처)             → Level A 약물 정보
Step 4  PubMed RAG                → Level B 학술 근거
Step 5  AnalyzeService            → 동의보감/TKM 매핑
Step 6  SimPreService             → 유사처방 조회
Step 7  결과 조합                 → 5섹션 JSON 반환
```

**Evidence Level 체계 확립**
| 레벨 | 소스 | 설명 |
|------|------|------|
| A | 식약처 DrbEasyDrugInfoService | 공식 의약품 라벨 |
| A | DUR API | 병용금기 |
| B | PubMed | 임상 논문 |
| C | Gemini AI | 생성형 AI |

**`MfdsService` 구현** (식약처 e약은요)
- `DrbEasyDrugInfoService` API 연동
- `DrugLabel` 데이터클래스: 효능·부작용·상호작용·이미지 URL
- `get_drug_labels_bulk()`: 병렬 조회
- 캐시: 7일 TTL

**`SimPreService` 구현** (한국전통지식포털 유사처방)
- API: `apis.data.go.kr/1430000/SimPreInfoService/getSimPreSearch`
- XML 응답 파싱
- 처방 코드, 구성 약재, 관련 논문 반환

**FastAPI 앱 구조 확립**
```
app/
├── main.py                  # FastAPI 앱, CORS 설정
├── api/v1/endpoints/
│   └── analysis.py          # Router: /api/v1/analyze/*
├── schemas/
│   └── analysis.py          # Pydantic 스키마
└── services/
    ├── prescription_service.py   # 통합 파이프라인
    ├── mfds_service.py           # 식약처 e약은요
    ├── dur_service.py            # DUR 병용금기
    ├── sim_pre_service.py        # 한국전통 유사처방
    ├── medication_service.py     # PubMed RAG
    ├── analyze_service.py        # 동의보감 분석
    └── pubmed_service.py         # PubMed E-utilities
```

**성능 최적화**
- `CacheManager` 구현 — JSON 파일 기반 캐시
- `drug_validator.py` — 약물명 정규화
- `performance_monitor.py` — 응답 시간 추적
- MFDS + PubMed 동시 병렬 조회 (`asyncio.gather`)

---

## 2026-02-20

### 외부 API 3종 추가 통합

#### 1. 의약품 낱알정보 API (`MdcinGrnIdntfcInfoService03`)

**새 서비스**: `app/services/pill_id_service.py`
- `PillIdService.search_by_name(drug_name)` — 약품명으로 낱알 외형 조회
- `PillIdService.search_by_appearance(shape, color, mark, ...)` — 외형으로 약 식별
- `PillIdService.get_image_url(drug_name)` — 이미지 URL 추출 (MfdsService fallback용)
- 캐시: 이름 검색 7일, 외형 검색 48시간

**`MfdsService` 이미지 보완**
- e약은요 `itemImage` 없을 때 → 낱알정보 API 자동 호출
- `enrich_image=True` 파라미터로 제어

**새 API 엔드포인트**
```
POST /api/v1/analyze/pill-search/name
POST /api/v1/analyze/pill-search/appearance
```

**응답 필드**: `itemSeq`, `itemName`, `chart`(성상), `imageUrl`, `printFront/Back`(각인), `drugShape`, `colorFront/Back`, `lineFront/Back`, `lengLong/Short`, `thick`, `formName`, `className`, `etcOtc`, `ediCode`

---

#### 2. Tavily 웹 검색 API

**새 서비스**: `app/services/tavily_service.py`
- AI agent 최적화 검색 엔진 — 실시간 웹 정보
- `search_drug_info(drug_name)` — 효능·부작용 웹 검색 (신뢰 도메인 우선)
- `search_drug_safety_news(drug_name)` — 최신 안전성 경고·뉴스
- `search_bulk(drug_names)` — 병렬 다중 검색
- 신뢰 도메인 우선: `health.kr`, `drug.mfds.go.kr`, `nhs.uk`, `drugs.com`, `webmd.com`, `medlineplus.gov`
- 캐시: 정보 검색 24시간, 뉴스 12시간

**Evidence Level 체계 갱신**
| 레벨 | 소스 | 설명 |
|------|------|------|
| A | MFDS (식약처 e약은요) | 공식 의약품 라벨 |
| A | DUR API | 병용금기 |
| B | PubMed | 임상 논문 |
| **C** | **Tavily 웹 검색** | **실시간 웹 — 새로 추가** |
| C | Gemini AI | 생성형 AI (최후 fallback) |

**`PrescriptionService` fallback chain 갱신**
```python
if MFDS 있음:      # Level A → 식약처 라벨 사용
elif PubMed 있음:  # Level B → 논문 기반
elif Tavily 있음:  # Level C → 웹 검색 (NEW)
else:              # 소스 없음
```
- Tavily는 MFDS·PubMed **둘 다 없을 때만** 호출 (불필요한 외부 요청 최소화)

---

#### 3. `.env` 문서화

```env
TAVILY_API_KEY=tvly-dev-...          # Tavily 웹 검색
KOREA_DRUG_API_KEY=...               # 식약처 전체 (MFDS/DUR/낱알/유사처방)
```

---

## 2026-02-22

### 프론트엔드 버그 수정 및 기능 완성

**Tailwind CSS 충돌 해결**
- `index.html`에 Tailwind CDN v3 + v4 PostCSS가 동시 존재 → Hero 텍스트 전체 소멸
- CDN v3 스크립트 제거로 해결 (v4는 CSS 변수 `oklch()` 기반, v3가 덮어씀)

**Kakao Maps CustomOverlay onclick 오류 수정**
- `overlay.getContent()` 반환값이 DOM 엘리먼트가 아닌 **원본 문자열** → `TypeError: Cannot create property 'onclick' on string`
- `document.createElement('div')` 로 DOM 엘리먼트 직접 생성 → onclick 설정 후 `content:` 에 전달

**Google GenAI 임포트 누락 수정**
- `GoogleGenAI`, `Modality` 임포트 누락으로 AI TTS 버튼 동작 불가 → 임포트 추가

**약국 영업시간 링크 추가**
- Kakao Maps SDK / 네이버 API 모두 영업시간 데이터 미제공
- `place_url` 필드 캡처 → "🕐 영업시간 확인" 링크로 Kakao Maps 상세 페이지 연결
- 거리(`distance`) 뱃지 함께 표시

**지도 탭 재진입 버그 수정**
- 다른 탭 → 약국 탭 복귀 시 지도 DOM 언마운트·리마운트 → stale ref로 초기화 스킵
- `naverMapRef.current = null` 강제 리셋 후 150ms delay로 재초기화

**건강 리포트 탭 구현**
- 6개 섹션: 한눈에 보기 / TOP 5 약물 / 타임라인 / 증상 패턴 / 자주 등장 식재료 / 레시피
- 추가 state 없이 IIFE 패턴으로 처방 이력 인라인 집계

---

## 현재 서비스 아키텍처

```
처방전 이미지 (jpg/png)
       │
       ▼
 [Gemini Vision OCR]
       │ drugList
       ▼
 [DUR API] ─────────────────────────────► 병용금기 경고
       │
       ▼
 ┌─────────────────────────────────────────┐
 │  Level A: 식약처 MfdsService            │
 │           ↳ 이미지 없으면 낱알정보 API  │
 ├─────────────────────────────────────────┤
 │  Level B: PubMed RAG (MedicationSvc)    │
 ├─────────────────────────────────────────┤
 │  Level C: Tavily 웹 검색 (NEW)          │
 └─────────────────────────────────────────┘
       │ drugDetails + all_papers
       ▼
 [AnalyzeService] ──── 동의보감/TKM 매핑
 [SimPreService] ───── 유사처방 조회
       │
       ▼
 5섹션 리포트 반환
 ├─ prescriptionSummary (drugList + warnings)
 ├─ drugDetails (효능 + 부작용)
 ├─ academicEvidence (trustLevel + papers)
 ├─ lifestyleGuide (식생활 조언)
 └─ donguibogam (식재료 + 전통처방)
```

---

## 통합 외부 API 목록

| API | 용도 | 키 변수 |
|-----|------|---------|
| Gemini 2.0 Flash | OCR·생성 | `API_KEY` |
| Naver Clova OCR | 처방전 OCR | `NAVER_OCR_*` |
| PubMed E-utilities | 임상 논문 | `PUBMED_API_KEY` |
| 식약처 DrbEasyDrugInfoService | 약물 라벨 (Level A) | `KOREA_DRUG_API_KEY` |
| 식약처 MdcinGrnIdntfcInfoService03 | 낱알 외형 식별 | `KOREA_DRUG_API_KEY` |
| DUR 병용금기 API (OdCloud) | 병용금기 | `KOREA_DRUG_API_KEY` |
| 한국전통지식포털 SimPreInfoService | 유사처방 | `KOREA_DRUG_API_KEY` |
| Tavily Search | 웹 검색 fallback | `TAVILY_API_KEY` |
| Supabase | DB + Auth | `SUPABASE_*` |
| OpenAI | (예비) | `OPENAI_API_KEY` |
| YouTube Data v3 | 영상 콘텐츠 | `YOUTUBE_API_KEY` |
