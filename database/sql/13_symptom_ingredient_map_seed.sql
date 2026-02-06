-- =============================================
-- Migration: Create Symptom Ingredient Map Table + Seed Data
-- Date: 2026-02-06
-- Description: 증상 → 식재료 추천/주의/회피 매핑
-- =============================================

-- -----------------------------------------------
-- 1. symptom_ingredient_map 테이블 생성/확장
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS symptom_ingredient_map (
  id bigserial PRIMARY KEY,
  
  symptom_id bigint NOT NULL REFERENCES disease_master(id) ON DELETE CASCADE,
  rep_code text NOT NULL REFERENCES foods_master(rep_code) ON DELETE CASCADE,
  
  -- direction 규칙:
  -- 'recommend' : 적극 추천 (이 증상에 효과적)
  -- 'good'      : 권장 (도움이 됨)
  -- 'neutral'   : 중립 (특별한 영향 없음)
  -- 'caution'   : 주의 (과다 섭취 주의)
  -- 'avoid'     : 회피 (악화 가능성)
  direction text NOT NULL CHECK (direction IN ('recommend', 'good', 'neutral', 'caution', 'avoid')),
  
  rationale_ko text,  -- 사용자에게 보여줄 한 줄 이유
  rationale_en text,  -- 영문 이유 (선택)
  
  priority int DEFAULT 50 CHECK (priority >= 1 AND priority <= 100),
  -- priority 규칙: 1~100, 높을수록 우선 표시
  -- 90~100: 핵심 추천 (동의보감 명시적 언급)
  -- 70~89:  강력 추천 (다수 문헌 근거)
  -- 50~69:  일반 추천 (경험적 근거)
  -- 30~49:  참고 추천 (간접 연관)
  -- 1~29:   약한 연관 (보조적)
  
  source_ref text,    -- 출처 (동의보감/본초강목/현대연구 등)
  evidence_level text CHECK (evidence_level IN ('traditional', 'clinical', 'empirical', 'theoretical')),
  
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  
  UNIQUE(symptom_id, rep_code)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_symptom_ingredient_symptom ON symptom_ingredient_map(symptom_id);
CREATE INDEX IF NOT EXISTS idx_symptom_ingredient_rep_code ON symptom_ingredient_map(rep_code);
CREATE INDEX IF NOT EXISTS idx_symptom_ingredient_direction ON symptom_ingredient_map(direction);
CREATE INDEX IF NOT EXISTS idx_symptom_ingredient_priority ON symptom_ingredient_map(priority DESC);

-- 컬럼 코멘트
COMMENT ON TABLE symptom_ingredient_map IS 'Symptom to ingredient recommendation/caution/avoid mapping';
COMMENT ON COLUMN symptom_ingredient_map.direction IS 'recommend, good, neutral, caution, avoid';
COMMENT ON COLUMN symptom_ingredient_map.priority IS 'Priority 1-100, higher = show first';
COMMENT ON COLUMN symptom_ingredient_map.evidence_level IS 'traditional, clinical, empirical, theoretical';

-- 트리거
DROP TRIGGER IF EXISTS update_symptom_ingredient_map_updated_at ON symptom_ingredient_map;
CREATE TRIGGER update_symptom_ingredient_map_updated_at
    BEFORE UPDATE ON symptom_ingredient_map
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------
-- 2. 시드 데이터 삽입
-- -----------------------------------------------

INSERT INTO symptom_ingredient_map (symptom_id, rep_code, direction, rationale_ko, priority, source_ref, evidence_level)

-- ===================================================================
-- 불면 (不眠) 관련 추천/주의 식재료
-- ===================================================================
SELECT d.id, 'F001', 'recommend', '대추는 심신을 안정시키고 숙면을 돕습니다', 95, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '不眠'
UNION ALL
SELECT d.id, 'V002', 'recommend', '상추에는 수면 유도 성분(락투신)이 있습니다', 90, '현대연구', 'clinical'
FROM disease_master d WHERE d.disease = '不眠'
UNION ALL
SELECT d.id, 'V001', 'good', '연근은 마음을 안정시키고 불면에 도움됩니다', 85, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '不眠'
UNION ALL
SELECT d.id, 'H010', 'recommend', '연자(연자육)는 심장을 편안하게 하고 불면을 다스립니다', 92, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '不眠'
UNION ALL
SELECT d.id, 'D001', 'good', '꿀을 따뜻한 물에 타서 마시면 숙면에 도움됩니다', 80, '전통의학', 'empirical'
FROM disease_master d WHERE d.disease = '不眠'
UNION ALL
SELECT d.id, 'H005', 'good', '오미자는 심장을 안정시켜 불면에 좋습니다', 78, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '不眠'
-- 불면 시 주의 식재료
UNION ALL
SELECT d.id, 'V004', 'caution', '생강은 몸을 따뜻하게 하므로 저녁에는 적게 드세요', 40, '경험의학', 'empirical'
FROM disease_master d WHERE d.disease = '不眠'
UNION ALL
SELECT d.id, 'H001', 'caution', '인삼은 기운을 북돋아 밤에 섭취 시 수면을 방해할 수 있습니다', 35, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '不眠'

-- ===================================================================
-- 소화불량 (消化不良) 관련 추천/주의 식재료
-- ===================================================================
UNION ALL
SELECT d.id, 'V006', 'recommend', '무는 소화를 촉진하고 체한 것을 풀어줍니다', 95, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '消化不良'
UNION ALL
SELECT d.id, 'V004', 'recommend', '생강은 위장을 따뜻하게 하고 소화를 돕습니다', 92, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '消化不良'
UNION ALL
SELECT d.id, 'F009', 'recommend', '매실은 소화를 촉진하고 식욕을 돋웁니다', 90, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '消化不良'
UNION ALL
SELECT d.id, 'H008', 'good', '진피(귤껍질)는 기를 순환시켜 소화를 돕습니다', 85, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '消化不良'
UNION ALL
SELECT d.id, 'G001', 'good', '율무는 소화기능을 강화하고 습을 제거합니다', 80, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '消化不良'
-- 소화불량 시 주의
UNION ALL
SELECT d.id, 'D002', 'caution', '우유는 소화가 어려울 수 있으니 적당히 드세요', 40, '현대연구', 'clinical'
FROM disease_master d WHERE d.disease = '消化不良'
UNION ALL
SELECT d.id, 'G006', 'caution', '찹쌀은 소화에 부담될 수 있습니다', 35, '경험의학', 'empirical'
FROM disease_master d WHERE d.disease = '消化不良'

-- ===================================================================
-- 피로/권태 (倦怠) 관련 추천 식재료
-- ===================================================================
UNION ALL
SELECT d.id, 'H001', 'recommend', '인삼은 기력을 보충하고 피로를 풀어줍니다', 98, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '倦怠'
UNION ALL
SELECT d.id, 'H003', 'recommend', '황기는 기를 보충하여 만성 피로에 좋습니다', 95, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '倦怠'
UNION ALL
SELECT d.id, 'F001', 'good', '대추는 비장과 위장을 튼튼히 하여 기력을 북돋습니다', 88, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '倦怠'
UNION ALL
SELECT d.id, 'G004', 'good', '검정콩은 신장을 보하고 체력을 강화합니다', 85, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '倦怠'
UNION ALL
SELECT d.id, 'H009', 'good', '산약(마)은 비위를 보하고 체력을 증진시킵니다', 82, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '倦怠'
UNION ALL
SELECT d.id, 'M001', 'good', '닭고기는 기혈을 보충하여 허약함을 개선합니다', 80, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '倦怠'

-- ===================================================================
-- 기침 (咳嗽) 관련 추천 식재료
-- ===================================================================
UNION ALL
SELECT d.id, 'F002', 'recommend', '배는 폐를 윤택하게 하고 기침을 진정시킵니다', 96, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '咳嗽'
UNION ALL
SELECT d.id, 'V001', 'good', '연근은 폐를 맑게 하고 가래를 삭입니다', 88, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '咳嗽'
UNION ALL
SELECT d.id, 'D001', 'good', '꿀은 목을 부드럽게 하고 기침을 완화합니다', 85, '전통의학', 'empirical'
FROM disease_master d WHERE d.disease = '咳嗽'
UNION ALL
SELECT d.id, 'S001', 'good', '다시마는 가래를 삭이는 데 도움됩니다', 75, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '咳嗽'
-- 기침 시 주의
UNION ALL
SELECT d.id, 'V004', 'caution', '생강은 마른 기침에는 도움되나 가래 있는 기침에는 주의', 40, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '咳嗽'

-- ===================================================================
-- 두통 (頭痛) 관련 추천 식재료
-- ===================================================================
UNION ALL
SELECT d.id, 'H012', 'recommend', '국화차는 머리를 맑게 하고 두통을 완화합니다', 90, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '頭痛'
UNION ALL
SELECT d.id, 'H011', 'good', '결명자차는 눈과 머리를 맑게 합니다', 85, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '頭痛'
UNION ALL
SELECT d.id, 'H006', 'good', '계피는 혈액순환을 도와 두통 완화에 좋습니다', 80, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '頭痛'
UNION ALL
SELECT d.id, 'V010', 'good', '미나리는 열을 내리고 두통에 도움됩니다', 75, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '頭痛'

-- ===================================================================
-- 변비 (便秘) 관련 추천 식재료
-- ===================================================================
UNION ALL
SELECT d.id, 'V009', 'recommend', '시금치는 장을 윤택하게 하여 변비에 좋습니다', 92, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '便秘'
UNION ALL
SELECT d.id, 'G005', 'recommend', '현미는 식이섬유가 풍부하여 장운동을 돕습니다', 90, '현대연구', 'clinical'
FROM disease_master d WHERE d.disease = '便秘'
UNION ALL
SELECT d.id, 'D006', 'good', '참깨(흑임자)는 장을 윤활하게 하여 변비에 효과적입니다', 88, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '便秘'
UNION ALL
SELECT d.id, 'D001', 'good', '꿀은 장을 부드럽게 하여 배변을 돕습니다', 85, '전통의학', 'empirical'
FROM disease_master d WHERE d.disease = '便秘'
UNION ALL
SELECT d.id, 'H011', 'good', '결명자는 장을 청소하고 변비에 도움됩니다', 82, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '便秘'

-- ===================================================================
-- 수족냉증 (手足冷) 관련 추천 식재료
-- ===================================================================
UNION ALL
SELECT d.id, 'V004', 'recommend', '생강은 몸을 따뜻하게 하여 손발 냉증에 효과적입니다', 95, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '手足冷'
UNION ALL
SELECT d.id, 'H006', 'recommend', '계피는 양기를 보하여 냉증을 개선합니다', 92, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '手足冷'
UNION ALL
SELECT d.id, 'M004', 'good', '양고기는 몸을 따뜻하게 하는 대표 식품입니다', 88, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '手足冷'
UNION ALL
SELECT d.id, 'H004', 'good', '당귀는 혈액순환을 도와 냉증 개선에 좋습니다', 85, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '手足冷'
UNION ALL
SELECT d.id, 'V003', 'good', '마늘은 몸을 따뜻하게 하고 기혈순환을 돕습니다', 82, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '手足冷'
-- 수족냉증 시 주의
UNION ALL
SELECT d.id, 'G002', 'caution', '녹두는 성질이 차가우니 냉증에는 적게 드세요', 35, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '手足冷'
UNION ALL
SELECT d.id, 'V007', 'caution', '동과(동아)는 몸을 차게 하니 주의하세요', 30, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '手足冷'

-- ===================================================================
-- 불안/심번 (心煩) 관련 추천 식재료
-- ===================================================================
UNION ALL
SELECT d.id, 'H010', 'recommend', '연자(연자육)는 심장을 안정시키고 불안을 완화합니다', 92, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '心煩'
UNION ALL
SELECT d.id, 'F001', 'recommend', '대추는 신경을 안정시키고 마음을 편안하게 합니다', 90, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '心煩'
UNION ALL
SELECT d.id, 'H007', 'good', '복령은 심신을 안정시키는 데 도움됩니다', 85, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '心煩'
UNION ALL
SELECT d.id, 'G008', 'good', '메밀은 열을 내리고 마음을 안정시킵니다', 78, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '心煩'

-- ===================================================================
-- 설사 (泄瀉) 관련 추천/주의 식재료
-- ===================================================================
UNION ALL
SELECT d.id, 'V004', 'recommend', '생강은 위장을 따뜻하게 하여 설사를 멎게 합니다', 90, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '泄瀉'
UNION ALL
SELECT d.id, 'H009', 'recommend', '산약(마)은 비장을 보하여 설사에 효과적입니다', 88, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '泄瀉'
UNION ALL
SELECT d.id, 'G007', 'good', '조는 비위를 튼튼하게 하여 설사에 도움됩니다', 82, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '泄瀉'
-- 설사 시 주의
UNION ALL
SELECT d.id, 'G002', 'avoid', '녹두는 성질이 차가워 설사를 악화시킬 수 있습니다', 25, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '泄瀉'
UNION ALL
SELECT d.id, 'F002', 'caution', '배는 차가운 성질이니 설사 시에는 적게 드세요', 35, '경험의학', 'empirical'
FROM disease_master d WHERE d.disease = '泄瀉'

-- ===================================================================
-- 위통 (胃脘痛) 관련 추천 식재료
-- ===================================================================
UNION ALL
SELECT d.id, 'V004', 'recommend', '생강은 위를 따뜻하게 하고 통증을 완화합니다', 92, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '胃脘痛'
UNION ALL
SELECT d.id, 'V008', 'good', '호박은 위를 보하고 통증을 완화합니다', 85, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '胃脘痛'
UNION ALL
SELECT d.id, 'D001', 'good', '꿀은 위 점막을 보호하고 통증을 줄입니다', 80, '현대연구', 'clinical'
FROM disease_master d WHERE d.disease = '胃脘痛'

-- ===================================================================
-- 요통 (腰痛) 관련 추천 식재료
-- ===================================================================
UNION ALL
SELECT d.id, 'G004', 'recommend', '검정콩은 신장을 보하여 요통에 효과적입니다', 90, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '腰痛'
UNION ALL
SELECT d.id, 'D005', 'good', '호두는 신장과 허리를 보강합니다', 85, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '腰痛'
UNION ALL
SELECT d.id, 'F010', 'good', '구기자는 간과 신장을 보하여 허리에 좋습니다', 82, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '腰痛'
UNION ALL
SELECT d.id, 'S003', 'good', '굴은 신장을 보강하여 요통 개선에 도움됩니다', 78, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '腰痛'

-- ===================================================================
-- 부종 (浮腫) 관련 추천/주의 식재료
-- ===================================================================
UNION ALL
SELECT d.id, 'G001', 'recommend', '율무는 이뇨작용이 있어 부종에 효과적입니다', 95, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '浮腫'
UNION ALL
SELECT d.id, 'G003', 'recommend', '팥은 부종을 빼는 대표적인 식품입니다', 92, '동의보감', 'traditional'
FROM disease_master d WHERE d.disease = '浮腫'
UNION ALL
SELECT d.id, 'V007', 'good', '동과(동아)는 수분 배출을 도와 부종에 좋습니다', 88, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '浮腫'
UNION ALL
SELECT d.id, 'V013', 'good', '오이는 이뇨작용이 있어 부종 해소에 도움됩니다', 82, '현대연구', 'clinical'
FROM disease_master d WHERE d.disease = '浮腫'

ON CONFLICT (symptom_id, rep_code) DO UPDATE SET
  direction = EXCLUDED.direction,
  rationale_ko = EXCLUDED.rationale_ko,
  priority = EXCLUDED.priority,
  source_ref = EXCLUDED.source_ref,
  evidence_level = EXCLUDED.evidence_level,
  updated_at = now();

-- -----------------------------------------------
-- 3. 조회용 뷰
-- -----------------------------------------------
CREATE OR REPLACE VIEW v_symptom_ingredient_recommendations AS
SELECT 
  d.disease,
  d.modern_name_ko AS symptom_ko,
  d.name_en AS symptom_en,
  f.modern_name AS ingredient_ko,
  f.name_en AS ingredient_en,
  f.category AS ingredient_category,
  m.direction,
  m.rationale_ko,
  m.priority,
  m.source_ref,
  m.evidence_level
FROM symptom_ingredient_map m
JOIN disease_master d ON m.symptom_id = d.id
JOIN foods_master f ON m.rep_code = f.rep_code
ORDER BY d.category, d.disease, 
  CASE m.direction 
    WHEN 'recommend' THEN 1 
    WHEN 'good' THEN 2 
    WHEN 'neutral' THEN 3 
    WHEN 'caution' THEN 4 
    WHEN 'avoid' THEN 5 
  END,
  m.priority DESC;
