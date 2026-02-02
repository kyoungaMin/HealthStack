-- ============================================
-- babiyagida - Embedding Cache Migration
-- ============================================
-- Purpose: Convert row-level embeddings to unique text cache structure
-- Prerequisite: 02_create_embeddings_table.sql executed
-- ============================================

-- ============================================
-- PHASE 1: Schema Changes
-- ============================================

-- 1.1 Drop old unique constraint (row-level)
ALTER TABLE embeddings 
DROP CONSTRAINT IF EXISTS embeddings_source_table_source_id_content_type_key;

-- 1.2 Add cache-based unique constraint (content_hash + model)
-- This ensures same text is only embedded once per model
ALTER TABLE embeddings 
ADD CONSTRAINT embeddings_cache_unique 
UNIQUE (content_type, content_hash, model);

-- 1.3 Make source_table and source_id nullable for cache entries
ALTER TABLE embeddings 
ALTER COLUMN source_table DROP NOT NULL,
ALTER COLUMN source_id DROP NOT NULL;

-- 1.4 Add index for cache lookups
CREATE INDEX IF NOT EXISTS idx_embeddings_cache_lookup 
ON embeddings(content_hash, model);

-- ============================================
-- PHASE 2: Mapping Table
-- ============================================

-- 2.1 Create embedding_mappings table
CREATE TABLE IF NOT EXISTS embedding_mappings (
  id BIGSERIAL PRIMARY KEY,
  
  -- Source reference
  source_table VARCHAR(50) NOT NULL,     -- 'traditional_foods', 'disease_master', etc.
  source_id BIGINT NOT NULL,             -- Row ID in source table
  
  -- Embedding reference
  embedding_id BIGINT NOT NULL REFERENCES embeddings(id) ON DELETE CASCADE,
  content_type VARCHAR(50) NOT NULL,     -- Must match embeddings.content_type
  
  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Constraints
  UNIQUE(source_table, source_id, content_type)
);

-- 2.2 Indexes for mapping table
CREATE INDEX IF NOT EXISTS idx_em_source 
ON embedding_mappings(source_table, source_id);

CREATE INDEX IF NOT EXISTS idx_em_embedding 
ON embedding_mappings(embedding_id);

CREATE INDEX IF NOT EXISTS idx_em_content_type 
ON embedding_mappings(content_type);

-- 2.3 Comments
COMMENT ON TABLE embedding_mappings IS 'Maps source rows to cached embeddings (many-to-one)';
COMMENT ON COLUMN embedding_mappings.source_table IS 'Source table name (traditional_foods, disease_master, etc.)';
COMMENT ON COLUMN embedding_mappings.embedding_id IS 'Reference to cached embedding';

-- ============================================
-- PHASE 3: Content Type Enum (Optional)
-- ============================================

-- 3.1 Create content_type enum for validation
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'embedding_content_type') THEN
    CREATE TYPE embedding_content_type AS ENUM (
      'symptom_query',        -- User query (runtime)
      'indication',           -- Symptom/indication text
      'food_entity',          -- Food/ingredient entity
      'prescription_entity',  -- Prescription entity
      'ingredients_core',     -- Core ingredients (1-5)
      'disease_entity'        -- Disease entity
    );
  END IF;
END $$;

-- Note: Not enforcing enum on existing column to allow migration
-- Can add: ALTER TABLE embeddings ALTER COLUMN content_type TYPE embedding_content_type USING content_type::embedding_content_type;

-- ============================================
-- PHASE 4: Cache Lookup Functions
-- ============================================

