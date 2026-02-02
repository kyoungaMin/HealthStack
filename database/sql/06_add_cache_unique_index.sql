-- ============================================
-- babiyagida - Cache Unique Index for Embeddings
-- ============================================
-- This index enables content_hash + model based caching
-- Required for embed_pipeline.py to work correctly
-- ============================================

-- Add unique index for cache lookup (content_hash + model)
CREATE UNIQUE INDEX IF NOT EXISTS uq_embeddings_content_hash_model 
ON public.embeddings(content_hash, model);

-- Verify the index was created
SELECT 
  indexname,
  indexdef
FROM pg_indexes 
WHERE tablename = 'embeddings'
ORDER BY indexname;
