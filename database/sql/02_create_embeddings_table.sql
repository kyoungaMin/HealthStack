-- ============================================
-- 밥이약이다 (babiyagida) - Embeddings 테이블 생성
-- ============================================
-- 사전 조건: 01_enable_pgvector.sql 실행 완료
-- ============================================

-- 1. embeddings 테이블 생성
CREATE TABLE IF NOT EXISTS embeddings (
  id BIGSERIAL PRIMARY KEY,
  
  -- 연결 정보
  source_table VARCHAR(50) NOT NULL,         -- 'traditional_foods', 'disease_master', 'prescription_master'
  source_id BIGINT NOT NULL,                 -- 원본 테이블의 id
  
  -- 임베딩 내용
  content_type VARCHAR(50) NOT NULL,         -- 'search_combined', 'disease', 'prescription'
  content TEXT NOT NULL,                     -- 임베딩 생성에 사용된 원본 텍스트
  content_hash VARCHAR(64) NOT NULL,         -- SHA256 해시 (변경 감지용)
  
  -- 벡터 임베딩
  embedding vector(1536),                    -- OpenAI text-embedding-3-small (1536차원)
  
  -- 메타데이터
  model VARCHAR(50) DEFAULT 'text-embedding-3-small',
  tokens_used INT,                           -- 토큰 사용량 추적
  
  -- 타임스탬프
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- 유니크 제약 (동일 소스의 동일 타입은 하나만)
  UNIQUE(source_table, source_id, content_type)
);

-- 2. 인덱스 생성

-- 소스 테이블별 조회용
CREATE INDEX IF NOT EXISTS idx_embeddings_source 
ON embeddings(source_table, source_id);

-- 컨텐츠 타입별 조회용
CREATE INDEX IF NOT EXISTS idx_embeddings_type 
ON embeddings(content_type);

-- 벡터 검색용 IVFFlat 인덱스 (코사인 유사도)
-- 참고: 데이터가 충분히 쌓인 후(최소 1000개) 생성하는 것이 효율적
-- lists 값은 sqrt(row_count)로 설정하는 것이 권장됨
CREATE INDEX IF NOT EXISTS idx_embeddings_vector 
ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 3. 업데이트 시간 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_embeddings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_embeddings_updated_at ON embeddings;
CREATE TRIGGER trigger_embeddings_updated_at
  BEFORE UPDATE ON embeddings
  FOR EACH ROW
  EXECUTE FUNCTION update_embeddings_updated_at();

-- 4. 코멘트 추가
COMMENT ON TABLE embeddings IS '동의보감 데이터 벡터 임베딩 테이블 - 시맨틱 검색용';
COMMENT ON COLUMN embeddings.source_table IS '원본 테이블명 (traditional_foods, disease_master, prescription_master)';
COMMENT ON COLUMN embeddings.content_type IS '임베딩 타입 (search_combined: 검색용 통합, disease: 질병, prescription: 처방)';
COMMENT ON COLUMN embeddings.content_hash IS 'SHA256 해시 - 원본 변경 감지용';
COMMENT ON COLUMN embeddings.embedding IS 'OpenAI text-embedding-3-small 1536차원 벡터';

-- 확인
SELECT 
  column_name, 
  data_type, 
  is_nullable
FROM information_schema.columns 
WHERE table_name = 'embeddings'
ORDER BY ordinal_position;
