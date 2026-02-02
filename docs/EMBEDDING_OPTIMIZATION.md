# Embedding Optimization Design

## Executive Summary

**Problem**: 322,452 rows in `traditional_foods` being embedded individually = high cost  
**Solution**: Unique text embedding cache + row mapping structure  
**Expected Savings**: ~90% token reduction (32만 → ~3만 unique embeddings)

---

## 1. Content Type Set (6 Types)

### 1.1 Overview

| content_type | Source Table | Unique Count (Est.) | Purpose |
|--------------|--------------|---------------------|---------|
| `disease_entity` | disease_master | ~2,000 | Disease/symptom entity |
| `prescription_entity` | prescription_master | ~3,000 | Prescription/recipe entity |
| `food_entity` | foods_master | ~5,000 | Food item entity |
| `indication` | traditional_foods.indication | ~10,000 | Symptom indication text |
| `ingredients_set` | traditional_foods.ingredients | ~8,000 | Ingredient combination |
| `symptom_query` | Runtime | N/A | User query embedding |

### 1.2 Standard Text Templates

#### 1.2.1 `disease_entity`
```
[질병] {disease}
[현대명] {modern_disease}
[별명] {disease_alias}
```

**Example**:
```
[질병] 消渴
[현대명] 당뇨병, 갈증
[별명] 삼다증
```

**Token estimate**: ~20-50 tokens per entity

---

#### 1.2.2 `prescription_entity`
```
[처방] {prescription}
[현대명] {prescription_modern}
[별명] {prescription_alias}
```

**Example**:
```
[처방] 六味地黃湯
[현대명] 육미지황탕
[별명] 지황환
```

**Token estimate**: ~15-40 tokens per entity

---

#### 1.2.3 `food_entity`
```
[음식] {rep_name}
[코드] {rep_code}
```

**Example**:
```
[음식] 결명자차
[코드] FD001
```

**Token estimate**: ~10-20 tokens per entity

---

#### 1.2.4 `indication`
```
[적응증] {indication}
```

**Example**:
```
[적응증] 눈이 침침하고 머리가 무거우며 소변이 잦을 때
```

**Token estimate**: ~30-100 tokens per indication

---

#### 1.2.5 `ingredients_set`
```
[재료] {ingredients_normalized}
```

**Example**:
```
[재료] 결명자, 감초, 대추
```

**Token estimate**: ~20-60 tokens per set

---

#### 1.2.6 `symptom_query` (Runtime Only)
```
[증상] {user_query}
```

**Example**:
```
[증상] 요즘 눈이 피곤하고 잠이 잘 안와요
```

**Note**: Embedded at query time, not pre-computed

---

## 2. Search Flow A: Symptom-based Recommendation

### Goal: User describes symptoms → Get food/prescription recommendations

```
┌─────────────────────────────────────────────────────────────────┐
│                   Symptom → Recommendation Flow                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [User Query]                                                   │
│  "요즘 눈이 피곤하고 잠이 잘 안와요"                             │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────┐                   │
│  │ Step 1: Query Preprocessing (Haiku)     │                   │
│  │ - Extract keywords: ["눈피로", "불면"]   │                   │
│  │ - Normalize: remove stopwords           │                   │
│  └─────────────────────────────────────────┘                   │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────┐                   │
│  │ Step 2: FTS Candidate Retrieval         │                   │
│  │ - Search disease_master.modern_disease  │                   │
│  │ - Search traditional_foods.indication   │                   │
│  │ - Get TOP 100 candidates                │                   │
│  └─────────────────────────────────────────┘                   │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────┐                   │
│  │ Step 3: Vector Reranking                │                   │
│  │ - Embed user query → symptom_query      │                   │
│  │ - Compare with indication embeddings    │                   │
│  │ - Compare with disease_entity embeddings│                   │
│  │ - Cosine similarity scoring             │                   │
│  └─────────────────────────────────────────┘                   │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────┐                   │
│  │ Step 4: Result Expansion                │                   │
│  │ - Join with traditional_foods           │                   │
│  │ - Get prescription, ingredients, dosage │                   │
│  │ - Return TOP 10 recommendations         │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### SQL Pseudocode

```sql
-- Step 2: FTS Candidate Retrieval
WITH fts_candidates AS (
  SELECT tf.id, tf.indication, dm.id as disease_id
  FROM traditional_foods tf
  JOIN disease_master dm ON tf.disease = dm.disease
  WHERE 
    to_tsvector('simple', tf.indication) @@ plainto_tsquery('simple', '눈피로 불면')
    OR to_tsvector('simple', dm.modern_disease) @@ plainto_tsquery('simple', '눈피로 불면')
  LIMIT 100
),

