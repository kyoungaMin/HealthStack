# Embedding and Search Design

## Overview

본 문서는 babiyagida 프로젝트의 임베딩 생성 및 검색 설계를 정리합니다.

---

## 1. Embedding Pipeline

### 1.1 실행 방법

```bash
cd database

# 특정 content_type만 처리
python embed_pipeline.py --source-table traditional_foods --content-type indication --limit 1000

# 모든 content_type 처리
python embed_pipeline.py --source-table traditional_foods --content-type all --batch-size 100

# 중단 후 재개
python embed_pipeline.py --source-table traditional_foods --content-type indication --resume

# 통계 확인
python embed_pipeline.py --stats
```

### 1.2 Content Type 표준

| content_type | 설명 | 예시 |
|--------------|------|------|
| `indication` | 효능/적응증 요약 | "기를 아주 잘 내린다 (증상: 소화불량)" |
| `food_entity` | 음식 엔티티 | "음식: 곰국\n분류: 식재료명\n재료: 무, 소고기" |
| `prescription_entity` | 처방 엔티티 | "처방: 六味地黃湯\n현대명: 육미지황탕" |
| `ingredients_core` | 대표 재료 1~5개 | "무, 감초, 대추" |

### 1.3 Content 정규화 규칙

1. **한문 원문 제거**: 中文字 → 삭제
2. **동의어 정리**: `[蘿葍,나복,무]` → `무`
3. **중복 제거**: 동일 재료 하나만 유지
4. **길이 제한**: indication 100자, ingredients 5개
5. **빈값 제거**: 공백/null 필드 스킵

**Before (raw)**:
```
적응증: 기를 아주 잘 내린다./大下氣.
재료: [蘿葍,나복,나복근,무,라복,蘿葍辛而又甘...]
```

**After (normalized)**:
```
indication: 기를 아주 잘 내린다.
ingredients_core: 무
```

---

## 2. 캐시 구조

### 2.1 캐시 키

```
(content_hash, model) = UNIQUE
```

- `content_hash`: SHA256(normalized_content)
- `model`: text-embedding-3-small

### 2.2 캐시 유니크 인덱스

```sql
-- 이 인덱스가 없으면 생성 필요
CREATE UNIQUE INDEX IF NOT EXISTS uq_embeddings_content_hash_model 
ON public.embeddings(content_hash, model);
```

### 2.3 처리 흐름

```
1. row → build_content(row, content_type) → normalized text
2. content_hash = SHA256(text)
3. SELECT FROM embeddings WHERE content_hash = ? AND model = ?
   → 존재하면 SKIP (cache hit)
   → 없으면 OpenAI 호출 → INSERT
4. source_table/source_id/content_type 매핑 저장
```

---

## 3. Checkpoint 재개

### 3.1 Checkpoint 파일

```
checkpoints/
├── traditional_foods_indication.json
├── traditional_foods_food_entity.json
├── traditional_foods_prescription_entity.json
└── traditional_foods_ingredients_core.json
```

### 3.2 Checkpoint 형식

```json
{
  "last_source_id": 12345,
  "updated_at": "2026-01-23T15:30:00"
}
```

### 3.3 재개 사용법

```bash
# 중단된 지점부터 재개
python embed_pipeline.py --source-table traditional_foods --content-type indication --resume
```

---

## 4. 모니터링 SQL 쿼리

### 4.1 전체 임베딩 수

```sql
SELECT COUNT(*) 
FROM public.embeddings 
WHERE embedding IS NOT NULL;
```

### 4.2 content_type별 분포

```sql
SELECT content_type, COUNT(*) 
FROM public.embeddings 
WHERE embedding IS NOT NULL 
GROUP BY content_type 
ORDER BY COUNT(*) DESC;
```

### 4.3 캐시 효율성 (중복 비율)

```sql
SELECT 
  COUNT(DISTINCT content_hash) as unique_hashes,
  COUNT(*) as total_rows,
  ROUND(COUNT(DISTINCT content_hash)::numeric / COUNT(*) * 100, 2) as unique_pct
FROM public.embeddings;
```

### 4.4 토큰 사용량 통계

```sql
SELECT 
  content_type,
  COUNT(*) as count,
  SUM(tokens_used) as total_tokens,
  ROUND(AVG(tokens_used), 1) as avg_tokens
FROM public.embeddings
WHERE embedding IS NOT NULL
GROUP BY content_type;
```

### 4.5 최근 임베딩 작업

```sql
SELECT 
  DATE(created_at) as date,
  content_type,
  COUNT(*) as count,
  SUM(tokens_used) as tokens
FROM public.embeddings
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at), content_type
ORDER BY date DESC, count DESC;
```

---

## 5. 비용 추정

### 5.1 모델 비용

- **text-embedding-3-small**: $0.00002 / 1K tokens

### 5.2 예상 비용 (traditional_foods 32만건)

| 시나리오 | Unique 예상 | 토큰 예상 | 비용 |
|----------|------------|----------|------|
| Row 전체 임베딩 (금지) | 320,000 | 32M | $0.64 |
| Unique indication | ~10,000 | 500K | $0.01 |
| Unique ingredients | ~8,000 | 200K | $0.004 |
| Unique food_entity | ~5,000 | 250K | $0.005 |
| **Total (최적화)** | **~23,000** | **~1M** | **$0.02** |

---

## 6. 에러 처리

### 6.1 Rate Limit

- 지수 백오프: 1s → 2s → 4s → 8s → 16s
- 최대 5회 재시도

### 6.2 네트워크 오류

- 동일 백오프 적용
- 실패 시 로그 기록 후 계속 진행

### 6.3 체크포인트

- 배치마다 체크포인트 저장
- 중단 후 `--resume`로 이어서 처리

---

## 7. 파일 구조

```
database/
├── embed_pipeline.py      # 메인 임베딩 파이프라인
├── embed_cached.py        # 캐시 기반 파이프라인 (대안)
├── generate_embeddings.py # 레거시 (row 단위, 비추천)
├── checkpoints/           # 체크포인트 저장
│   └── *.json
├── sql/
│   ├── 01_enable_pgvector.sql
│   ├── 02_create_embeddings_table.sql
│   ├── 03_semantic_search_function.sql
│   ├── 04_embedding_cache_migration.sql
│   └── 05_cache_search_functions.sql
└── .env                   # 환경 변수
```

---

## Change History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-23 | 1.0.0 | Initial design |
