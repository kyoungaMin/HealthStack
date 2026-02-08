-- =============================================
-- Seed Data: Chronic Diseases (만성질환 마스터)
-- Date: 2026-02-08
-- Description: 고혈압, 당뇨, 고지혈증 등 만성질환 추가
-- =============================================

INSERT INTO disease_master (disease, disease_read, disease_alias, modern_disease, modern_name_ko, name_en, icd10_code, category, aliases) VALUES

-- ===== 대사/만성 질환 (Metabolic/Chronic) =====
('高血壓', '고혈압', '風眩', '고혈압', '고혈압', 'Hypertension', 'I10', '순환', ARRAY['혈압 높음', '혈압 상승', 'High Blood Pressure']),
('糖尿病', '당뇨병', '消渴', '당뇨병', '당뇨', 'Diabetes Mellitus', 'E11', '대사', ARRAY['당뇨', '혈당 높음', 'Diabetes']),
('高脂血症', '고지혈증', NULL, '이상지질혈증', '고지혈증', 'Dyslipidemia', 'E78', '대사', ARRAY['콜레스테롤 높음', '중성지방', 'Hyperlipidemia']),
('肥滿', '비만', NULL, '비만', '비만', 'Obesity', 'E66', '대사', ARRAY['과체중', '살찜', 'Overweight'])

ON CONFLICT (disease) DO UPDATE SET
  disease_read = EXCLUDED.disease_read,
  disease_alias = EXCLUDED.disease_alias,
  modern_disease = EXCLUDED.modern_disease,
  modern_name_ko = EXCLUDED.modern_name_ko,
  name_en = EXCLUDED.name_en,
  icd10_code = EXCLUDED.icd10_code,
  category = EXCLUDED.category,
  aliases = EXCLUDED.aliases,
  updated_at = now();

-- -----------------------------------------------
-- 식재료 매핑 추가 (symptom_ingredient_map)
-- -----------------------------------------------
-- 고혈압 (高血壓)
INSERT INTO symptom_ingredient_map (symptom_id, rep_code, direction, rationale_ko, priority, source_ref, evidence_level)
SELECT d.id, 'V001', 'recommend', '연근은 혈압 조절에 도움을 줄 수 있습니다', 85, '전통의학', 'empirical'
FROM disease_master d WHERE d.disease = '高血壓'
ON CONFLICT (symptom_id, rep_code) DO NOTHING;

INSERT INTO symptom_ingredient_map (symptom_id, rep_code, direction, rationale_ko, priority, source_ref, evidence_level)
SELECT d.id, 'G008', 'good', '메밀은 루틴 성분이 있어 혈관 건강에 좋습니다', 90, '본초학', 'traditional'
FROM disease_master d WHERE d.disease = '高血壓'
ON CONFLICT (symptom_id, rep_code) DO NOTHING;

-- 당뇨 (糖尿病) -> 현미, 율무
INSERT INTO symptom_ingredient_map (symptom_id, rep_code, direction, rationale_ko, priority, source_ref, evidence_level)
SELECT d.id, 'G005', 'recommend', '현미는 혈당 상승을 완만하게 돕습니다', 95, '현대영양학', 'clinical'
FROM disease_master d WHERE d.disease = '糖尿病'
ON CONFLICT (symptom_id, rep_code) DO NOTHING;

INSERT INTO symptom_ingredient_map (symptom_id, rep_code, direction, rationale_ko, priority, source_ref, evidence_level)
SELECT d.id, 'G001', 'good', '율무는 인슐린 저항성을 개선하는 데 도움될 수 있습니다', 85, '현대연구', 'clinical'
FROM disease_master d WHERE d.disease = '糖尿病'
ON CONFLICT (symptom_id, rep_code) DO NOTHING;
