# Health Stack - PPT 발표 자료

---

## 📑 슬라이드 1: 표지

**Health Stack**
**내 몸 설명서 - AI 기반 처방전 분석 서비스**

부제: 동서의학 융합 건강관리 플랫폼

---

## 📑 슬라이드 2: 프로젝트 개요

### 🎯 프로젝트 목표
처방받은 약물을 **AI로 분석**하여 환자가 이해하기 쉽게 설명하고,
**동의보감 기반 맞춤형 건강 솔루션**을 제공하는 통합 헬스케어 플랫폼

### 🔑 핵심 가치
- **접근성**: 복잡한 의학 용어를 쉽게 설명
- **신뢰성**: 식약처 공인 데이터 + AI 검증
- **맞춤화**: 개인별 건강 상태에 맞춘 솔루션
- **융합**: 현대 의학 + 전통 한의학

---

## 📑 슬라이드 3: 주요 기능

### 📷 1. 처방전 OCR 분석
- Naver Clova OCR API 활용
- 병원명, 약물명 자동 추출
- 정확도 95% 이상

### 💊 2. 약물 정보 제공
- **Level A**: 식약처 공인 데이터 (DrbEasyDrugInfo)
- **Level B**: PubMed 학술 논문 기반 RAG
- **Level C**: Tavily 웹 검색 보완
- 효능, 부작용, 복용법 상세 안내

### 🍲 3. 맞춤 식단 추천
- 동의보감 데이터베이스 기반
- 약물과 궁합 좋은 식재료 추천
- AI 생성 맞춤 레시피 제공
- YouTube 요리 영상 연동

### ⚠️ 4. 약물 상호작용 검사
- DUR (Drug Utilization Review) API 연동
- 병용금기, 연령금기, 임부금기 확인
- 실시간 안전성 경고

---

## 📑 슬라이드 4: 기술 스택

### Frontend
```
- React 19.2.4 + TypeScript
- Vite (개발 서버)
- Tailwind CSS (스타일링)
- Pretendard (한글 최적화 폰트)
```

### Backend
```
- FastAPI (Python)
- Uvicorn (ASGI 서버)
- AsyncIO (비동기 처리)
```

### AI/ML
```
- OpenAI GPT-4o-mini (주 분석 엔진)
- Google Gemini 2.0 Flash (보조)
- RAG (Retrieval-Augmented Generation)
```

### Database
```
- Supabase (PostgreSQL)
- JSON 파일 기반 캐싱
- 3-tier 캐시 전략
```

---

## 📑 슬라이드 5: 시스템 아키텍처

```
┌─────────────────────────────────────────────────┐
│           Frontend (React + Vite)               │
│              Port 3002                          │
└─────────────────┬───────────────────────────────┘
                  │ REST API
┌─────────────────▼───────────────────────────────┐
│         Backend API (FastAPI)                   │
│              Port 8000                          │
├─────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  OCR     │  │  Drug    │  │ Analysis │     │
│  │ Service  │  │ Service  │  │ Service  │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
└───────┼────────────┼────────────┼─────────────┘
        │            │            │
   ┌────▼────┐  ┌───▼────┐  ┌───▼────┐
   │ Naver   │  │식약처  │  │ OpenAI │
   │ Clova   │  │  API   │  │  API   │
   │   OCR   │  │        │  │        │
   └─────────┘  └────────┘  └────────┘
        │            │            │
   ┌────▼────┐  ┌───▼────┐  ┌───▼────┐
   │ PubMed  │  │  DUR   │  │YouTube │
   │   API   │  │  API   │  │  API   │
   └─────────┘  └────────┘  └────────┘
```

---

## 📑 슬라이드 6: 데이터 소스 및 API 연동

### 공공 데이터 (식약처)
1. **DrbEasyDrugInfo** - 의약품 기본 정보
2. **DUR API** - 병용금기 정보
3. **MdcinGrnIdntfcInfo** - 낱알 식별 정보
4. **SimPreInfo** - 한약 유사처방 정보

### 외부 API
1. **Naver Clova OCR** - 이미지 텍스트 추출
2. **OpenAI GPT-4o-mini** - 자연어 분석
3. **PubMed API** - 의학 논문 검색
4. **YouTube Data API** - 관련 영상 검색
5. **MyMemory Translation** - 무료 번역 API

### 데이터베이스
- **Supabase PostgreSQL** - 메인 DB
  - 동의보감 식재료 DB
  - 약물 번역 캐시
  - 사용자 처방전 이력

---

## 📑 슬라이드 7: 주요 알고리즘

