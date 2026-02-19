-- =========================
-- 1. Disease Master (증상/질병)
-- =========================

-- disease_master (unique by disease name)
INSERT INTO public.disease_master (
    disease, 
    disease_read, 
    disease_alias, 
    disease_alias_read, 
    modern_disease, 
    category
)
SELECT DISTINCT 
    disease, 
    MAX(disease_read) as disease_read, 
    MAX(disease_alias) as disease_alias, 
    MAX(disease_alias_read) as disease_alias_read, 
    MAX(modern_disease) as modern_disease,
    MAX(disease_src) as category -- Using source book section as category proxy for now
FROM public.traditional_foods
WHERE disease IS NOT NULL AND disease != ''
GROUP BY disease
ON CONFLICT (disease) DO NOTHING;


-- =========================
-- 2. Foods Master (식재료)
-- =========================

-- foods_master (unique by rep_code)
INSERT INTO public.foods_master (
    rep_code, 
    rep_name, 
    modern_name, 
    category
)
SELECT DISTINCT 
    rep_code, 
    MAX(rep_name) as rep_name, 
    MAX(trad_name) as modern_name, -- Use trad_name as modern name initially
    MAX(food_type) as category
FROM public.traditional_foods
WHERE rep_code IS NOT NULL AND rep_code != ''
GROUP BY rep_code
ON CONFLICT (rep_code) DO NOTHING;


-- =========================
-- 3. TKM Symptom Master (동의보감 고유 증상)
-- =========================

INSERT INTO public.tkm_symptom_master (
    korean, 
    hanja, 
    description, 
    source_book, 
    source_ref
)
SELECT DISTINCT 
    disease_read as korean, 
    disease as hanja, 
    MAX(disease_content) as description, 
    '동의보감' as source_book, 
    MAX(disease_src) || ' ' || MAX(disease_src_section) as source_ref
FROM public.traditional_foods
WHERE disease IS NOT NULL AND disease != ''
GROUP BY disease, disease_read
ON CONFLICT (tkm_code) DO NOTHING; 
-- Note: tkm_code is unique but not populated here. We might need to generate it or use disease as key.
-- For now, let's skip conflict handling on tkm_code as it's null, or generate a code.
-- Let's use disease name as key for now if tkm_code is null logic permits.
-- Actually tkm_code is unique, so inserting NULLs will work only if it's not the conflict target or we generate one.
-- Let's update tkm_symptom_master schema to allow null tkm_code or generate it.
-- For this step, we will rely on serial ID and ignore tkm_code (let it be null).


-- =========================
-- 4. Symptom-Ingredient Map (효능 매핑)
-- =========================

-- Map symptoms to ingredients based on indication
INSERT INTO public.symptom_ingredient_map (
    symptom_id, 
    rep_code, 
    direction, 
    rationale_ko,
    source_ref
)
SELECT 
    dm.id as symptom_id,
    tf.rep_code,
    'recommend' as direction,
    tf.indication as rationale_ko,
    tf.prescription as source_ref
FROM public.traditional_foods tf
JOIN public.disease_master dm ON tf.disease = dm.disease
WHERE tf.rep_code IS NOT NULL AND tf.disease IS NOT NULL
ON CONFLICT (symptom_id, rep_code) DO NOTHING;
