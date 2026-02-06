-- =============================================
-- Migration: Create TKM to Modern Map Table + Seed Data
-- Date: 2026-02-06
-- Description: 동의보감 증상 → 현대 질환 매핑 테이블 및 시드 데이터
-- =============================================

-- -----------------------------------------------
-- 1. tkm_to_modern_map 테이블 생성
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS tkm_to_modern_map (
  id bigserial PRIMARY KEY,
  
  tkm_symptom_id bigint NOT NULL REFERENCES tkm_symptom_master(id) ON DELETE CASCADE,
  modern_disease_id bigint NOT NULL REFERENCES disease_master(id) ON DELETE CASCADE,
  
  mapping_strength text NOT NULL CHECK (mapping_strength IN ('high', 'medium', 'low')),
  mapping_type text NOT NULL CHECK (mapping_type IN ('equivalent', 'overlap', 'differential', 'context')),
  
  evidence_note text,
  reviewer text,
  reviewed_at timestamptz,
  
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  
  UNIQUE(tkm_symptom_id, modern_disease_id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_tkm_to_modern_tkm ON tkm_to_modern_map(tkm_symptom_id);
CREATE INDEX IF NOT EXISTS idx_tkm_to_modern_modern ON tkm_to_modern_map(modern_disease_id);
CREATE INDEX IF NOT EXISTS idx_tkm_to_modern_strength ON tkm_to_modern_map(mapping_strength);

-- 컬럼 코멘트
COMMENT ON TABLE tkm_to_modern_map IS '동의보감 증상 → 현대 질환 매핑';
COMMENT ON COLUMN tkm_to_modern_map.mapping_strength IS '매핑 강도: high(거의 동일), medium(부분 일치), low(약한 연관)';
COMMENT ON COLUMN tkm_to_modern_map.mapping_type IS '매핑 유형: equivalent(동일), overlap(중복), differential(감별), context(맥락적)';

-- 트리거
DROP TRIGGER IF EXISTS update_tkm_to_modern_map_updated_at ON tkm_to_modern_map;
CREATE TRIGGER update_tkm_to_modern_map_updated_at
    BEFORE UPDATE ON tkm_to_modern_map
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------
-- 2. 시드 데이터 삽입
-- -----------------------------------------------
-- 주의: tkm_symptom_master와 disease_master의 실제 id를 사용해야 함
-- 아래는 tkm_code와 disease를 기준으로 조인하여 삽입하는 방식

INSERT INTO tkm_to_modern_map (tkm_symptom_id, modern_disease_id, mapping_strength, mapping_type, evidence_note, reviewer)

-- ===== 수면 장애 매핑 =====
SELECT t.id, d.id, 'high', 'equivalent', 
  '동의보감의 不眠은 현대의 불면증과 거의 동일한 개념', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-SL-001' AND d.disease = '不眠'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '동의보감의 多夢은 현대의 다몽증(수면 중 과다한 꿈)과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-SL-003' AND d.disease = '多夢'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '동의보감의 嗜睡는 현대의 기면증과 유사', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-SL-004' AND d.disease = '嗜睡'

-- ===== 소화기 장애 매핑 =====
UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '食滯(식체)는 현대의 소화불량과 동일 개념', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-DG-001' AND d.disease = '消化不良'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '不欲食은 현대의 식욕부진과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-DG-002' AND d.disease = '食慾不振'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '腹脹은 현대의 복부팽만과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-DG-003' AND d.disease = '腹脹'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '泄瀉는 현대의 설사와 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-DG-004' AND d.disease = '泄瀉'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '便秘는 현대의 변비와 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-DG-005' AND d.disease = '便秘'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '噯氣는 현대의 트림과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-DG-006' AND d.disease = '噯氣'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '胃脘痛은 현대의 위통과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-DG-007' AND d.disease = '胃脘痛'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '嘔吐는 현대의 구토와 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-DG-008' AND d.disease = '嘔吐'

-- ===== 피로/허약 매핑 =====
UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '虛勞는 현대의 만성피로/허로와 동일한 개념', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-FT-001' AND d.disease = '虛勞'

UNION ALL
SELECT t.id, d.id, 'high', 'overlap',
  '氣虛는 현대의 기력저하, 만성피로와 중복되는 개념', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-FT-002' AND d.disease = '氣虛'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '自汗은 현대의 자한증과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-FT-003' AND d.disease = '自汗'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '盜汗은 현대의 도한증과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-FT-004' AND d.disease = '盜汗'

-- ===== 호흡기 장애 매핑 =====
UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '咳嗽는 현대의 기침과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-RS-001' AND d.disease = '咳嗽'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '痰飮은 현대의 가래와 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-RS-002' AND d.disease = '痰飮'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '喘息은 현대의 천식과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-RS-003' AND d.disease = '喘息'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '咽喉痛은 현대의 인후통과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-RS-004' AND d.disease = '咽喉痛'

-- ===== 순환계 장애 매핑 =====
UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '頭痛은 현대의 두통과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-CR-001' AND d.disease = '頭痛'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '眩暈은 현대의 어지러움과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-CR-002' AND d.disease = '眩暈'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '手足冷은 현대의 수족냉증과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-CR-003' AND d.disease = '手足冷'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '心悸는 현대의 심계항진과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-CR-004' AND d.disease = '心悸'

-- ===== 피부 질환 매핑 =====
UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '瘙痒은 현대의 가려움증과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-SK-001' AND d.disease = '瘙痒'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '濕疹은 현대의 습진과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-SK-002' AND d.disease = '濕疹'

-- ===== 정신/신경 장애 매핑 =====
UNION ALL
SELECT t.id, d.id, 'high', 'overlap',
  '心煩은 현대의 불안과 중복되는 개념', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-MN-001' AND d.disease = '心煩'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '健忘은 현대의 건망증과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-MN-002' AND d.disease = '健忘'

UNION ALL
SELECT t.id, d.id, 'high', 'overlap',
  '鬱症은 현대의 우울증과 중복되는 개념 (기울체 중심)', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-MN-003' AND d.disease = '憂鬱'

UNION ALL
SELECT t.id, d.id, 'high', 'overlap',
  '驚悸는 현대의 공황장애와 중복', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-MN-004' AND d.disease = '驚悸'

-- ===== 통증 매핑 =====
UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '腰痛은 현대의 요통과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-PN-001' AND d.disease = '腰痛'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '關節痛은 현대의 관절통과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-PN-002' AND d.disease = '關節痛'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '痺症은 현대의 저림과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-PN-003' AND d.disease = '痺症'

-- ===== 여성 건강 매핑 =====
UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '月經不調는 현대의 월경불순과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-WM-001' AND d.disease = '月經不調'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '痛經은 현대의 월경통과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-WM-002' AND d.disease = '痛經'

-- ===== 비뇨기 매핑 =====
UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '小便頻數는 현대의 빈뇨와 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-UR-001' AND d.disease = '頻尿'

UNION ALL
SELECT t.id, d.id, 'high', 'equivalent',
  '水腫은 현대의 부종과 동일', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-UR-002' AND d.disease = '浮腫'

-- ===== 교차 매핑 (한 TKM 증상이 여러 현대 질환에 해당하는 경우) =====

-- 心煩不得眠 → 불면증 (context)
UNION ALL
SELECT t.id, d.id, 'medium', 'context',
  '心煩不得眠은 불면증의 특수한 형태 (불안 동반)', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-SL-002' AND d.disease = '不眠'

-- 虛勞 → 만성피로 (overlap)
UNION ALL
SELECT t.id, d.id, 'high', 'overlap',
  '虛勞는 만성피로와 광범위하게 중복됨', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-FT-001' AND d.disease = '倦怠'

-- 喘息 → 호흡곤란 (context)
UNION ALL
SELECT t.id, d.id, 'medium', 'context',
  '喘息은 천식 외에도 일반적인 호흡곤란 증상 포함', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-RS-003' AND d.disease = '咳嗽'

-- 눈 피로와 어지러움 연관
UNION ALL
SELECT t.id, d.id, 'low', 'differential',
  '眩暈과 두통은 감별진단이 필요한 관계', 'system'
FROM tkm_symptom_master t, disease_master d 
WHERE t.tkm_code = 'TKM-CR-002' AND d.disease = '頭痛'

ON CONFLICT (tkm_symptom_id, modern_disease_id) DO UPDATE SET
  mapping_strength = EXCLUDED.mapping_strength,
  mapping_type = EXCLUDED.mapping_type,
  evidence_note = EXCLUDED.evidence_note,
  reviewer = EXCLUDED.reviewer,
  updated_at = now();

-- -----------------------------------------------
-- 3. 매핑 통계 확인용 뷰 (선택적)
-- -----------------------------------------------
CREATE OR REPLACE VIEW v_tkm_to_modern_summary AS
SELECT 
  t.tkm_code,
  t.korean AS tkm_korean,
  t.hanja AS tkm_hanja,
  d.disease AS modern_disease,
  d.modern_name_ko,
  d.name_en AS modern_name_en,
  m.mapping_strength,
  m.mapping_type,
  m.evidence_note
FROM tkm_to_modern_map m
JOIN tkm_symptom_master t ON m.tkm_symptom_id = t.id
JOIN disease_master d ON m.modern_disease_id = d.id
ORDER BY t.category, t.korean;