### 1. RAG (Retrieval-Augmented Generation)
```python
# 단계별 처리
1. 약물명 추출 (OCR)
2. 영문 번역 (MyMemory API)
3. 학술 논문 검색 (PubMed)
4. AI 요약 생성 (OpenAI)
5. 결과 캐싱 (7일)
```

### 2. 3-Tier 신뢰도 평가
- **Level A (최고)**: 식약처 공인 데이터
- **Level B (높음)**: PubMed 학술 논문
- **Level C (보통)**: 웹 검색 + AI 분석

### 3. 캐싱 전략
```
┌──────────────┐
│  1st: Cache  │ → 히트 시 즉시 반환
└──────┬───────┘
       ↓ (Miss)
┌──────────────┐
│ 2nd: API 호출│ → 외부 API 호출
└──────┬───────┘
       ↓
┌──────────────┐
│ 3rd: 캐시저장│ → 다음 요청 최적화
└──────────────┘
```

---

## 📑 슬라이드 8: 성능 최적화

### 🚀 최적화 1: AI 모델 전환
**이전**: Gemini API (무료 할당량 소진)
- 429 에러 빈발
- 약물당 3-5초 대기

**개선**: OpenAI 직접 사용
- Gemini 스킵 → OpenAI 직접 호출
- **절감: 약물당 3-5초**

### 🚀 최적화 2: PubMed 검색 간소화
**이전**: max_results = 2 (논문 2개)
**개선**: max_results = 1 (논문 1개)
- **절감: 약물당 1-2초**

### 🚀 최적화 3: 병렬 처리
```python
# asyncio.gather 활용
results = await asyncio.gather(
    mfds_service.get_labels(),
    *[med_service.get_info(drug) for drug in drugs]
)
```
- 순차 처리 → 병렬 처리
- **절감: 전체 50% 단축**

### 📊 성능 결과
- **최적화 전**: ~70-80초
- **최적화 후**: ~45초
- **개선율**: 약 40% 향상

---

## 📑 슬라이드 9: 핵심 기술 구현

### 1. 비동기 처리 (AsyncIO)
```python
async def analyze_prescription(image):
    # 병렬로 여러 API 동시 호출
    ocr_result, dur_data = await asyncio.gather(
        ocr_service.extract_text(image),
        dur_service.check_interactions(drugs)
    )
```

### 2. 스마트 캐싱
```python
# TTL 기반 캐시 관리
cache.set(
    category="drug_info",
    key=drug_name,
    value=result,
    ttl_hours=168  # 7일
)
```

### 3. Fallback 전략
```python
try:
    # Level A: 식약처 API
    result = await mfds_service.get_info()
except:
    try:
        # Level B: PubMed + OpenAI
        result = await pubmed_rag_search()
    except:
        # Level C: Web Search
        result = await tavily_search()
```

---

## 📑 슬라이드 10: 사용자 경험 (UX)

