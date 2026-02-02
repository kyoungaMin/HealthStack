-- ============================================
-- babiyagida - Cache-based Search Functions
-- ============================================
-- Purpose: Search functions optimized for embedding cache structure
-- Prerequisite: 04_embedding_cache_migration.sql executed
-- ============================================

-- ============================================
-- FLOW A: Symptom → Recommendation
-- ============================================

-- A.1 Hybrid search: FTS candidates + Vector reranking
CREATE OR REPLACE FUNCTION search_symptom_hybrid(
  p_query TEXT,
  p_query_embedding vector(1536),
  p_fts_limit INT DEFAULT 100,
  p_result_limit INT DEFAULT 10
)
RETURNS TABLE (
  id BIGINT,
  rep_name TEXT,
  disease TEXT,
  modern_disease TEXT,
  indication TEXT,
  prescription_modern TEXT,
  ingredients TEXT,
  dosage TEXT,
  match_type TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH 
  -- Step 1: FTS candidate retrieval
  fts_candidates AS (
    SELECT DISTINCT tf.id
    FROM traditional_foods tf
    LEFT JOIN disease_master dm ON tf.disease = dm.disease
    WHERE 
      tf.indication ILIKE '%' || p_query || '%'
      OR tf.modern_disease ILIKE '%' || p_query || '%'
      OR dm.modern_disease ILIKE '%' || p_query || '%'
      OR dm.disease_alias ILIKE '%' || p_query || '%'
    LIMIT p_fts_limit
  ),
  
  -- Step 2: Get embeddings for candidates via mapping
  candidates_with_embeddings AS (
    SELECT 
      fc.id,
      e.embedding,
      em.content_type
    FROM fts_candidates fc
    JOIN embedding_mappings em ON em.source_table = 'traditional_foods' 
      AND em.source_id = fc.id
      AND em.content_type IN ('indication', 'disease_entity')
    JOIN embeddings e ON e.id = em.embedding_id
  ),
  
  -- Step 3: Vector reranking
  reranked AS (
    SELECT 
      cwe.id,
      MAX(1 - (cwe.embedding <=> p_query_embedding)) as max_similarity
    FROM candidates_with_embeddings cwe
    GROUP BY cwe.id
    ORDER BY max_similarity DESC
    LIMIT p_result_limit
  )
  
  -- Step 4: Join with full data
  SELECT 
    tf.id,
    tf.rep_name,
    tf.disease,
    tf.modern_disease,
    tf.indication,
    tf.prescription_modern,
    tf.ingredients,
    tf.dosage,
    'symptom_match'::TEXT as match_type,
    r.max_similarity::FLOAT as similarity
  FROM reranked r
  JOIN traditional_foods tf ON tf.id = r.id
  ORDER BY r.max_similarity DESC;
END;
$$;

-- A.2 Pure vector search (when no FTS matches)
CREATE OR REPLACE FUNCTION search_symptom_vector(
  p_query_embedding vector(1536),
  p_limit INT DEFAULT 10
)
RETURNS TABLE (
  id BIGINT,
  rep_name TEXT,
  disease TEXT,
  modern_disease TEXT,
  indication TEXT,
  prescription_modern TEXT,
  ingredients TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    tf.id,
    tf.rep_name,
    tf.disease,
    tf.modern_disease,
    tf.indication,
    tf.prescription_modern,
    tf.ingredients,
    (1 - (e.embedding <=> p_query_embedding))::FLOAT as similarity
  FROM embeddings e
  JOIN embedding_mappings em ON em.embedding_id = e.id
  JOIN traditional_foods tf ON tf.id = em.source_id AND em.source_table = 'traditional_foods'
  WHERE e.content_type IN ('indication', 'disease_entity')
  ORDER BY e.embedding <=> p_query_embedding
  LIMIT p_limit;
END;
$$;

-- ============================================
-- FLOW B: Food/Ingredient → Effects
-- ============================================

-- B.1 Exact match + Vector similar
CREATE OR REPLACE FUNCTION search_food_hybrid(
  p_query TEXT,
  p_query_embedding vector(1536) DEFAULT NULL,
  p_exact_limit INT DEFAULT 20,
  p_similar_limit INT DEFAULT 10,
  p_similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
  id BIGINT,
  rep_code TEXT,
  rep_name TEXT,
  indication TEXT,
  ingredients TEXT,
  preparation TEXT,
  match_type TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH 
  -- Step 1: Exact matches
  exact_matches AS (
    SELECT DISTINCT
      tf.id,
      tf.rep_code,
      tf.rep_name,
      tf.indication,
      tf.ingredients,
      tf.preparation,
      'exact'::TEXT as match_type,
      1.0::FLOAT as similarity
    FROM traditional_foods tf
    WHERE 
      tf.rep_name ILIKE '%' || p_query || '%'
      OR tf.ingredients ILIKE '%' || p_query || '%'
      OR tf.prescription ILIKE '%' || p_query || '%'
    LIMIT p_exact_limit
  ),
  
  -- Step 2: Vector similar (only if embedding provided)
  similar_items AS (
    SELECT 
      tf.id,
      tf.rep_code,
      tf.rep_name,
      tf.indication,
      tf.ingredients,
      tf.preparation,
      'similar'::TEXT as match_type,
      (1 - (e.embedding <=> p_query_embedding))::FLOAT as similarity
    FROM embeddings e
    JOIN embedding_mappings em ON em.embedding_id = e.id
    JOIN traditional_foods tf ON tf.id = em.source_id AND em.source_table = 'traditional_foods'
    WHERE p_query_embedding IS NOT NULL
      AND e.content_type IN ('food_entity', 'ingredients_core')
      AND (1 - (e.embedding <=> p_query_embedding)) >= p_similarity_threshold
      AND tf.id NOT IN (SELECT id FROM exact_matches)
    ORDER BY e.embedding <=> p_query_embedding
    LIMIT p_similar_limit
  )
  
  -- Combine results
  SELECT * FROM exact_matches
  UNION ALL
  SELECT * FROM similar_items
  ORDER BY similarity DESC;
END;
$$;

-- B.2 Find similar foods by embedding ID
CREATE OR REPLACE FUNCTION find_similar_foods(
  p_food_id BIGINT,
  p_limit INT DEFAULT 10,
  p_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
  id BIGINT,
  rep_code TEXT,
  rep_name TEXT,
  indication TEXT,
  ingredients TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_embedding vector(1536);
BEGIN
  -- Get embedding for source food
  SELECT e.embedding INTO v_embedding
  FROM embedding_mappings em
  JOIN embeddings e ON e.id = em.embedding_id
  WHERE em.source_table = 'traditional_foods'
    AND em.source_id = p_food_id
    AND em.content_type = 'ingredients_core'
  LIMIT 1;
  
  IF v_embedding IS NULL THEN
    -- Fallback to indication embedding
    SELECT e.embedding INTO v_embedding
    FROM embedding_mappings em
    JOIN embeddings e ON e.id = em.embedding_id
    WHERE em.source_table = 'traditional_foods'
      AND em.source_id = p_food_id
      AND em.content_type = 'indication'
    LIMIT 1;
  END IF;
  
  IF v_embedding IS NULL THEN
    RETURN;
  END IF;
  
  RETURN QUERY
  SELECT 
    tf.id,
    tf.rep_code,
    tf.rep_name,
    tf.indication,
    tf.ingredients,
    (1 - (e.embedding <=> v_embedding))::FLOAT as similarity
  FROM embeddings e
  JOIN embedding_mappings em ON em.embedding_id = e.id
  JOIN traditional_foods tf ON tf.id = em.source_id AND em.source_table = 'traditional_foods'
  WHERE tf.id != p_food_id
    AND e.content_type IN ('ingredients_core', 'indication')
    AND (1 - (e.embedding <=> v_embedding)) >= p_threshold
  ORDER BY e.embedding <=> v_embedding
  LIMIT p_limit;
END;
$$;

-- ============================================
-- Master Table Search Functions
-- ============================================

-- Search disease_master by embedding
CREATE OR REPLACE FUNCTION search_disease_by_symptom(
  p_query_embedding vector(1536),
  p_limit INT DEFAULT 10
)
RETURNS TABLE (
  id BIGINT,
  disease TEXT,
  modern_disease TEXT,
  disease_alias TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    dm.id,
    dm.disease,
    dm.modern_disease,
    dm.disease_alias,
    (1 - (e.embedding <=> p_query_embedding))::FLOAT as similarity
  FROM embeddings e
  JOIN embedding_mappings em ON em.embedding_id = e.id
  JOIN disease_master dm ON dm.id = em.source_id AND em.source_table = 'disease_master'
  WHERE e.content_type = 'disease_entity'
  ORDER BY e.embedding <=> p_query_embedding
  LIMIT p_limit;
END;
$$;

-- Search prescription_master by embedding
CREATE OR REPLACE FUNCTION search_prescription(
  p_query_embedding vector(1536),
  p_limit INT DEFAULT 10
)
RETURNS TABLE (
  id BIGINT,
  prescription TEXT,
  prescription_modern TEXT,
  prescription_alias TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    pm.id,
    pm.prescription,
    pm.prescription_modern,
    pm.prescription_alias,
    (1 - (e.embedding <=> p_query_embedding))::FLOAT as similarity
  FROM embeddings e
  JOIN embedding_mappings em ON em.embedding_id = e.id
  JOIN prescription_master pm ON pm.id = em.source_id AND em.source_table = 'prescription_master'
  WHERE e.content_type = 'prescription_entity'
  ORDER BY e.embedding <=> p_query_embedding
  LIMIT p_limit;
END;
$$;

-- ============================================
-- Utility Functions
-- ============================================

-- Check if embedding exists in cache
CREATE OR REPLACE FUNCTION embedding_exists(
  p_content_hash VARCHAR(64),
  p_model VARCHAR(50) DEFAULT 'text-embedding-3-small'
)
RETURNS BIGINT
LANGUAGE sql
AS $$
  SELECT id FROM embeddings 
  WHERE content_hash = p_content_hash AND model = p_model
  LIMIT 1;
$$;

-- Get cache statistics
CREATE OR REPLACE FUNCTION get_embedding_cache_stats()
RETURNS TABLE (
  total_embeddings BIGINT,
  total_mappings BIGINT,
  total_tokens BIGINT,
  content_types JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    (SELECT COUNT(*) FROM embeddings)::BIGINT,
    (SELECT COUNT(*) FROM embedding_mappings)::BIGINT,
    (SELECT COALESCE(SUM(tokens_used), 0) FROM embeddings)::BIGINT,
    (SELECT jsonb_object_agg(content_type, cnt) 
     FROM (SELECT content_type, COUNT(*) as cnt 
           FROM embeddings GROUP BY content_type) sub);
END;
$$;

-- ============================================
-- Comments
-- ============================================

COMMENT ON FUNCTION search_symptom_hybrid IS 'Flow A: Symptom query to food/prescription recommendations';
COMMENT ON FUNCTION search_symptom_vector IS 'Flow A: Pure vector search for symptoms';
COMMENT ON FUNCTION search_food_hybrid IS 'Flow B: Food/ingredient search with exact + similar matches';
COMMENT ON FUNCTION find_similar_foods IS 'Find similar foods based on ingredients or indication';
COMMENT ON FUNCTION embedding_exists IS 'Check if embedding exists in cache by hash';
