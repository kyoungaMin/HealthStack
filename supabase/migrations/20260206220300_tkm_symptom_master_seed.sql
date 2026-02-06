-- =============================================
-- Migration: Create TKM Symptom Master Table + Seed Data
-- Date: 2026-02-06
-- Description: 동의보감 증상 마스터 테이블 생성 및 시드 데이터
-- =============================================

-- -----------------------------------------------
-- 1. tkm_symptom_master 테이블 생성
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS tkm_symptom_master (
  id bigserial PRIMARY KEY,
  
  tkm_code text UNIQUE,
  hanja text,
  korean text NOT NULL,
  name_en text,
  aliases text[] DEFAULT '{}',
  description text,
  
  category text,
  pattern_tags text[] DEFAULT '{}',
  
  source_book text DEFAULT '동의보감',
  source_ref text,
  
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- 인덱스 생성 (테이블이 이미 존재할 경우 컬럼 추가)
ALTER TABLE tkm_symptom_master ADD COLUMN IF NOT EXISTS name_en text;

CREATE INDEX IF NOT EXISTS idx_tkm_symptom_master_category ON tkm_symptom_master(category);
CREATE INDEX IF NOT EXISTS idx_tkm_symptom_master_name_en ON tkm_symptom_master(name_en);
CREATE INDEX IF NOT EXISTS idx_tkm_symptom_master_korean ON tkm_symptom_master(korean);
CREATE INDEX IF NOT EXISTS idx_tkm_symptom_master_tags ON tkm_symptom_master USING GIN(pattern_tags);
CREATE INDEX IF NOT EXISTS idx_tkm_symptom_master_aliases ON tkm_symptom_master USING GIN(aliases);

-- 컬럼 코멘트
COMMENT ON TABLE tkm_symptom_master IS '동의보감 기반 전통 한의학(TKM) 증상 마스터';
COMMENT ON COLUMN tkm_symptom_master.tkm_code IS '내부 코드';
COMMENT ON COLUMN tkm_symptom_master.hanja IS '한자 표기 (예: 不眠)';
COMMENT ON COLUMN tkm_symptom_master.korean IS '한글 표기 (예: 불면)';
COMMENT ON COLUMN tkm_symptom_master.name_en IS '영문명 (예: Insomnia)';
COMMENT ON COLUMN tkm_symptom_master.category IS '분류 (수면/소화/호흡/순환/피부/정신/통증 등)';
COMMENT ON COLUMN tkm_symptom_master.pattern_tags IS '한의학 패턴 (寒/熱/虛/實/痰/瘀血 등)';
COMMENT ON COLUMN tkm_symptom_master.source_book IS '출처 (동의보감, 의학입문 등)';
COMMENT ON COLUMN tkm_symptom_master.source_ref IS '권/편/문장/페이지';

-- 트리거 (updated_at 자동 갱신)
DROP TRIGGER IF EXISTS update_tkm_symptom_master_updated_at ON tkm_symptom_master;
CREATE TRIGGER update_tkm_symptom_master_updated_at
    BEFORE UPDATE ON tkm_symptom_master
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------
-- 2. 시드 데이터 삽입
-- -----------------------------------------------

INSERT INTO tkm_symptom_master (tkm_code, hanja, korean, name_en, aliases, description, category, pattern_tags, source_book, source_ref) VALUES

-- ===== 수면 장애 (Sleep Disorders) =====
('TKM-SL-001', '不眠', '불면', 'Insomnia', 
  ARRAY['失眠', '不得眠', '不得臥', '목불면', '잠 못 이룸'], 
  '밤에 잠들지 못하거나 잠이 들어도 쉽게 깨는 증상', 
  '수면', ARRAY['心火', '陰虛', '血虛'], '동의보감', '내경편 권3 몽'),

('TKM-SL-002', '心煩不得眠', '심번불득면', 'Insomnia with Restlessness',
  ARRAY['심번불면', '가슴 답답해 잠 못 잠'],
  '마음이 번거롭고 불안하여 잠들지 못함',
  '수면', ARRAY['心火', '熱'], '동의보감', '내경편 권3'),

('TKM-SL-003', '多夢', '다몽', 'Excessive Dreaming',
  ARRAY['夢多', '꿈 많음', '꿈 자주 꿈'],
  '잠을 자도 꿈을 많이 꾸어 숙면하지 못함',
  '수면', ARRAY['心血虛', '痰火'], '동의보감', '내경편 권3 몽'),

('TKM-SL-004', '嗜睡', '기수', 'Hypersomnia',
  ARRAY['多睡', '過睡', '졸음', '항상 졸림'],
  '항상 졸리고 잠이 많은 증상',
  '수면', ARRAY['脾虛', '濕痰'], '동의보감', '내경편'),

-- ===== 소화기 장애 (Digestive Disorders) =====
('TKM-DG-001', '食滯', '식체', 'Food Stagnation',
  ARRAY['積滯', '체함', '소화 안됨', '밥이 안 내려감'],
  '음식이 소화되지 않고 체한 상태',
  '소화', ARRAY['脾虛', '食積', '濕'], '동의보감', '내경편 권4'),

('TKM-DG-002', '不欲食', '불욕식', 'Loss of Appetite',
  ARRAY['食慾不振', '納呆', '밥맛 없음', '입맛 없음'],
  '음식을 먹고 싶지 않은 증상',
  '소화', ARRAY['脾胃虛弱', '濕困'], '동의보감', '내경편'),

('TKM-DG-003', '腹脹', '복창', 'Abdominal Distension',
  ARRAY['腹滿', '배 부름', '가스 참', '腸鳴'],
  '배가 부르고 팽창한 느낌',
  '소화', ARRAY['脾虛', '氣滯', '濕'], '동의보감', '잡병편'),

('TKM-DG-004', '泄瀉', '설사', 'Diarrhea',
  ARRAY['下利', '洩瀉', '묽은 변', '水瀉'],
  '대변이 묽거나 물처럼 나오는 증상',
  '소화', ARRAY['脾虛', '寒濕', '濕熱'], '동의보감', '잡병편 권6'),

('TKM-DG-005', '便秘', '변비', 'Constipation',
  ARRAY['大便秘結', '大便難', '大便燥結', '배변 곤란'],
  '대변이 굳어 나오지 않는 증상',
  '소화', ARRAY['陰虛', '血虛', '熱結'], '동의보감', '내경편'),

('TKM-DG-006', '噯氣', '애기', 'Belching',
  ARRAY['噫氣', '트림', '가스 올라옴'],
  '위에서 가스가 올라와 트림이 나는 증상',
  '소화', ARRAY['脾胃虛', '氣滯'], '동의보감', '내경편'),

('TKM-DG-007', '胃脘痛', '위완통', 'Epigastric Pain',
  ARRAY['胃痛', '心下痛', '명치 아픔', '위통'],
  '명치 부위가 아픈 증상',
  '소화', ARRAY['寒', '氣滯', '瘀血'], '동의보감', '잡병편'),

('TKM-DG-008', '嘔吐', '구토', 'Vomiting',
  ARRAY['吐', '嘔', '토함', '欲吐'],
  '위의 내용물을 토해내는 증상',
  '소화', ARRAY['痰飮', '胃熱', '寒'], '동의보감', '잡병편'),

-- ===== 피로/허약 (Fatigue/Weakness) =====
('TKM-FT-001', '虛勞', '허로', 'Consumptive Disease',
  ARRAY['虛損', '勞傷', '몸이 약함', '만성 피로'],
  '기혈이 부족하여 몸이 쇠약해진 상태',
  '피로', ARRAY['氣虛', '血虛', '陰虛', '陽虛'], '동의보감', '잡병편 권6'),

('TKM-FT-002', '氣虛', '기허', 'Qi Deficiency',
  ARRAY['氣弱', '기운 없음', '무기력'],
  '기가 허하여 힘이 없고 피곤한 상태',
  '피로', ARRAY['虛'], '동의보감', '내경편'),

('TKM-FT-003', '自汗', '자한', 'Spontaneous Sweating',
  ARRAY['汗出', '식은땀', '자연 발한'],
  '활동하지 않아도 저절로 땀이 나는 증상',
  '피로', ARRAY['氣虛', '陽虛', '表虛'], '동의보감', '내경편 권2'),

('TKM-FT-004', '盜汗', '도한', 'Night Sweats',
  ARRAY['寢汗', '잘 때 땀', '수면 중 발한'],
  '잠을 자는 동안 땀이 나는 증상',
  '피로', ARRAY['陰虛'], '동의보감', '내경편 권2'),

-- ===== 호흡기 장애 (Respiratory Disorders) =====
('TKM-RS-001', '咳嗽', '해수', 'Cough',
  ARRAY['咳', '嗽', '기침'],
  '기침이 나는 증상',
  '호흡', ARRAY['風寒', '風熱', '痰濕', '陰虛'], '동의보감', '잡병편 권4'),

('TKM-RS-002', '痰飮', '담음', 'Phlegm',
  ARRAY['痰', '가래', '담'],
  '기도에 가래가 끼는 증상',
  '호흡', ARRAY['濕痰', '寒痰', '熱痰'], '동의보감', '잡병편 권5'),

('TKM-RS-003', '喘息', '천식', 'Asthma',
  ARRAY['喘', '哮', '숨참', '호흡곤란'],
  '숨이 차고 가쁜 증상',
  '호흡', ARRAY['肺虛', '痰飮', '腎虛'], '동의보감', '잡병편 권4'),

('TKM-RS-004', '咽喉痛', '인후통', 'Sore Throat',
  ARRAY['喉痛', '咽痛', '목 아픔'],
  '목구멍이 아픈 증상',
  '호흡', ARRAY['熱', '風熱', '陰虛'], '동의보감', '외형편'),

-- ===== 순환계 장애 (Circulatory Disorders) =====
('TKM-CR-001', '頭痛', '두통', 'Headache',
  ARRAY['頭疾', '머리 아픔', '편두통'],
  '머리가 아픈 증상',
  '순환', ARRAY['風', '火', '痰', '瘀血', '氣虛', '血虛'], '동의보감', '외형편 권1'),

('TKM-CR-002', '眩暈', '현훈', 'Dizziness',
  ARRAY['眩冒', '頭暈', '어지러움', '현기증'],
  '머리가 어지럽고 눈앞이 캄캄한 증상',
  '순환', ARRAY['肝陽', '痰濕', '氣血虛'], '동의보감', '외형편 권1'),

('TKM-CR-003', '手足冷', '수족냉', 'Cold Extremities',
  ARRAY['手足厥冷', '四肢冷', '손발 시림'],
  '손발이 차가운 증상',
  '순환', ARRAY['陽虛', '血虛', '寒'], '동의보감', '내경편'),

('TKM-CR-004', '心悸', '심계', 'Palpitation',
  ARRAY['心動悸', '怔忡', '가슴 두근거림'],
  '가슴이 두근거리는 증상',
  '순환', ARRAY['心血虛', '心陰虛', '痰火'], '동의보감', '내경편 권3'),

-- ===== 피부 질환 (Skin Disorders) =====
('TKM-SK-001', '瘙痒', '소양', 'Pruritus',
  ARRAY['皮膚瘙痒', '가려움', '피부 가려움'],
  '피부가 가려운 증상',
  '피부', ARRAY['風', '濕', '血虛', '血熱'], '동의보감', '외형편'),

('TKM-SK-002', '濕疹', '습진', 'Eczema',
  ARRAY['濕瘡', '습진', '피부염'],
  '피부에 진물이 나고 가려운 증상',
  '피부', ARRAY['濕熱', '脾虛濕困'], '동의보감', '외형편'),

-- ===== 정신/신경 장애 (Mental/Neurological Disorders) =====
('TKM-MN-001', '心煩', '심번', 'Restlessness',
  ARRAY['煩躁', '번조', '마음 불안'],
  '마음이 번거롭고 불안한 증상',
  '정신', ARRAY['心火', '陰虛熱'], '동의보감', '내경편 권3'),

('TKM-MN-002', '健忘', '건망', 'Forgetfulness',
  ARRAY['善忘', '건망증', '기억력 감퇴'],
  '잘 잊어버리는 증상',
  '정신', ARRAY['心脾虛', '腎虛'], '동의보감', '내경편'),

('TKM-MN-003', '鬱症', '울증', 'Depression',
  ARRAY['鬱', '憂鬱', '우울', '기분 저하'],
  '기가 울체되어 우울한 상태',
  '정신', ARRAY['肝鬱', '氣滯'], '동의보감', '잡병편'),

('TKM-MN-004', '驚悸', '경계', 'Panic',
  ARRAY['驚', '驚恐', '놀람', '깜짝 놀람'],
  '쉽게 놀라고 두려워하는 증상',
  '정신', ARRAY['心膽虛', '痰'], '동의보감', '내경편 권3'),

-- ===== 통증 (Pain) =====
('TKM-PN-001', '腰痛', '요통', 'Low Back Pain',
  ARRAY['腰脊痛', '허리 아픔', '요추통'],
  '허리가 아픈 증상',
  '통증', ARRAY['腎虛', '寒濕', '瘀血'], '동의보감', '외형편 권4'),

('TKM-PN-002', '關節痛', '관절통', 'Joint Pain',
  ARRAY['痹症', '마디 아픔', '관절염'],
  '관절이 아픈 증상',
  '통증', ARRAY['風寒濕', '瘀血'], '동의보감', '잡병편'),

('TKM-PN-003', '痺症', '비증', 'Bi Syndrome',
  ARRAY['痹', '저림', '마비감'],
  '사지가 저리거나 마비되는 증상',
  '통증', ARRAY['風', '寒', '濕'], '동의보감', '잡병편 권3'),

-- ===== 여성 건강 (Women Health) =====
('TKM-WM-001', '月經不調', '월경불조', 'Menstrual Irregularity',
  ARRAY['經期不順', '생리 불순', '월경 이상'],
  '월경 주기가 불규칙한 증상',
  '여성', ARRAY['血虛', '氣滯', '寒凝'], '동의보감', '잡병편 권9'),

('TKM-WM-002', '痛經', '통경', 'Dysmenorrhea',
  ARRAY['經行腹痛', '생리통', '월경통'],
  '월경 시 통증이 있는 증상',
  '여성', ARRAY['寒凝', '氣滯', '瘀血'], '동의보감', '잡병편 권9'),

-- ===== 비뇨기 (Urinary) =====
('TKM-UR-001', '小便頻數', '소변빈삭', 'Frequent Urination',
  ARRAY['頻尿', '잦은 소변', '화장실 자주'],
  '소변을 자주 보는 증상',
  '비뇨', ARRAY['腎虛', '濕熱'], '동의보감', '내경편'),

('TKM-UR-002', '水腫', '수종', 'Edema',
  ARRAY['浮腫', '부종', '붓기'],
  '몸이 붓는 증상',
  '비뇨', ARRAY['脾虛', '腎虛', '水濕'], '동의보감', '잡병편 권7')

ON CONFLICT (tkm_code) DO UPDATE SET
  hanja = EXCLUDED.hanja,
  korean = EXCLUDED.korean,
  name_en = EXCLUDED.name_en,
  aliases = EXCLUDED.aliases,
  description = EXCLUDED.description,
  category = EXCLUDED.category,
  pattern_tags = EXCLUDED.pattern_tags,
  source_book = EXCLUDED.source_book,
  source_ref = EXCLUDED.source_ref,
  updated_at = now();