-- Step 3: Vector Reranking
reranked AS (
  SELECT 
    fc.id,
    1 - (e.embedding <=> query_embedding) as similarity
  FROM fts_candidates fc
  JOIN embeddings e ON e.source_id = fc.id 
    AND e.source_table = 'traditional_foods' 
    AND e.content_type = 'indication'
  ORDER BY similarity DESC
  LIMIT 10
)

-- Step 4: Result Expansion
SELECT tf.*, similarity
FROM reranked r
JOIN traditional_foods tf ON tf.id = r.id;
```

---

## 3. Search Flow B: Food/Ingredient Search

### Goal: User searches for specific food/ingredient → Get exact matches + similar items

```
┌─────────────────────────────────────────────────────────────────┐
│                   Food/Ingredient Search Flow                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [User Query]                                                   │
│  "결명자"                                                        │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────┐                   │
│  │ Step 1: Exact Match (FTS)               │                   │
│  │ - Search foods_master.rep_name          │                   │
│  │ - Search traditional_foods.ingredients  │                   │
│  │ - Search prescription_master.prescription│                  │
│  │ - ILIKE '%결명자%' fallback             │                   │
│  └─────────────────────────────────────────┘                   │
│         │                                                       │
│         ├─── Exact matches found ───────────────┐              │
│         │                                       ▼              │
│         │                              [Return exact matches]   │
│         │                                       +              │
│         ▼                              [Similar items below]    │
│  ┌─────────────────────────────────────────┐                   │
│  │ Step 2: Vector Similar Search           │                   │
│  │ - Get embedding of exact match          │                   │
│  │ - OR embed query as food_entity         │                   │
│  │ - Find similar ingredients_set          │                   │
│  │ - Find similar food_entity              │                   │
│  └─────────────────────────────────────────┘                   │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────┐                   │
│  │ Step 3: Result Merge & Rank             │                   │
│  │ - Exact matches: boost score +1.0       │                   │
│  │ - Similar items: vector similarity      │                   │
│  │ - Deduplicate by rep_code               │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### SQL Pseudocode

```sql
-- Step 1: Exact Match
WITH exact_matches AS (
  SELECT tf.id, tf.rep_code, 1.0 as match_score, 'exact' as match_type
  FROM traditional_foods tf
  WHERE 
    tf.ingredients ILIKE '%결명자%'
    OR tf.rep_name ILIKE '%결명자%'
),

-- Step 2: Vector Similar (using embedding of first exact match)
similar_items AS (
  SELECT 
    e2.source_id as id,
    1 - (e1.embedding <=> e2.embedding) as similarity,
    'similar' as match_type
  FROM embeddings e1
  JOIN embeddings e2 ON e2.content_type = 'ingredients_set'
  WHERE e1.source_id = (SELECT id FROM exact_matches LIMIT 1)
    AND e1.content_type = 'ingredients_set'
    AND e2.source_id != e1.source_id
    AND 1 - (e1.embedding <=> e2.embedding) > 0.7
  ORDER BY similarity DESC
  LIMIT 10
)

-- Step 3: Merge
SELECT * FROM exact_matches
UNION ALL
SELECT id, rep_code, similarity, match_type FROM similar_items
WHERE rep_code NOT IN (SELECT rep_code FROM exact_matches);
```

---

## 4. Cost Reduction Priority

### P0 (Critical - Do First)

| Item | Current | Optimized | Savings |
|------|---------|-----------|---------|
| **Unique entity embedding** | 322,452 row embeddings | ~3,000 disease + ~3,000 prescription + ~5,000 food = ~11,000 | **97%** |
| **Hash-based dedup** | No dedup | SHA256 content_hash check | Prevents re-embedding |
| **Batch API calls** | 1 call per row | 100 texts per API call | 100x fewer API calls |

