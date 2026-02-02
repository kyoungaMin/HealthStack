-- ============================================
-- 밥이약이다 (babiyagida) - pgvector 확장 활성화
-- ============================================
-- 실행 방법: Supabase Dashboard > SQL Editor에서 실행
-- ============================================

-- 1. pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 확인
SELECT * FROM pg_extension WHERE extname = 'vector';