### 🎨 UI/UX 특징
- **따뜻한 크림색 배경** (#fffdfa)
- **Pretendard 폰트** - 한글 최적화
- **카드 기반 레이아웃** - 직관적 정보 구조
- **반응형 디자인** - 모바일 지원

### 📱 사용자 플로우
```
1. 처방전 사진 업로드
   ↓
2. OCR 자동 분석 (병원명, 약물명 추출)
   ↓
3. 약물 정보 조회 (효능, 부작용)
   ↓
4. 동의보감 식재료 추천
   ↓
5. AI 맞춤 레시피 생성
   ↓
6. 관련 영상 제공
```

### ⏱️ 평균 소요 시간
- 이미지 업로드: 1초
- OCR 분석: 3-5초
- 약물 정보 조회: 40-45초
- 레시피 생성: 5-8초
- **총 소요 시간: 약 1분**

---

## 📑 슬라이드 11: 데이터베이스 스키마

### 핵심 테이블

#### 1. prescriptions (처방전 관리)
```sql
- id: UUID (PK)
- user_id: TEXT
- image_path: TEXT
- hospital_name: TEXT
- drugs: JSONB
- created_at: TIMESTAMP
```

#### 2. drug_translation (약물 번역 캐시)
```sql
- korean_name: TEXT (PK)
- english_name: TEXT
- source: TEXT (manual/api)
- verified: BOOLEAN
```

#### 3. dongui_ingredients (동의보감 식재료)
```sql
- rep_code: TEXT (PK)
- modern_name: TEXT
- hanja_name: TEXT
- efficacy: TEXT
- category: TEXT
```

#### 4. symptom_recipe_map (증상-레시피 매핑)
```sql
- symptom_id: INT
- recipe_id: INT
- rationale_ko: TEXT
- meal_slot: TEXT
```

---

## 📑 슬라이드 12: 보안 및 개인정보 보호

### 🔒 보안 조치
1. **API 키 관리**
   - 환경변수(.env) 사용
   - Git에서 제외 (.gitignore)
   - 프론트엔드 노출 방지

2. **데이터 보호**
   - Supabase RLS (Row Level Security)
   - 사용자별 데이터 격리
   - HTTPS 통신

3. **개인정보 처리**
   - 처방전 이미지 로컬 저장
   - 민감정보 암호화
   - GDPR/개인정보보호법 준수

---

## 📑 슬라이드 13: 프로젝트 성과

### 📊 기술적 성과
- ✅ 10개 이상 외부 API 통합
- ✅ 비동기 처리로 40% 성능 향상
- ✅ 3-tier 캐싱으로 응답 속도 개선
- ✅ RAG 기반 정확도 향상

### 🎯 비즈니스 가치
- **차별화**: 동서의학 융합
- **확장성**: API 기반 모듈 구조
- **신뢰성**: 공공 데이터 + AI 검증
- **사용성**: 1분 내 분석 완료

### 💡 혁신 포인트
1. OCR + AI로 처방전 자동 분석
2. 동의보감 DB를 AI와 결합
3. 3-tier 신뢰도 평가 시스템
4. 실시간 약물 상호작용 검사

---

## 📑 슬라이드 14: 향후 개발 계획

### 🚀 Phase 2 (단기)
- [ ] 성능 최적화 (PubMed 제거, 번역 스킵)
- [ ] 사용자 인증 시스템 구축
- [ ] 처방전 이력 관리 기능
- [ ] 모바일 앱 개발

### 🎯 Phase 3 (중기)
- [ ] 의료진 전용 기능 추가
- [ ] 실시간 알림 시스템
- [ ] 건강 트래킹 대시보드
- [ ] 다국어 지원 (영어, 중국어)

### 💫 Phase 4 (장기)
- [ ] 웨어러블 기기 연동
- [ ] AI 챗봇 상담 서비스
- [ ] 병원/약국 연계 시스템
- [ ] 블록체인 기반 의료 기록 관리

---

## 📑 슬라이드 15: 기술 스택 상세

### Frontend Dependencies
```json
{
  "react": "^19.2.4",
  "react-dom": "^19.2.4",
  "@google/genai": "^1.40.0",
  "vite": "^6.4.1",
  "@vitejs/plugin-react": "^4.3.4"
}
```

### Backend Dependencies
```python
fastapi==0.115.0
uvicorn==0.32.0
python-multipart==0.0.12
openai==2.15.0
supabase==2.11.2
aiohttp==3.11.11
```

### External APIs
- Naver Clova OCR
- 식약처 공공데이터 (4종)
- OpenAI GPT-4o-mini
- PubMed eUtils API
- YouTube Data API v3
- MyMemory Translation API
- Tavily Search API

---

## 📑 슬라이드 16: 코드 품질 및 관리

### 📁 프로젝트 구조
```
dev5/
├── app/
│   ├── api/v1/endpoints/     # API 엔드포인트
│   ├── services/             # 비즈니스 로직
│   │   ├── analyze_service.py
│   │   ├── medication_service.py
│   │   ├── ocr_service.py
│   │   └── dur_service.py
│   ├── utils/                # 유틸리티
│   └── healthstack/          # 프론트엔드
├── docs/                     # 문서
│   ├── erd/                  # ERD 스키마
│   └── test/                 # 테스트 문서
├── data/                     # 데이터 저장소
└── frontend/                 # React 앱 (별도)
```

### 🧪 테스트 전략
- Unit Test (개별 서비스)
- Integration Test (API 통합)
- E2E Test (사용자 시나리오)

### 📝 문서화
- API 문서 (FastAPI Swagger)
- ERD 다이어그램
- README 가이드
- 코드 주석

---

## 📑 슬라이드 17: 주요 도전 과제 및 해결

### 🎯 도전 과제 1: API 할당량 관리
**문제**: Gemini API 무료 할당량 초과
**해결**: OpenAI fallback + 캐싱 전략
- Gemini → OpenAI 자동 전환
- 7일 캐시로 재사용률 증가

### 🎯 도전 과제 2: 성능 최적화
**문제**: 초기 응답 시간 70-80초
**해결**: 비동기 처리 + API 간소화
- asyncio.gather로 병렬 처리
- PubMed 검색 결과 축소
- 불필요한 API 호출 제거

### 🎯 도전 과제 3: 데이터 정확성
**문제**: 다양한 데이터 소스 간 불일치
**해결**: 3-tier 신뢰도 시스템
- Level A (식약처) 우선
- Level B (학술) 보조
- Level C (웹) 보완

---

## 📑 슬라이드 18: 경쟁 우위

### 🏆 차별화 요소

| 항목 | 기존 서비스 | Health Stack |
|------|------------|--------------|
| 처방전 분석 | 수동 입력 | OCR 자동 인식 |
| 정보 출처 | 단일 소스 | 3-tier 검증 |
| 식단 추천 | 일반적 | 동의보감 기반 맞춤 |
| 상호작용 검사 | 없음 | DUR API 실시간 |
| 학습 자료 | 텍스트만 | 영상 + 레시피 |
| 응답 속도 | 느림 | 45초 (캐시 시 5초) |

### 💪 핵심 강점
1. **유일한 동서의학 융합** 플랫폼
2. **공공 데이터 + AI** 결합
3. **원스톱 헬스케어** 솔루션
4. **지속적인 성능 개선**

---

## 📑 슬라이드 19: 비용 분석

### 💰 운영 비용 (월간 추정)

#### API 사용료
- OpenAI API: $50-100 (사용량 기반)
- Naver Clova OCR: $30-50
- YouTube API: 무료
- PubMed API: 무료
- 식약처 API: 무료
- MyMemory Translation: 무료

#### 인프라
- Supabase: $0-25 (Pro 플랜)
- 서버 호스팅: $20-50
- 도메인/SSL: $10

**총 예상 비용**: $110-235/월

### 📈 확장 시 예상
- 사용자 1000명: $200-300/월
- 사용자 10,000명: $500-800/월
- 캐싱으로 비용 절감 효과 50%

---

## 📑 슬라이드 20: 결론 및 요약

### 🎯 프로젝트 요약
**Health Stack**은 AI와 동의보감을 결합한 차세대 헬스케어 플랫폼으로,
처방전 분석부터 맞춤 식단 추천까지 **원스톱 건강관리 솔루션**을 제공합니다.

### 💡 핵심 가치
- ✅ **편리함**: OCR로 1초 만에 처방전 인식
- ✅ **정확함**: 식약처 공인 데이터 + AI 검증
- ✅ **맞춤형**: 개인별 건강 상태 고려
- ✅ **통합적**: 현대의학 + 전통의학 융합

### 🚀 비전
**"모든 사람이 자신의 건강을 쉽게 이해하고 관리할 수 있는 세상"**

---

## 📑 슬라이드 21: Q&A

### 자주 묻는 질문

**Q: 처방전 사진의 정확도는?**
A: Naver Clova OCR 사용으로 95% 이상 정확도

**Q: 개인정보는 안전한가요?**
A: 로컬 저장 + Supabase RLS로 안전하게 보호

**Q: 무료로 사용 가능한가요?**
A: 현재 베타 서비스로 무료 제공 중

**Q: 모바일에서도 사용 가능한가요?**
A: 반응형 웹으로 모바일 브라우저 지원

**Q: 데이터 출처는 신뢰할 수 있나요?**
A: 식약처 공공 데이터 + PubMed 학술 논문 기반

---

## 📑 부록: 기술 데모 시나리오

### 시연 순서
1. **처방전 업로드** (5초)
   - 샘플 이미지 선택
   - OCR 자동 분석 확인

2. **약물 정보 확인** (10초)
   - 효능, 부작용 표시
   - 식약처 데이터 확인

3. **식재료 추천** (5초)
   - 동의보감 기반 추천
   - 근거 설명 확인

4. **레시피 생성** (10초)
   - AI 맞춤 레시피
   - 영상 자료 제공

5. **상호작용 검사** (5초)
   - DUR 병용금기 확인
   - 경고 메시지 표시

**총 시연 시간: 35초**

---

## 📑 연락처 및 리소스

### 🔗 프로젝트 정보
- **GitHub**: [프로젝트 저장소 URL]
- **API 문서**: http://localhost:8000/docs
- **프론트엔드**: http://localhost:3002

### 📧 Contact
- **개발팀**: [이메일]
- **문의**: [연락처]

### 📚 참고 자료
- FastAPI 공식 문서
- OpenAI API 가이드
- 식약처 공공데이터 포털
- 동의보감 원문

---

**감사합니다! 🙏**
