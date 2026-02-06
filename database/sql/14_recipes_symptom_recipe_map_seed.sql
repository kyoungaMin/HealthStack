-- =============================================
-- Migration: Create Recipes + Symptom Recipe Map Seed Data
-- Date: 2026-02-06
-- Description: 레시피 마스터 + 증상별 레시피 추천 매핑
-- =============================================

-- -----------------------------------------------
-- 1. recipes 테이블 생성/확장
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS recipes (
  id bigserial PRIMARY KEY,
  
  title text NOT NULL,
  description text,
  
  -- 재료 정보 (JSONB 배열)
  -- [{"name": "대추", "rep_code": "F001", "amount": "10개"}, ...]
  ingredients jsonb DEFAULT '[]',
  
  -- 조리 단계 (JSONB 배열)
  -- [{"step": 1, "instruction": "대추를 깨끗이 씻는다"}, ...]
  steps jsonb DEFAULT '[]',
  
  -- 메타데이터
  prep_time_min int,           -- 준비 시간 (분)
  cook_time_min int,           -- 조리 시간 (분)
  servings int DEFAULT 2,      -- 인분
  difficulty text CHECK (difficulty IN ('easy', 'medium', 'hard')),
  
  -- 분류 태그
  tags text[] DEFAULT '{}',    -- 예: {'수면', '보양', '해독', '디저트'}
  meal_type text[],            -- 예: {'breakfast', 'lunch', 'dinner', 'snack', 'tea'}
  
  -- 한의학 특성
  nature text,                 -- 성질: 열/온/평/량/한
  flavor text[],               -- 맛: 신/고/감/신/함
  target_organs text[],        -- 귀경: 심/간/비/폐/신
  
  source_ref text,             -- 출처
  
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_recipes_tags ON recipes USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_recipes_meal_type ON recipes USING GIN(meal_type);
CREATE INDEX IF NOT EXISTS idx_recipes_title ON recipes(title);

-- 트리거
DROP TRIGGER IF EXISTS update_recipes_updated_at ON recipes;
CREATE TRIGGER update_recipes_updated_at
    BEFORE UPDATE ON recipes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------
-- 2. symptom_recipe_map 테이블 생성/확장
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS symptom_recipe_map (
  id bigserial PRIMARY KEY,
  
  symptom_id bigint NOT NULL REFERENCES disease_master(id) ON DELETE CASCADE,
  recipe_id bigint NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
  
  meal_slot text CHECK (meal_slot IN ('breakfast', 'lunch', 'dinner', 'snack', 'tea', 'anytime')),
  priority int DEFAULT 50 CHECK (priority >= 1 AND priority <= 100),
  
  rationale_ko text,           -- 추천 이유
  best_time text,              -- 최적 섭취 시간대
  frequency text,              -- 권장 빈도: daily, weekly, occasionally
  
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  
  UNIQUE(symptom_id, recipe_id)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_symptom_recipe_symptom ON symptom_recipe_map(symptom_id);
CREATE INDEX IF NOT EXISTS idx_symptom_recipe_recipe ON symptom_recipe_map(recipe_id);
CREATE INDEX IF NOT EXISTS idx_symptom_recipe_meal_slot ON symptom_recipe_map(meal_slot);

-- 트리거
DROP TRIGGER IF EXISTS update_symptom_recipe_map_updated_at ON symptom_recipe_map;
CREATE TRIGGER update_symptom_recipe_map_updated_at
    BEFORE UPDATE ON symptom_recipe_map
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------
-- 3. 레시피 시드 데이터
-- -----------------------------------------------
INSERT INTO recipes (id, title, description, ingredients, steps, prep_time_min, cook_time_min, servings, difficulty, tags, meal_type, nature, flavor, target_organs, source_ref) VALUES

-- ===== 수면/안정 레시피 =====
(1, '대추차', 
  '심신을 안정시키고 숙면을 돕는 전통 보양차',
  '[{"name": "대추", "rep_code": "F001", "amount": "10개"}, {"name": "물", "amount": "500ml"}]'::jsonb,
  '[{"step": 1, "instruction": "대추를 깨끗이 씻어 칼집을 낸다"}, {"step": 2, "instruction": "물과 함께 30분간 끓인다"}, {"step": 3, "instruction": "기호에 따라 꿀을 넣어 마신다"}]'::jsonb,
  5, 30, 2, 'easy', 
  ARRAY['수면', '보양', '차'], ARRAY['tea', 'snack'],
  '온', ARRAY['감'], ARRAY['심', '비'], '동의보감'),

(2, '연자죽', 
  '마음을 편안하게 하고 불면에 좋은 전통 죽',
  '[{"name": "연자육", "rep_code": "H010", "amount": "30g"}, {"name": "쌀", "amount": "1컵"}, {"name": "물", "amount": "6컵"}]'::jsonb,
  '[{"step": 1, "instruction": "연자육을 30분 불린다"}, {"step": 2, "instruction": "쌀과 함께 죽을 끓인다"}, {"step": 3, "instruction": "연자육이 부드러워질 때까지 저어가며 끓인다"}]'::jsonb,
  35, 40, 2, 'easy',
  ARRAY['수면', '보양', '죽'], ARRAY['breakfast', 'dinner'],
  '평', ARRAY['감'], ARRAY['심', '비', '신'], '동의보감'),

(3, '상추겉절이', 
  '락투신 성분으로 숙면을 돕는 반찬',
  '[{"name": "상추", "rep_code": "V002", "amount": "200g"}, {"name": "고춧가루", "amount": "1큰술"}, {"name": "마늘", "amount": "1쪽"}, {"name": "참기름", "amount": "1큰술"}]'::jsonb,
  '[{"step": 1, "instruction": "상추를 씻어 한입 크기로 뜯는다"}, {"step": 2, "instruction": "양념 재료를 섞는다"}, {"step": 3, "instruction": "상추에 양념을 버무린다"}]'::jsonb,
  10, 0, 2, 'easy',
  ARRAY['수면', '반찬'], ARRAY['lunch', 'dinner'],
  '량', ARRAY['고'], ARRAY['심'], '현대요리'),

-- ===== 소화/위장 레시피 =====
(4, '생강차', 
  '속을 따뜻하게 하고 소화를 돕는 차',
  '[{"name": "생강", "rep_code": "V004", "amount": "30g"}, {"name": "물", "amount": "500ml"}, {"name": "꿀", "rep_code": "D001", "amount": "1큰술"}]'::jsonb,
  '[{"step": 1, "instruction": "생강을 얇게 썬다"}, {"step": 2, "instruction": "물과 함께 20분 끓인다"}, {"step": 3, "instruction": "꿀을 넣어 마신다"}]'::jsonb,
  5, 20, 2, 'easy',
  ARRAY['소화', '감기', '차'], ARRAY['tea', 'anytime'],
  '온', ARRAY['신'], ARRAY['폐', '비', '위'], '동의보감'),

(5, '무생채', 
  '소화를 촉진하고 체한 것을 풀어주는 반찬',
  '[{"name": "무", "rep_code": "V006", "amount": "300g"}, {"name": "고춧가루", "amount": "2큰술"}, {"name": "식초", "amount": "1큰술"}, {"name": "설탕", "amount": "1큰술"}]'::jsonb,
  '[{"step": 1, "instruction": "무를 채 썬다"}, {"step": 2, "instruction": "소금에 절여 물기를 뺀다"}, {"step": 3, "instruction": "양념에 버무린다"}]'::jsonb,
  15, 0, 4, 'easy',
  ARRAY['소화', '반찬'], ARRAY['lunch', 'dinner'],
  '량', ARRAY['신', '감'], ARRAY['폐', '비'], '전통요리'),

(6, '매실차', 
  '식욕을 돋우고 소화를 도우는 새콤한 차',
  '[{"name": "매실청", "rep_code": "F009", "amount": "2큰술"}, {"name": "물", "amount": "200ml"}]'::jsonb,
  '[{"step": 1, "instruction": "매실청을 물에 희석한다"}, {"step": 2, "instruction": "차갑게 또는 따뜻하게 마신다"}]'::jsonb,
  2, 0, 1, 'easy',
  ARRAY['소화', '식욕', '차'], ARRAY['tea', 'anytime'],
  '평', ARRAY['산'], ARRAY['간', '비'], '전통의학'),

-- ===== 피로/보양 레시피 =====
(7, '삼계탕', 
  '기력을 보충하고 피로를 풀어주는 보양식',
  '[{"name": "닭", "rep_code": "M001", "amount": "1마리"}, {"name": "인삼", "rep_code": "H001", "amount": "1뿌리"}, {"name": "대추", "rep_code": "F001", "amount": "5개"}, {"name": "마늘", "rep_code": "V003", "amount": "5쪽"}, {"name": "찹쌀", "rep_code": "G006", "amount": "1/2컵"}]'::jsonb,
  '[{"step": 1, "instruction": "닭 배에 찹쌀, 인삼, 대추를 넣는다"}, {"step": 2, "instruction": "물을 붓고 1시간 끓인다"}, {"step": 3, "instruction": "소금, 후추로 간한다"}]'::jsonb,
  20, 60, 2, 'medium',
  ARRAY['피로', '보양', '탕'], ARRAY['lunch', 'dinner'],
  '온', ARRAY['감'], ARRAY['비', '폐', '신'], '동의보감'),

(8, '황기삼계탕', 
  '만성 피로와 허약 체질에 좋은 보양탕',
  '[{"name": "닭", "rep_code": "M001", "amount": "1마리"}, {"name": "황기", "rep_code": "H003", "amount": "20g"}, {"name": "인삼", "rep_code": "H001", "amount": "1뿌리"}, {"name": "대추", "rep_code": "F001", "amount": "5개"}]'::jsonb,
  '[{"step": 1, "instruction": "모든 재료를 넣고 물을 붓는다"}, {"step": 2, "instruction": "약불에서 1시간 30분 끓인다"}, {"step": 3, "instruction": "고기가 부드러워지면 완성"}]'::jsonb,
  15, 90, 2, 'medium',
  ARRAY['피로', '보양', '면역', '탕'], ARRAY['lunch', 'dinner'],
  '온', ARRAY['감'], ARRAY['비', '폐'], '동의보감'),

(9, '검정콩밥', 
  '신장을 보하고 체력을 강화하는 밥',
  '[{"name": "검정콩", "rep_code": "G004", "amount": "1/2컵"}, {"name": "쌀", "amount": "2컵"}]'::jsonb,
  '[{"step": 1, "instruction": "검정콩을 4시간 불린다"}, {"step": 2, "instruction": "쌀과 섞어 밥을 짓는다"}]'::jsonb,
  240, 30, 4, 'easy',
  ARRAY['피로', '신장', '밥'], ARRAY['lunch', 'dinner'],
  '평', ARRAY['감'], ARRAY['신', '비'], '본초학'),

-- ===== 호흡기/기침 레시피 =====
(10, '배숙', 
  '기침을 멎게 하고 폐를 윤택하게 하는 전통 음청류',
  '[{"name": "배", "rep_code": "F002", "amount": "1개"}, {"name": "생강", "rep_code": "V004", "amount": "3쪽"}, {"name": "꿀", "rep_code": "D001", "amount": "2큰술"}, {"name": "대추", "rep_code": "F001", "amount": "3개"}]'::jsonb,
  '[{"step": 1, "instruction": "배를 8등분하여 속을 파낸다"}, {"step": 2, "instruction": "꿀, 생강, 대추를 넣고 찐다"}, {"step": 3, "instruction": "30분간 쪄서 완성"}]'::jsonb,
  10, 30, 2, 'easy',
  ARRAY['기침', '폐', '디저트'], ARRAY['snack', 'tea'],
  '량', ARRAY['감'], ARRAY['폐', '위'], '동의보감'),

(11, '도라지배즙', 
  '기관지를 보호하고 기침을 진정시키는 즙',
  '[{"name": "배", "rep_code": "F002", "amount": "2개"}, {"name": "도라지", "amount": "50g"}, {"name": "꿀", "rep_code": "D001", "amount": "2큰술"}]'::jsonb,
  '[{"step": 1, "instruction": "도라지를 썰어 쓴맛을 우린다"}, {"step": 2, "instruction": "배와 함께 즙을 낸다"}, {"step": 3, "instruction": "꿀을 넣어 마신다"}]'::jsonb,
  20, 10, 2, 'easy',
  ARRAY['기침', '가래', '폐'], ARRAY['tea', 'anytime'],
  '평', ARRAY['감', '고'], ARRAY['폐'], '전통의학'),

(12, '연근차', 
  '폐를 맑게 하고 가래를 삭이는 차',
  '[{"name": "연근", "rep_code": "V001", "amount": "100g"}, {"name": "물", "amount": "500ml"}, {"name": "꿀", "rep_code": "D001", "amount": "1큰술"}]'::jsonb,
  '[{"step": 1, "instruction": "연근을 얇게 썬다"}, {"step": 2, "instruction": "물과 함께 20분 끓인다"}, {"step": 3, "instruction": "꿀을 넣어 마신다"}]'::jsonb,
  10, 20, 2, 'easy',
  ARRAY['기침', '폐', '차'], ARRAY['tea'],
  '평', ARRAY['감'], ARRAY['심', '비', '폐'], '동의보감'),

-- ===== 냉증/혈액순환 레시피 =====
(13, '생강대추차', 
  '몸을 따뜻하게 하고 냉증을 개선하는 차',
  '[{"name": "생강", "rep_code": "V004", "amount": "20g"}, {"name": "대추", "rep_code": "F001", "amount": "10개"}, {"name": "물", "amount": "600ml"}]'::jsonb,
  '[{"step": 1, "instruction": "생강을 썰고 대추에 칼집을 낸다"}, {"step": 2, "instruction": "물과 함께 30분 끓인다"}, {"step": 3, "instruction": "따뜻하게 마신다"}]'::jsonb,
  5, 30, 2, 'easy',
  ARRAY['냉증', '혈액순환', '차'], ARRAY['tea', 'anytime'],
  '온', ARRAY['신', '감'], ARRAY['비', '위', '폐'], '동의보감'),

(14, '계피차', 
  '양기를 보하고 손발 냉증에 효과적인 차',
  '[{"name": "계피", "rep_code": "H006", "amount": "5g"}, {"name": "물", "amount": "300ml"}, {"name": "꿀", "rep_code": "D001", "amount": "1큰술"}]'::jsonb,
  '[{"step": 1, "instruction": "계피를 물에 넣고 15분 끓인다"}, {"step": 2, "instruction": "꿀을 넣어 마신다"}]'::jsonb,
  2, 15, 1, 'easy',
  ARRAY['냉증', '혈액순환', '차'], ARRAY['tea'],
  '열', ARRAY['신', '감'], ARRAY['신', '비', '간'], '동의보감'),

(15, '당귀차', 
  '혈액순환을 돕고 냉증을 개선하는 여성 보양차',
  '[{"name": "당귀", "rep_code": "H004", "amount": "10g"}, {"name": "대추", "rep_code": "F001", "amount": "5개"}, {"name": "물", "amount": "500ml"}]'::jsonb,
  '[{"step": 1, "instruction": "당귀와 대추를 깨끗이 씻는다"}, {"step": 2, "instruction": "물과 함께 30분 끓인다"}, {"step": 3, "instruction": "따뜻하게 마신다"}]'::jsonb,
  5, 30, 2, 'easy',
  ARRAY['냉증', '여성', '혈액순환', '차'], ARRAY['tea'],
  '온', ARRAY['감', '신'], ARRAY['심', '간', '비'], '동의보감'),

-- ===== 두통/머리 맑음 레시피 =====
(16, '국화차', 
  '머리를 맑게 하고 두통을 완화하는 차',
  '[{"name": "국화", "rep_code": "H012", "amount": "5g"}, {"name": "물", "amount": "300ml"}]'::jsonb,
  '[{"step": 1, "instruction": "국화를 뜨거운 물에 우린다"}, {"step": 2, "instruction": "3-5분 우려 마신다"}]'::jsonb,
  2, 5, 1, 'easy',
  ARRAY['두통', '눈', '차'], ARRAY['tea', 'anytime'],
  '량', ARRAY['고', '감'], ARRAY['폐', '간'], '동의보감'),

(17, '결명자차', 
  '눈과 머리를 맑게 하는 해열 청간 차',
  '[{"name": "결명자", "rep_code": "H011", "amount": "10g"}, {"name": "물", "amount": "500ml"}]'::jsonb,
  '[{"step": 1, "instruction": "결명자를 볶아 향을 낸다"}, {"step": 2, "instruction": "물과 함께 10분 끓인다"}, {"step": 3, "instruction": "따뜻하게 또는 차갑게 마신다"}]'::jsonb,
  5, 10, 2, 'easy',
  ARRAY['두통', '눈', '변비', '차'], ARRAY['tea'],
  '량', ARRAY['고', '감'], ARRAY['간', '신'], '본초학'),

-- ===== 변비/장건강 레시피 =====
(18, '흑임자죽', 
  '장을 윤활하게 하여 변비에 좋은 죽',
  '[{"name": "참깨(흑임자)", "rep_code": "D006", "amount": "50g"}, {"name": "쌀", "amount": "1컵"}, {"name": "물", "amount": "6컵"}]'::jsonb,
  '[{"step": 1, "instruction": "흑임자를 갈아 준비한다"}, {"step": 2, "instruction": "쌀죽을 끓이다가 흑임자를 넣는다"}, {"step": 3, "instruction": "소금이나 꿀로 간한다"}]'::jsonb,
  10, 40, 2, 'easy',
  ARRAY['변비', '장', '죽'], ARRAY['breakfast'],
  '평', ARRAY['감'], ARRAY['간', '신', '대장'], '동의보감'),

(19, '현미밥', 
  '식이섬유가 풍부하여 장운동을 돕는 밥',
  '[{"name": "현미", "rep_code": "G005", "amount": "2컵"}, {"name": "물", "amount": "적당량"}]'::jsonb,
  '[{"step": 1, "instruction": "현미를 6시간 이상 불린다"}, {"step": 2, "instruction": "압력솥에서 밥을 짓는다"}]'::jsonb,
  360, 30, 4, 'easy',
  ARRAY['변비', '다이어트', '밥'], ARRAY['lunch', 'dinner'],
  '평', ARRAY['감'], ARRAY['비', '대장'], '현대영양학'),

-- ===== 부종/이뇨 레시피 =====
(20, '율무차', 
  '이뇨작용으로 부종을 빼는 차',
  '[{"name": "율무", "rep_code": "G001", "amount": "30g"}, {"name": "물", "amount": "500ml"}]'::jsonb,
  '[{"step": 1, "instruction": "율무를 볶아 향을 낸다"}, {"step": 2, "instruction": "물과 함께 20분 끓인다"}]'::jsonb,
  5, 20, 2, 'easy',
  ARRAY['부종', '다이어트', '차'], ARRAY['tea'],
  '량', ARRAY['감'], ARRAY['비', '폐', '신'], '동의보감'),

(21, '팥죽', 
  '부종을 빼고 해독하는 전통 죽',
  '[{"name": "팥", "rep_code": "G003", "amount": "1컵"}, {"name": "쌀", "amount": "1/2컵"}, {"name": "물", "amount": "8컵"}]'::jsonb,
  '[{"step": 1, "instruction": "팥을 삶아 껍질을 제거한다"}, {"step": 2, "instruction": "팥물에 쌀을 넣고 죽을 끓인다"}, {"step": 3, "instruction": "소금으로 간한다"}]'::jsonb,
  30, 60, 4, 'medium',
  ARRAY['부종', '해독', '죽'], ARRAY['breakfast', 'snack'],
  '평', ARRAY['감'], ARRAY['심', '소장'], '동의보감'),

-- ===== 면역/감기 레시피 =====
(22, '대추생강차', 
  '감기 예방과 면역력 강화에 좋은 차',
  '[{"name": "대추", "rep_code": "F001", "amount": "10개"}, {"name": "생강", "rep_code": "V004", "amount": "20g"}, {"name": "꿀", "rep_code": "D001", "amount": "1큰술"}]'::jsonb,
  '[{"step": 1, "instruction": "대추와 생강을 썰어 물에 넣는다"}, {"step": 2, "instruction": "30분간 약불에서 끓인다"}, {"step": 3, "instruction": "꿀을 넣어 따뜻하게 마신다"}]'::jsonb,
  5, 30, 2, 'easy',
  ARRAY['면역', '감기', '차'], ARRAY['tea', 'anytime'],
  '온', ARRAY['감', '신'], ARRAY['비', '폐'], '전통의학'),

(23, '오미자차', 
  '면역력을 높이고 피로를 풀어주는 차',
  '[{"name": "오미자", "rep_code": "H005", "amount": "20g"}, {"name": "물", "amount": "500ml"}, {"name": "꿀", "rep_code": "D001", "amount": "1큰술"}]'::jsonb,
  '[{"step": 1, "instruction": "오미자를 하룻밤 찬물에 우린다"}, {"step": 2, "instruction": "체에 걸러 꿀을 넣는다"}, {"step": 3, "instruction": "차갑게 또는 따뜻하게 마신다"}]'::jsonb,
  480, 5, 4, 'easy',
  ARRAY['면역', '피로', '차'], ARRAY['tea'],
  '온', ARRAY['산', '감', '고', '신', '함'], ARRAY['폐', '신', '심'], '동의보감')

ON CONFLICT (id) DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  ingredients = EXCLUDED.ingredients,
  steps = EXCLUDED.steps,
  prep_time_min = EXCLUDED.prep_time_min,
  cook_time_min = EXCLUDED.cook_time_min,
  servings = EXCLUDED.servings,
  difficulty = EXCLUDED.difficulty,
  tags = EXCLUDED.tags,
  meal_type = EXCLUDED.meal_type,
  nature = EXCLUDED.nature,
  flavor = EXCLUDED.flavor,
  target_organs = EXCLUDED.target_organs,
  source_ref = EXCLUDED.source_ref,
  updated_at = now();

-- ID 시퀀스 재설정
SELECT setval('recipes_id_seq', (SELECT MAX(id) FROM recipes));

-- -----------------------------------------------
-- 4. 증상-레시피 매핑 시드 데이터
-- -----------------------------------------------
INSERT INTO symptom_recipe_map (symptom_id, recipe_id, meal_slot, priority, rationale_ko, best_time, frequency)

-- ===== 불면 (不眠) → 레시피 매핑 =====
SELECT d.id, 1, 'tea', 95, '대추차는 심신을 안정시켜 숙면에 도움됩니다', '취침 1시간 전', 'daily'
FROM disease_master d WHERE d.disease = '不眠'
UNION ALL
SELECT d.id, 2, 'dinner', 90, '연자죽은 마음을 편안하게 하여 불면에 좋습니다', '저녁 식사', 'daily'
FROM disease_master d WHERE d.disease = '不眠'
UNION ALL
SELECT d.id, 3, 'dinner', 85, '상추의 락투신 성분이 수면을 유도합니다', '저녁 식사', 'daily'
FROM disease_master d WHERE d.disease = '不眠'

-- ===== 소화불량 (消化不良) → 레시피 매핑 =====
UNION ALL
SELECT d.id, 4, 'tea', 95, '생강차는 위장을 따뜻하게 하여 소화를 촉진합니다', '식후 30분', 'daily'
FROM disease_master d WHERE d.disease = '消化不良'
UNION ALL
SELECT d.id, 5, 'anytime', 88, '무생채는 소화효소가 풍부하여 체한 것을 풀어줍니다', '식사 시', 'daily'
FROM disease_master d WHERE d.disease = '消化不良'
UNION ALL
SELECT d.id, 6, 'tea', 85, '매실차는 식욕을 돋우고 소화를 도웁니다', '식전 또는 식후', 'daily'
FROM disease_master d WHERE d.disease = '消化不良'

-- ===== 피로/권태 (倦怠) → 레시피 매핑 =====
UNION ALL
SELECT d.id, 7, 'lunch', 98, '삼계탕은 기력을 보충하는 대표 보양식입니다', '점심 또는 저녁', 'weekly'
FROM disease_master d WHERE d.disease = '倦怠'
UNION ALL
SELECT d.id, 8, 'lunch', 95, '황기삼계탕은 만성 피로에 더욱 효과적입니다', '점심 또는 저녁', 'weekly'
FROM disease_master d WHERE d.disease = '倦怠'
UNION ALL
SELECT d.id, 9, 'anytime', 85, '검정콩밥은 신장을 보하여 체력을 강화합니다', '매 식사', 'daily'
FROM disease_master d WHERE d.disease = '倦怠'
UNION ALL
SELECT d.id, 23, 'tea', 80, '오미자차는 피로 회복에 좋습니다', '오후', 'daily'
FROM disease_master d WHERE d.disease = '倦怠'

-- ===== 기침 (咳嗽) → 레시피 매핑 =====
UNION ALL
SELECT d.id, 10, 'snack', 95, '배숙은 기침을 멎게 하고 폐를 윤택하게 합니다', '증상 시', 'daily'
FROM disease_master d WHERE d.disease = '咳嗽'
UNION ALL
SELECT d.id, 11, 'tea', 92, '도라지배즙은 기관지를 보호합니다', '아침 저녁', 'daily'
FROM disease_master d WHERE d.disease = '咳嗽'
UNION ALL
SELECT d.id, 12, 'tea', 85, '연근차는 폐를 맑게 하고 가래를 삭입니다', '수시', 'daily'
FROM disease_master d WHERE d.disease = '咳嗽'

-- ===== 수족냉증 (手足冷) → 레시피 매핑 =====
UNION ALL
SELECT d.id, 13, 'tea', 95, '생강대추차는 몸을 따뜻하게 합니다', '아침 저녁', 'daily'
FROM disease_master d WHERE d.disease = '手足冷'
UNION ALL
SELECT d.id, 14, 'tea', 90, '계피차는 양기를 보하여 냉증을 개선합니다', '오후', 'daily'
FROM disease_master d WHERE d.disease = '手足冷'
UNION ALL
SELECT d.id, 15, 'tea', 88, '당귀차는 혈액순환을 도와 냉증에 좋습니다', '오후', 'daily'
FROM disease_master d WHERE d.disease = '手足冷'

-- ===== 두통 (頭痛) → 레시피 매핑 =====
UNION ALL
SELECT d.id, 16, 'tea', 92, '국화차는 머리를 맑게 하고 두통을 완화합니다', '증상 시', 'daily'
FROM disease_master d WHERE d.disease = '頭痛'
UNION ALL
SELECT d.id, 17, 'tea', 88, '결명자차는 눈과 머리를 맑게 합니다', '오후', 'daily'
FROM disease_master d WHERE d.disease = '頭痛'

-- ===== 변비 (便秘) → 레시피 매핑 =====
UNION ALL
SELECT d.id, 18, 'breakfast', 92, '흑임자죽은 장을 윤활하게 하여 변비에 좋습니다', '아침', 'daily'
FROM disease_master d WHERE d.disease = '便秘'
UNION ALL
SELECT d.id, 19, 'anytime', 90, '현미밥의 식이섬유가 장운동을 돕습니다', '매 식사', 'daily'
FROM disease_master d WHERE d.disease = '便秘'
UNION ALL
SELECT d.id, 17, 'tea', 85, '결명자차는 장을 청소하여 변비에 도움됩니다', '아침', 'daily'
FROM disease_master d WHERE d.disease = '便秘'

-- ===== 부종 (浮腫) → 레시피 매핑 =====
UNION ALL
SELECT d.id, 20, 'tea', 95, '율무차의 이뇨작용이 부종을 빼줍니다', '오전', 'daily'
FROM disease_master d WHERE d.disease = '浮腫'
UNION ALL
SELECT d.id, 21, 'breakfast', 90, '팥죽은 부종을 빼는 대표적인 음식입니다', '아침', 'weekly'
FROM disease_master d WHERE d.disease = '浮腫'

-- ===== 감기 (感冒) → 레시피 매핑 =====
UNION ALL
SELECT d.id, 22, 'tea', 95, '대추생강차는 감기 초기에 효과적입니다', '수시', 'daily'
FROM disease_master d WHERE d.disease = '感冒'
UNION ALL
SELECT d.id, 4, 'tea', 90, '생강차는 몸을 따뜻하게 하여 감기에 좋습니다', '수시', 'daily'
FROM disease_master d WHERE d.disease = '感冒'

ON CONFLICT (symptom_id, recipe_id) DO UPDATE SET
  meal_slot = EXCLUDED.meal_slot,
  priority = EXCLUDED.priority,
  rationale_ko = EXCLUDED.rationale_ko,
  best_time = EXCLUDED.best_time,
  frequency = EXCLUDED.frequency,
  updated_at = now();

-- -----------------------------------------------
-- 5. 조회용 뷰
-- -----------------------------------------------
CREATE OR REPLACE VIEW v_symptom_recipe_recommendations AS
SELECT 
  d.disease,
  d.modern_name_ko AS symptom_ko,
  r.title AS recipe_title,
  r.description AS recipe_desc,
  r.tags AS recipe_tags,
  m.meal_slot,
  m.priority,
  m.rationale_ko,
  m.best_time,
  m.frequency
FROM symptom_recipe_map m
JOIN disease_master d ON m.symptom_id = d.id
JOIN recipes r ON m.recipe_id = r.id
ORDER BY d.category, d.disease, m.priority DESC;
