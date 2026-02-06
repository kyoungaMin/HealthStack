-- =============================================
-- Seed Data: disease_master (질환/증상 마스터)
-- Date: 2026-02-06
-- Description: 동의보감 기반 주요 증상 + 현대명/영문명/ICD-10 매핑
-- =============================================

-- UPSERT 방식: disease 기준으로 존재하면 UPDATE, 없으면 INSERT

INSERT INTO disease_master (disease, disease_read, disease_alias, modern_disease, modern_name_ko, name_en, icd10_code, category, aliases) VALUES

-- ===== 수면 장애 (Sleep Disorders) =====
('不眠', '불면', '失眠', '불면증', '불면증', 'Insomnia', 'G47.0', '수면', ARRAY['잠 못 이룸', '수면 장애', 'Sleep Disorder']),
('多夢', '다몽', '夢多', '다몽증', '꿈 많음', 'Excessive Dreaming', 'G47.8', '수면', ARRAY['꿈 많이 꿈', '악몽', 'Dream Disturbed Sleep']),
('嗜睡', '기수', '多睡', '기면증', '졸음', 'Hypersomnia', 'G47.1', '수면', ARRAY['항상 졸림', '과수면', 'Excessive Sleepiness']),
('夜驚', '야경', NULL, '야경증', '밤에 깨어남', 'Night Terror', 'F51.4', '수면', ARRAY['수면 중 놀람', 'Sleep Terror']),
('淺眠', '천면', NULL, '수면의 질 저하', '얕은 잠', 'Light Sleep', 'G47.9', '수면', ARRAY['깊은 잠 못 자는 증상', 'Poor Sleep Quality']),

-- ===== 소화기 장애 (Digestive Disorders) =====
('消化不良', '소화불량', '食滯', '소화불량', '소화불량', 'Dyspepsia', 'K30', '소화', ARRAY['체함', '소화 안됨', 'Indigestion']),
('食慾不振', '식욕부진', '不欲食', '식욕부진', '식욕 없음', 'Anorexia', 'R63.0', '소화', ARRAY['밥맛 없음', '입맛 없음', 'Loss of Appetite']),
('腹痛', '복통', '腹中痛', '복통', '배가 아픔', 'Abdominal Pain', 'R10.4', '소화', ARRAY['배 아픔', '위통', 'Stomach Ache']),
('泄瀉', '설사', '下利', '설사', '설사', 'Diarrhea', 'K59.1', '소화', ARRAY['묽은 변', '물변', 'Loose Stool']),
('便秘', '변비', '大便秘結', '변비', '변비', 'Constipation', 'K59.0', '소화', ARRAY['대변 막힘', '배변 곤란', 'Difficulty Defecating']),
('嘔吐', '구토', '吐', '구토', '구토', 'Vomiting', 'R11', '소화', ARRAY['토함', '메스꺼움', 'Nausea']),
('噯氣', '애기', '噫氣', '트림', '트림', 'Belching', 'R14', '소화', ARRAY['가스 올라옴', 'Eructation', 'Burping']),
('胃脘痛', '위완통', NULL, '위통', '위가 아픔', 'Gastric Pain', 'K29.7', '소화', ARRAY['명치 아픔', '상복부 통증', 'Epigastric Pain']),
('腹脹', '복창', '腹滿', '복부팽만', '배 부름', 'Abdominal Distension', 'R14.0', '소화', ARRAY['가스 참', '배 부른 느낌', 'Bloating']),

-- ===== 피로/체력 (Fatigue) =====
('倦怠', '권태', '懶惰', '만성피로', '피곤함', 'Fatigue', 'R53', '피로', ARRAY['무기력', '기운 없음', 'Tiredness']),
('氣虛', '기허', '氣弱', '기력저하', '기운 부족', 'Qi Deficiency', 'R53.1', '피로', ARRAY['원기 부족', '기운 빠짐', 'Lack of Energy']),
('虛勞', '허로', '虛損', '허로', '쇠약', 'Consumptive Disease', 'R53.8', '피로', ARRAY['몸이 약함', '체력 저하', 'Weakness']),
('自汗', '자한', NULL, '자한증', '식은땀', 'Spontaneous Sweating', 'R61', '피로', ARRAY['가만히 있어도 땀남', 'Excessive Sweating']),
('盜汗', '도한', NULL, '도한증', '잘 때 땀', 'Night Sweats', 'R61.0', '피로', ARRAY['수면 중 땀', '밤에 땀', 'Sleep Sweating']),

-- ===== 호흡기 장애 (Respiratory Disorders) =====
('咳嗽', '해수', '咳', '기침', '기침', 'Cough', 'R05', '호흡', ARRAY['기침함', '콜록거림', 'Coughing']),
('痰飮', '담음', '痰', '가래', '가래', 'Phlegm', 'R09.3', '호흡', ARRAY['가래 낌', '담', 'Sputum']),
('喘息', '천식', '喘', '천식', '숨참', 'Asthma', 'J45', '호흡', ARRAY['숨이 가쁨', '호흡곤란', 'Shortness of Breath']),
('咽喉痛', '인후통', '喉痛', '인후통', '목 아픔', 'Sore Throat', 'J02.9', '호흡', ARRAY['목감기', '인후염', 'Pharyngitis']),
('鼻塞', '비색', '鼻不通', '코막힘', '코가 막힘', 'Nasal Congestion', 'R09.81', '호흡', ARRAY['코막힘', 'Stuffy Nose', 'Blocked Nose']),
('鼻淵', '비연', NULL, '비염', '콧물', 'Rhinitis', 'J31.0', '호흡', ARRAY['축농증', '부비동염', 'Sinusitis']),