**Implementation**:
```python
# Batch embedding (100 texts at once)
response = openai.embeddings.create(
    model="text-embedding-3-small",
    input=texts_batch  # List of 100 texts
)
```

---

### P1 (High - Do Soon)

| Item | Description | Savings |
|------|-------------|---------|
| **Indication dedup** | Many rows share same indication text | ~70% of 322K → ~10K unique |
| **Ingredients normalization** | "결명자, 감초" == "감초, 결명자" (sort & normalize) | ~50% dedup |
| **Master table priority** | Embed disease_master, prescription_master first | Small tables, high reuse |

**Normalization Example**:
```python
def normalize_ingredients(text: str) -> str:
    items = [x.strip() for x in text.split(',')]
    items = sorted(set(items))  # Sort & dedupe
    return ', '.join(items)
```

---

### P2 (Medium - Optimize Later)

| Item | Description | Savings |
|------|-------------|---------|
| **Template compression** | Remove Korean labels, use delimiters | ~20% token reduction |
| **Embedding dimension** | Use 512-dim instead of 1536 | ~66% storage savings |
| **Lazy embedding** | Only embed on first search hit | Defer cost to runtime |

**Compressed Template**:
```
# Before (verbose)
[질병] 消渴
[현대명] 당뇨병, 갈증
[별명] 삼다증

# After (compressed)
消渴|당뇨병,갈증|삼다증
```

---

## 5. New Table Schema

### 5.1 Mapping Table: `embedding_mappings`

```sql
CREATE TABLE embedding_mappings (
  id BIGSERIAL PRIMARY KEY,
  source_table VARCHAR(50) NOT NULL,     -- 'traditional_foods'
  source_id BIGINT NOT NULL,             -- traditional_foods.id
  embedding_id BIGINT REFERENCES embeddings(id),
  content_type VARCHAR(50) NOT NULL,     -- 'indication', 'ingredients_set'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE(source_table, source_id, content_type)
);

CREATE INDEX idx_em_source ON embedding_mappings(source_table, source_id);
CREATE INDEX idx_em_embedding ON embedding_mappings(embedding_id);
```

### 5.2 Updated Embeddings Table

```sql
-- Add unique constraint on content_hash
ALTER TABLE embeddings ADD CONSTRAINT embeddings_content_hash_unique 
  UNIQUE(content_type, content_hash);

-- This allows: same hash = reuse existing embedding
```

### 5.3 Data Flow

```
[traditional_foods row]
        │
        ├─ indication ────→ [Hash] ─→ embeddings (content_type='indication')
        │                              ↓
        │                    embedding_mappings (source_id → embedding_id)
        │
        ├─ ingredients ───→ [Normalize + Hash] ─→ embeddings (content_type='ingredients_set')
        │                              ↓
        │                    embedding_mappings (source_id → embedding_id)
        │
        └─ disease ───────→ [Lookup disease_master.id] ─→ embeddings (content_type='disease_entity')
```

---

## 6. Migration Steps

### Phase 1: Master Tables (Day 1)
```bash
# ~11,000 embeddings total
python embed_masters.py --table disease_master      # ~2,000
python embed_masters.py --table prescription_master # ~3,000
python embed_masters.py --table foods_master        # ~5,000
```

### Phase 2: Unique Indications (Day 2)
```bash
# Extract unique indications, embed, create mappings
python embed_unique_fields.py --field indication    # ~10,000 unique
```

### Phase 3: Unique Ingredients (Day 3)
```bash
# Normalize & extract unique ingredient sets
python embed_unique_fields.py --field ingredients   # ~8,000 unique
```

### Phase 4: Create Mappings (Day 4)
```bash
# Link all traditional_foods rows to existing embeddings
python create_mappings.py --table traditional_foods
```

---

## 7. Cost Comparison

| Approach | Embeddings | Tokens (Est.) | Cost ($0.00002/1K) |
|----------|------------|---------------|-------------------|
| **Current (row-by-row)** | 322,452 | ~32M | **$0.64** |
| **Optimized (unique)** | ~31,000 | ~3.1M | **$0.06** |
| **Savings** | -291,452 | -29M | **$0.58 (90%)** |

---

## 8. Change History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-24 | Initial design |
