# 🎯 AI 모델 최적화 실행 가이드 (Quick Start)

**작성일**: 2026-02-09  
**대상**: 개발팀  
**목표**: 응답속도 50% 개선 + 비용 24% 절감 (2시간 작업)

---

## 📋 최적화 전후 비교

| 항목 | 현재 | 개선 후 | 개선율 |
|:---|:---|:---|:---|
| **전체 응답시간** | 50-60초 | 25-30초 | **50% ↓** |
| **약물조회 시간** | 3.8초 | 0.1초 | **97% ↓** |
| **월 API 비용** | $1.87 | $1.42 | **24% ↓** |
| **Fallback 비율** | 10% | 3% | **70% ↓** |
| **사용자 경험** | 불만족 | 만족 | **개선** ✅ |

---

## 🔧 Action Items (우선순위)

### [우선1️⃣] 약물 정보 조회 최적화 (2시간) ⭐ 필수

#### 현재 문제
```typescript
// ❌ 비효율: Gemini 1.5 호출 (3.8초 + 비용)
const model = ai.getGenerativeModel({ model: "gemini-1.5-flash" });
const response = await model.generateContent("약물 정보 조회...");
```

#### 해결책
```typescript
// ✅ 효율: JSON 파일 직접 로드 (0.1초 + 무료)
import { get_drugs_info_list } from '@backend/utils/drug_info_loader';

const medicationsInfo = await fetch('/api/drugs-info', {
  method: 'POST',
  body: JSON.stringify({ drug_names: medications })
});
```

#### 적용 방법

**Step 1: 백엔드 약물 조회 엔드포인트 추가**
```python
# app/services/server.py에 추가

@app.post("/api/drugs-info")
async def get_drugs_info(request: dict):
    """약물 정보 조회 API"""
    drug_names = request.get("drug_names", [])
    from app.utils.drug_info_loader import get_drugs_info_list
    return {"medications": get_drugs_info_list(drug_names)}
```

**Step 2: 프론트엔드 수정**
```typescript
// app/healthstack/index.tsx 수정

// 약물 정보 조회
if (backendResult?.medications && backendResult.medications.length > 0) {
  // 이미 API에서 약물정보를 받아옴 (server.py 수정으로 자동 적용)
}
```

**상태**: ✅ 이미 `server.py`에 적용됨 (확인 필요)

---

### [우선2️⃣] JSON 파싱 강화 (1시간) 🟡 권장

#### 현재 문제
```
Gemini 2.0 → "```json {...}" 형태 → 파싱 실패 → GPT-4 호출
```

#### 해결책
```python
# app/services/analyze_service.py 수정

# Gemini 호출 전 프롬프트 개선
prompt = f"""
{ANALYSIS_PROMPT}

⚠️ 중요: 응답은 반드시 아래 형식의 JSON만 포함하세요.
마크로(```, ```)는 절대 사용하지 마세요.

{{
  "symptom_summary": "...",
  "ingredients": [...],
  "recipes": [...]
}}
"""

# 응답 처리
try:
    text = response.text.strip()
    # ``` 마크로 제거 (혹시모를 상황)
    text = text.replace("```json", "").replace("```", "").strip()
    data = json.loads(text)
except json.JSONDecodeError:
    # Fallback으로 진행
    ...
```

**적용 파일**: `app/services/analyze_service.py` (라인 348-367 근처)

---

### [우선3️⃣] 캐시 히트율 개선 (3시간) 🟢 선택

#### 개선 전략
```python
# app/utils/cache_manager.py 강화

from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class CacheManager:
    def get_with_similarity(self, query: str, threshold=0.85):
        """유사도 기반 캐시 조회"""
        for cached_query, result in self.cache.items():
            # 유사도 계산 (0~1 사이)
            similarity = self._calculate_similarity(query, cached_query)
            if similarity > threshold:
                print(f"캐시 히트! 유사도: {similarity:.2%}")
                return result
        return None
    
    def _calculate_similarity(self, text1: str, text2: str):
        # 간단한 구현: 단어 겹침 비율
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0
```

**예상 효과**: 캐시 히트율 30% → 60%

---

## 📊 효과 측정 방법

### 적용 전 기준선 설정
```bash
# 현재 상태 기록
응답시간: 50-60초
비용: $1.87/월
Fallback: 10%
```

### 적용 후 측정
```python
# app/services/analyze_service.py에 모니터링 추가

import time
from datetime import datetime

