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
WHERE disease IS NOT NULL AND disease != '' AND disease_read IS NOT NULL AND disease_read != ''
GROUP BY disease, disease_read
ON CONFLICT (tkm_code) DO NOTHING;
