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