class PerformanceMonitor:
    stats = {
        'total_requests': 0,
        'gemini_success': 0,
        'gemini_1_5_used': 0,
        'openai_fallback': 0,
        'cache_hit': 0,
        'total_latency': 0,
        'drug_lookup_time': 0
    }
    
    @staticmethod
    def record_request(latency, success, fallback_used, cache_hit):
        PerformanceMonitor.stats['total_requests'] += 1
        PerformanceMonitor.stats['total_latency'] += latency
        if success:
            PerformanceMonitor.stats['gemini_success'] += 1
        if fallback_used:
            PerformanceMonitor.stats['openai_fallback'] += 1
        if cache_hit:
            PerformanceMonitor.stats['cache_hit'] += 1
    
    @staticmethod
    def get_report():
        stats = PerformanceMonitor.stats
        total = stats['total_requests']
        return {
            'avg_latency': stats['total_latency'] / total if total > 0 else 0,
            'success_rate': stats['gemini_success'] / total * 100 if total > 0 else 0,
            'cache_hit_rate': stats['cache_hit'] / total * 100 if total > 0 else 0,
            'fallback_rate': stats['openai_fallback'] / total * 100 if total > 0 else 0
        }
```

### 주간 보고 템플릿
```
📊 주간 성능 보고 (2026-02-09 ~ 2026-02-15)

평균 응답시간:   50초 → __초   (목표: 25초)
캐시 히트율:     30% → ___%   (목표: 60%)
Fallback 비율:   10% → ___%   (목표: 3%)
월예상비용:      $1.87 → $___  (목표: $1.42)

✅ 개선 사항:
❌ 미개선 사항:
🔧 다음 주 계획:
```

---

## 🚨 주의사항

### ⚠️ 변경 전 필독

1. **테스트 환경에서 먼저 검증**
   ```bash
   # 현재 테스트 파일 실행
   python test_backend_api.py
   python test_ocr_extraction.py
   ```

2. **API 키 확인**
   - `OPENAI_API_KEY` 설정 확인
   - `API_KEY` (Gemini) 설정 확인

3. **롤백 계획 수립**
   ```bash
   git branch -b feature/model-optimization
   git commit -m "optimize: AI model selection and caching"
   # 테스트 후 merge
   ```

### 🔄 CI/CD 체크

```python
# 변경 후 자동화 검사
def test_model_optimization():
    # 1. 약물 조회 성능
    start = time.time()
    drugs = get_drugs_info_list(['Tylenol', '넥세라정'])
    elapsed = time.time() - start
    assert elapsed < 0.5, f"약물조회 너무 느림: {elapsed}s"
    
    # 2. API 응답 포맷
    response = analyze_symptom_sync("감기")
    assert 'ingredients' in response, "응답 포맷 오류"
    
    # 3. Fallback 작동
    # Gemini API 키 잠시 비활성화 후 테스트
```

---

## 📅 실행 일정

```
월(09일): 
  - 보고서 작성 ✅ 
  - 변경 계획 수립

화(10일):
  - Step 1: 약물정보 최적화 (2시간)
  - 단위테스트 (1시간)
  
수(11일):
  - Step 2: JSON 포맷 강화 (1시간)
  - 통합테스트 (1시간)

목(12일):
  - Step 3: 캐시 개선 (선택, 3시간)
  - 성능 모니터링 설정

금(13일):
  - 성능 측정 및 보고
  - 프로덕션 배포 검토
```

---

## 📈 성공 기준

| 기준 | 현재 | 목표 | 달성시 |
|:---|:---|:---|:---|
| 평균 응답시간 | 50s | <30s | ✅ |
| 약물조회 | 3.8s | <0.5s | ✅ |
| 월 비용 | $1.87 | <$1.50 | ✅ |
| Fallback | 10% | <5% | ✅ |
| 캐시 히트 | 30% | >50% | ✅ |

---

## 📞 문의 및 지원

- 기술적 상세: `docs/AI_MODEL_OPTIMIZATION_REPORT.md` 참조
- 코드 구현: `app/services/analyze_service.py`
- 약물DB: `app/utils/drug_info_loader.py`

---

## ✅ 체크리스트

### Pre-Implementation
- [ ] 현재 성능 기준선 기록
- [ ] Git 브랜치 생성
- [ ] 팀 공지

### Implementation
- [ ] 약물 조회 최적화
- [ ] JSON 파싱 강화
- [ ] 캐시 개선 (선택)

### Testing
- [ ] 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 성능 벤치마크

### Deployment
- [ ] 스테이징 배포
- [ ] 모니터링 설정
- [ ] 프로덕션 배포

### Post-Deployment
- [ ] 성능 지표 수집
- [ ] 사용자 피드백
- [ ] 후속 최적화 계획

