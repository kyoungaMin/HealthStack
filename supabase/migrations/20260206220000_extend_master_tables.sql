-- =============================================
-- Migration: Extend Master Tables
-- Date: 2026-02-06
-- Description: Add modern terminology columns to foods_master and disease_master
-- =============================================

-- -----------------------------------------------
-- 1. foods_master 테이블 확장
-- -----------------------------------------------
ALTER TABLE foods_master 
  ADD COLUMN IF NOT EXISTS modern_name text,
  ADD COLUMN IF NOT EXISTS name_en text,
  ADD COLUMN IF NOT EXISTS aliases text[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS category text,
  ADD COLUMN IF NOT EXISTS nutrients jsonb,
  ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_foods_master_modern ON foods_master(modern_name);
CREATE INDEX IF NOT EXISTS idx_foods_master_category ON foods_master(category);
CREATE INDEX IF NOT EXISTS idx_foods_master_name_en ON foods_master(name_en);

-- GIN 인덱스 (별칭 검색용)
CREATE INDEX IF NOT EXISTS idx_foods_master_aliases ON foods_master USING GIN(aliases);

COMMENT ON COLUMN foods_master.modern_name IS '현대 한글명 (예: 대추)';
COMMENT ON COLUMN foods_master.name_en IS '영문명 (예: Jujube, Red Date)';
COMMENT ON COLUMN foods_master.aliases IS '동의어/별칭 배열';
COMMENT ON COLUMN foods_master.category IS '분류 (과일, 채소, 곡물, 약재, 해산물, 육류, 유제품, 견과류)';
COMMENT ON COLUMN foods_master.nutrients IS '주요 영양소 정보 (JSON)';

-- -----------------------------------------------
-- 2. disease_master 테이블 확장
-- -----------------------------------------------
ALTER TABLE disease_master 
  ADD COLUMN IF NOT EXISTS modern_name_ko text,
  ADD COLUMN IF NOT EXISTS name_en text,
  ADD COLUMN IF NOT EXISTS icd10_code text,
  ADD COLUMN IF NOT EXISTS category text,
  ADD COLUMN IF NOT EXISTS aliases text[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_disease_master_modern_ko ON disease_master(modern_name_ko);
CREATE INDEX IF NOT EXISTS idx_disease_master_name_en ON disease_master(name_en);
CREATE INDEX IF NOT EXISTS idx_disease_master_category ON disease_master(category);
CREATE INDEX IF NOT EXISTS idx_disease_master_icd10 ON disease_master(icd10_code);

-- GIN 인덱스 (별칭 검색용)
CREATE INDEX IF NOT EXISTS idx_disease_master_aliases ON disease_master USING GIN(aliases);

COMMENT ON COLUMN disease_master.modern_name_ko IS '현대 한글 질병명 (명확한 현대어)';
COMMENT ON COLUMN disease_master.name_en IS '영문 질병명';
COMMENT ON COLUMN disease_master.icd10_code IS 'ICD-10 코드 (선택적)';
COMMENT ON COLUMN disease_master.category IS '분류 (수면, 소화, 피로, 호흡, 순환, 피부, 정신, 통증, 면역)';
COMMENT ON COLUMN disease_master.aliases IS '동의어/별칭 배열';

-- -----------------------------------------------
-- 3. updated_at 트리거 (자동 갱신)
-- -----------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- foods_master 트리거
DROP TRIGGER IF EXISTS update_foods_master_updated_at ON foods_master;
CREATE TRIGGER update_foods_master_updated_at
    BEFORE UPDATE ON foods_master
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- disease_master 트리거
DROP TRIGGER IF EXISTS update_disease_master_updated_at ON disease_master;
CREATE TRIGGER update_disease_master_updated_at
    BEFORE UPDATE ON disease_master
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------
-- 4. tkm_symptom_master 테이블 확장 (name_en 컬럼 추가)
-- -----------------------------------------------
ALTER TABLE tkm_symptom_master 
  ADD COLUMN IF NOT EXISTS name_en text;

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_tkm_symptom_master_name_en ON tkm_symptom_master(name_en);

COMMENT ON COLUMN tkm_symptom_master.name_en IS '영문 증상명 (예: Insomnia, Dyspepsia)';
