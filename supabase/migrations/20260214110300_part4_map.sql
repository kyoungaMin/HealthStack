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
