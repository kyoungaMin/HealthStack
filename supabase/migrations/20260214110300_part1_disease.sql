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
