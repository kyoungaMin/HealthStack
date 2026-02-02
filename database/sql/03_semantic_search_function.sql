-- ============================================
-- 밥이약이다 (babiyagida) - 시맨틱 검색 함수
-- ============================================
-- 사전 조건: 02_create_embeddings_table.sql 실행 완료
-- ============================================

-- 1. 시맨틱 검색 함수 (traditional_foods 검색)
CREATE OR REPLACE FUNCTION search_foods_semantic(
  query_embedding vector(1536),
  match_threshold FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id BIGINT,
  rep_code TEXT,
  rep_name TEXT,
  prescription_modern TEXT,
  modern_disease TEXT,
  indication TEXT,
  food_type TEXT,
  ingredients TEXT,
  preparation TEXT,
  dosage TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    tf.id,
    tf.rep_code,
    tf.rep_name,
    tf.prescription_modern,
    tf.modern_disease,
    tf.indication,
    tf.food_type,
    tf.ingredients,
    tf.preparation,
    tf.dosage,
    1 - (e.embedding <=> query_embedding) AS similarity
  FROM embeddings e
  INNER JOIN traditional_foods tf ON e.source_id = tf.id
  WHERE 
    e.source_table = 'traditional_foods'
    AND e.content_type = 'search_combined'
    AND 1 - (e.embedding <=> query_embedding) > match_threshold
  ORDER BY e.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 2. 하이브리드 검색 함수 (키워드 + 시맨틱)
CREATE OR REPLACE FUNCTION search_foods_hybrid(
  search_query TEXT,
  query_embedding vector(1536),
  keyword_weight FLOAT DEFAULT 0.3,
  semantic_weight FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id BIGINT,
  rep_code TEXT,
  rep_name TEXT,
  prescription_modern TEXT,
  modern_disease TEXT,
  indication TEXT,
  food_type TEXT,
  keyword_score FLOAT,
  semantic_score FLOAT,
  combined_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH keyword_matches AS (
    -- 키워드 기반 검색 (FTS)
    SELECT 
      tf.id,
      ts_rank(
        to_tsvector('simple', COALESCE(tf.modern_disease, '') || ' ' || 
                              COALESCE(tf.indication, '') || ' ' || 
                              COALESCE(tf.prescription_modern, '')),
        plainto_tsquery('simple', search_query)
      ) AS kw_score
    FROM traditional_foods tf
    WHERE 
      to_tsvector('simple', COALESCE(tf.modern_disease, '') || ' ' || 
                            COALESCE(tf.indication, '') || ' ' || 
                            COALESCE(tf.prescription_modern, ''))
      @@ plainto_tsquery('simple', search_query)
  ),
  semantic_matches AS (
    -- 시맨틱 검색 (벡터 유사도)
    SELECT 
      e.source_id AS id,
      1 - (e.embedding <=> query_embedding) AS sem_score
    FROM embeddings e
    WHERE 
      e.source_table = 'traditional_foods'
      AND e.content_type = 'search_combined'
      AND 1 - (e.embedding <=> query_embedding) > 0.5
  ),
  combined AS (
    -- 두 검색 결과 통합
    SELECT 
      COALESCE(k.id, s.id) AS id,
      COALESCE(k.kw_score, 0) AS kw_score,
      COALESCE(s.sem_score, 0) AS sem_score,
      (COALESCE(k.kw_score, 0) * keyword_weight + 
       COALESCE(s.sem_score, 0) * semantic_weight) AS combined
    FROM keyword_matches k
    FULL OUTER JOIN semantic_matches s ON k.id = s.id
  )
  SELECT 
    tf.id,
    tf.rep_code,
    tf.rep_name,
    tf.prescription_modern,
    tf.modern_disease,
    tf.indication,
    tf.food_type,
    c.kw_score AS keyword_score,
    c.sem_score AS semantic_score,
    c.combined AS combined_score
  FROM combined c
  INNER JOIN traditional_foods tf ON c.id = tf.id
  ORDER BY c.combined DESC
  LIMIT match_count;
END;
$$;

-- 3. 유사 처방 찾기 함수
CREATE OR REPLACE FUNCTION find_similar_foods(
  food_id BIGINT,
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  id BIGINT,
  rep_code TEXT,
  rep_name TEXT,
  prescription_modern TEXT,
  modern_disease TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
DECLARE
  target_embedding vector(1536);
BEGIN
  -- 대상 음식의 임베딩 가져오기
  SELECT e.embedding INTO target_embedding
  FROM embeddings e
  WHERE e.source_table = 'traditional_foods'
    AND e.source_id = food_id
    AND e.content_type = 'search_combined'
  LIMIT 1;
  
  IF target_embedding IS NULL THEN
    RAISE EXCEPTION 'Embedding not found for food_id: %', food_id;
  END IF;
  
  RETURN QUERY
  SELECT 
    tf.id,
    tf.rep_code,
    tf.rep_name,
    tf.prescription_modern,
    tf.modern_disease,
    1 - (e.embedding <=> target_embedding) AS similarity
  FROM embeddings e
  INNER JOIN traditional_foods tf ON e.source_id = tf.id
  WHERE 
    e.source_table = 'traditional_foods'
    AND e.content_type = 'search_combined'
    AND e.source_id != food_id
  ORDER BY e.embedding <=> target_embedding
  LIMIT match_count;
END;
$$;

-- 4. 함수 권한 설정
GRANT EXECUTE ON FUNCTION search_foods_semantic TO anon, authenticated;
GRANT EXECUTE ON FUNCTION search_foods_hybrid TO anon, authenticated;
GRANT EXECUTE ON FUNCTION find_similar_foods TO anon, authenticated;

-- 코멘트
COMMENT ON FUNCTION search_foods_semantic IS '벡터 유사도 기반 시맨틱 검색';
COMMENT ON FUNCTION search_foods_hybrid IS '키워드 + 시맨틱 하이브리드 검색';
COMMENT ON FUNCTION find_similar_foods IS '특정 음식과 유사한 처방 찾기';