-- ===== 순환기 장애 (Circulatory Disorders) =====
('頭痛', '두통', '頭痺', '두통', '머리 아픔', 'Headache', 'R51', '순환', ARRAY['머리 아픔', '편두통', 'Migraine']),
('眩暈', '현훈', '眩冒', '어지러움', '어지러움', 'Dizziness', 'R42', '순환', ARRAY['현기증', '빙빙 돌음', 'Vertigo']),
('手足冷', '수족냉', '手足厥冷', '수족냉증', '손발이 차가움', 'Cold Extremities', 'R20.8', '순환', ARRAY['손발 시림', '냉증', 'Cold Hands and Feet']),
('心悸', '심계', '心動悸', '심계항진', '두근거림', 'Palpitation', 'R00.2', '순환', ARRAY['가슴 두근거림', '심장이 빨리 뜀', 'Heart Racing']),
('胸悶', '흉민', NULL, '흉민', '가슴 답답함', 'Chest Tightness', 'R07.89', '순환', ARRAY['가슴 막힘', '답답함', 'Chest Discomfort']),

-- ===== 피부 질환 (Skin Disorders) =====
('濕疹', '습진', NULL, '습진', '습진', 'Eczema', 'L30.9', '피부', ARRAY['피부염', '아토피', 'Dermatitis']),
('瘙痒', '소양', '皮膚瘙痒', '가려움증', '가려움', 'Pruritus', 'L29.9', '피부', ARRAY['피부 가려움', 'Itching']),
('瘡瘍', '창양', NULL, '피부 궤양', '피부 트러블', 'Skin Ulcer', 'L98.4', '피부', ARRAY['종기', '여드름', 'Acne']),
('蕁麻疹', '심마진', NULL, '두드러기', '두드러기', 'Urticaria', 'L50.9', '피부', ARRAY['피부 발진', '알레르기 발진', 'Hives']),

-- ===== 정신/신경 장애 (Mental/Neurological Disorders) =====
('心煩', '심번', '煩躁', '불안', '마음이 괴로움', 'Anxiety', 'F41.9', '정신', ARRAY['불안함', '초조함', 'Nervousness']),
('憂鬱', '우울', '鬱症', '우울증', '우울', 'Depression', 'F32.9', '정신', ARRAY['우울함', '기분 저하', 'Low Mood']),
('健忘', '건망', NULL, '건망증', '기억력 감퇴', 'Forgetfulness', 'R41.3', '정신', ARRAY['깜빡깜빡함', '기억 안남', 'Memory Loss']),
('驚悸', '경계', NULL, '공황', '놀람', 'Panic', 'F41.0', '정신', ARRAY['놀람증', '공황장애', 'Panic Disorder']),
('怔忡', '정충', NULL, '신경과민', '가슴 두근거림', 'Nervous Palpitation', 'R00.0', '정신', ARRAY['신경성 두근거림', 'Nervous Heart']),

-- ===== 근골격계 (Musculoskeletal) =====
('腰痛', '요통', '腰脊痛', '요통', '허리 아픔', 'Low Back Pain', 'M54.5', '통증', ARRAY['허리통증', '요추통', 'Lumbago']),
('關節痛', '관절통', NULL, '관절통', '관절이 아픔', 'Joint Pain', 'M25.5', '통증', ARRAY['마디 아픔', '관절염', 'Arthralgia']),
('肩痛', '견통', NULL, '어깨통증', '어깨 아픔', 'Shoulder Pain', 'M25.51', '통증', ARRAY['어깨결림', '어깨 뻣뻣함', 'Stiff Shoulder']),
('痺症', '비증', NULL, '저림', '저림', 'Numbness', 'R20.2', '통증', ARRAY['손발 저림', '마비감', 'Paresthesia']),

-- ===== 비뇨/생식기 (Urogenital) =====
('頻尿', '빈뇨', '小便頻數', '빈뇨', '소변 자주 봄', 'Frequent Urination', 'R35.0', '비뇨', ARRAY['잦은 소변', '화장실 자주', 'Urinary Frequency']),
('夜尿', '야뇨', NULL, '야뇨증', '밤에 소변', 'Nocturia', 'R35.1', '비뇨', ARRAY['야간 뇨', 'Night Urination']),
('浮腫', '부종', '水腫', '부종', '붓기', 'Edema', 'R60.0', '비뇨', ARRAY['부음', '몸이 붓는 증상', 'Swelling']),

-- ===== 여성 건강 (Women Health) =====
('月經不調', '월경불조', NULL, '월경불순', '생리불순', 'Menstrual Irregularity', 'N92.6', '여성', ARRAY['생리 불규칙', '월경 이상', 'Irregular Period']),
('痛經', '통경', NULL, '월경통', '생리통', 'Dysmenorrhea', 'N94.6', '여성', ARRAY['생리 아픔', '월경 통증', 'Menstrual Cramps']),
('更年期', '갱년기', NULL, '갱년기 증후군', '갱년기', 'Menopause', 'N95.1', '여성', ARRAY['폐경기', '안면홍조', 'Hot Flashes']),

-- ===== 면역/기타 (Immune/Others) =====
('感冒', '감모', NULL, '감기', '감기', 'Common Cold', 'J00', '면역', ARRAY['코감기', '몸살', 'Cold']),
('發熱', '발열', '身熱', '발열', '열이 남', 'Fever', 'R50.9', '면역', ARRAY['열', '고열', 'High Temperature']),
('虛弱', '허약', NULL, '면역력 저하', '면역력 약함', 'Immunodeficiency', 'D84.9', '면역', ARRAY['잔병치레', '자주 아픔', 'Weak Immunity']),
('過敏', '과민', NULL, '알레르기', '알레르기', 'Allergy', 'T78.40', '면역', ARRAY['과민반응', '음식 알레르기', 'Hypersensitivity'])

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