-- 4.1 Get or create embedding (upsert pattern)
CREATE OR REPLACE FUNCTION get_or_create_embedding(
  p_content_type VARCHAR(50),
  p_content TEXT,
  p_content_hash VARCHAR(64),
  p_embedding vector(1536),
  p_model VARCHAR(50) DEFAULT 'text-embedding-3-small',
  p_tokens_used INT DEFAULT NULL
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
  v_embedding_id BIGINT;
BEGIN
  -- Try to find existing cached embedding
  SELECT id INTO v_embedding_id
  FROM embeddings
  WHERE content_hash = p_content_hash
    AND model = p_model
    AND content_type = p_content_type
  LIMIT 1;
  
  -- If not found, create new
  IF v_embedding_id IS NULL THEN
    INSERT INTO embeddings (
      content_type, content, content_hash, embedding, model, tokens_used
    ) VALUES (
      p_content_type, p_content, p_content_hash, p_embedding, p_model, p_tokens_used
    )
    RETURNING id INTO v_embedding_id;
  END IF;
  
  RETURN v_embedding_id;
END;
$$;

-- 4.2 Link source row to embedding
CREATE OR REPLACE FUNCTION link_source_to_embedding(
  p_source_table VARCHAR(50),
  p_source_id BIGINT,
  p_embedding_id BIGINT,
  p_content_type VARCHAR(50)
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  INSERT INTO embedding_mappings (
    source_table, source_id, embedding_id, content_type
  ) VALUES (
    p_source_table, p_source_id, p_embedding_id, p_content_type
  )
  ON CONFLICT (source_table, source_id, content_type) 
  DO UPDATE SET embedding_id = EXCLUDED.embedding_id;
END;
$$;

-- 4.3 Get embedding for source row
CREATE OR REPLACE FUNCTION get_embedding_for_source(
  p_source_table VARCHAR(50),
  p_source_id BIGINT,
  p_content_type VARCHAR(50)
)
RETURNS vector(1536)
LANGUAGE plpgsql
AS $$
DECLARE
  v_embedding vector(1536);
BEGIN
  SELECT e.embedding INTO v_embedding
  FROM embedding_mappings em
  JOIN embeddings e ON e.id = em.embedding_id
  WHERE em.source_table = p_source_table
    AND em.source_id = p_source_id
    AND em.content_type = p_content_type;
    
  RETURN v_embedding;
END;
$$;

-- ============================================
-- PHASE 5: Updated Search Functions
-- ============================================

-- 5.1 Search by symptom query (Flow A)
CREATE OR REPLACE FUNCTION search_by_symptom(
  p_query_embedding vector(1536),
  p_limit INT DEFAULT 10
)
RETURNS TABLE (
  source_id BIGINT,
  source_table VARCHAR(50),
  content_type VARCHAR(50),
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    em.source_id,
    em.source_table,
    em.content_type,
    (1 - (e.embedding <=> p_query_embedding))::FLOAT as similarity
  FROM embeddings e
  JOIN embedding_mappings em ON em.embedding_id = e.id
  WHERE e.content_type IN ('indication', 'disease_entity')
  ORDER BY e.embedding <=> p_query_embedding
  LIMIT p_limit;
END;
$$;

-- 5.2 Search by food/ingredient (Flow B)
CREATE OR REPLACE FUNCTION search_by_food(
  p_query_embedding vector(1536),
  p_limit INT DEFAULT 10
)
RETURNS TABLE (
  source_id BIGINT,
  source_table VARCHAR(50),
  content_type VARCHAR(50),
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    em.source_id,
    em.source_table,
    em.content_type,
    (1 - (e.embedding <=> p_query_embedding))::FLOAT as similarity
  FROM embeddings e
  JOIN embedding_mappings em ON em.embedding_id = e.id
  WHERE e.content_type IN ('food_entity', 'ingredients_core', 'prescription_entity')
  ORDER BY e.embedding <=> p_query_embedding
  LIMIT p_limit;
END;
$$;

-- 5.3 Find similar embeddings (for "similar items" feature)
CREATE OR REPLACE FUNCTION find_similar_embeddings(
  p_embedding_id BIGINT,
  p_content_types VARCHAR(50)[] DEFAULT NULL,
  p_limit INT DEFAULT 10,
  p_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
  embedding_id BIGINT,
  source_id BIGINT,
  source_table VARCHAR(50),
  content_type VARCHAR(50),
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_source_embedding vector(1536);
  v_source_content_type VARCHAR(50);
BEGIN
  -- Get source embedding
  SELECT e.embedding, e.content_type 
  INTO v_source_embedding, v_source_content_type
  FROM embeddings e
  WHERE e.id = p_embedding_id;
  
  IF v_source_embedding IS NULL THEN
    RETURN;
  END IF;
  
  RETURN QUERY
  SELECT 
    e.id as embedding_id,
    em.source_id,
    em.source_table,
    e.content_type,
    (1 - (e.embedding <=> v_source_embedding))::FLOAT as similarity
  FROM embeddings e
  LEFT JOIN embedding_mappings em ON em.embedding_id = e.id
  WHERE e.id != p_embedding_id
    AND (p_content_types IS NULL OR e.content_type = ANY(p_content_types))
    AND (1 - (e.embedding <=> v_source_embedding)) >= p_threshold
  ORDER BY e.embedding <=> v_source_embedding
  LIMIT p_limit;
END;
$$;

-- ============================================
-- PHASE 6: Analytics Views
-- ============================================

-- 6.1 Embedding usage statistics
CREATE OR REPLACE VIEW v_embedding_stats AS
SELECT 
  content_type,
  COUNT(DISTINCT id) as unique_embeddings,
  COUNT(DISTINCT em.source_id) as mapped_rows,
  ROUND(COUNT(DISTINCT em.source_id)::NUMERIC / NULLIF(COUNT(DISTINCT e.id), 0), 2) as reuse_ratio,
  SUM(tokens_used) as total_tokens,
  ROUND(AVG(tokens_used), 0) as avg_tokens
FROM embeddings e
LEFT JOIN embedding_mappings em ON em.embedding_id = e.id
GROUP BY content_type
ORDER BY unique_embeddings DESC;

-- 6.2 Cache efficiency view
CREATE OR REPLACE VIEW v_cache_efficiency AS
SELECT 
  (SELECT COUNT(*) FROM embeddings) as total_embeddings,
  (SELECT COUNT(*) FROM embedding_mappings) as total_mappings,
  ROUND(
    (SELECT COUNT(*) FROM embedding_mappings)::NUMERIC / 
    NULLIF((SELECT COUNT(*) FROM embeddings), 0), 2
  ) as avg_reuse_per_embedding,
  (SELECT SUM(tokens_used) FROM embeddings) as total_tokens_saved;

-- ============================================
-- PHASE 7: Data Migration (if existing data)
-- ============================================

-- 7.1 Migrate existing row-level embeddings to cache structure
-- This creates mappings for existing embeddings
DO $$
BEGIN
  -- Only run if embeddings exist with source_table set
  IF EXISTS (SELECT 1 FROM embeddings WHERE source_table IS NOT NULL AND source_id IS NOT NULL) THEN
    INSERT INTO embedding_mappings (source_table, source_id, embedding_id, content_type)
    SELECT source_table, source_id, id, content_type
    FROM embeddings
    WHERE source_table IS NOT NULL AND source_id IS NOT NULL
    ON CONFLICT (source_table, source_id, content_type) DO NOTHING;
    
    RAISE NOTICE 'Migrated existing embeddings to mapping table';
  END IF;
END $$;

-- ============================================
-- Verification
-- ============================================

-- Check table structure
SELECT 
  table_name,
  column_name, 
  data_type, 
  is_nullable
FROM information_schema.columns 
WHERE table_name IN ('embeddings', 'embedding_mappings')
ORDER BY table_name, ordinal_position;

-- Check constraints
SELECT 
  tc.table_name, 
  tc.constraint_name, 
  tc.constraint_type
FROM information_schema.table_constraints tc
WHERE tc.table_name IN ('embeddings', 'embedding_mappings')
ORDER BY tc.table_name;
