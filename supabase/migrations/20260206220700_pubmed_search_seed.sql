-- =============================================
-- Migration: PubMed Search Strategy Seed Data
-- Date: 2026-02-06
-- Description: MeSH 용어 매핑 + PubMed 검색 키워드 시드 데이터
-- =============================================

-- -----------------------------------------------
-- 1. modern_to_mesh_map 테이블 생성
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS modern_to_mesh_map (
  id bigserial PRIMARY KEY,
  
  modern_disease_id bigint NOT NULL REFERENCES disease_master(id) ON DELETE CASCADE,
  
  mesh_term text NOT NULL,
  mesh_ui text,           -- MeSH Unique Identifier (예: D012893)
  mesh_tree text,         -- MeSH Tree Number (예: F03.870.400)
  
  search_role text NOT NULL CHECK (search_role IN ('primary', 'secondary', 'context')),
  priority int DEFAULT 100,
  note text,
  
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  
  UNIQUE(modern_disease_id, mesh_term)
);

CREATE INDEX IF NOT EXISTS idx_modern_to_mesh_modern ON modern_to_mesh_map(modern_disease_id);
CREATE INDEX IF NOT EXISTS idx_modern_to_mesh_priority ON modern_to_mesh_map(modern_disease_id, priority);

-- -----------------------------------------------
-- 2. symptom_pubmed_map 테이블 생성
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS symptom_pubmed_map (
  id bigserial PRIMARY KEY,
  
  symptom_id bigint NOT NULL REFERENCES disease_master(id) ON DELETE CASCADE,
  
  keyword_en text NOT NULL,
  mesh_term text,
  
  search_role text NOT NULL CHECK (search_role IN ('primary', 'secondary', 'context')),
  priority int DEFAULT 100,
  note text,
  
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  
  UNIQUE(symptom_id, keyword_en)
);

CREATE INDEX IF NOT EXISTS idx_symptom_pubmed_symptom ON symptom_pubmed_map(symptom_id);
CREATE INDEX IF NOT EXISTS idx_symptom_pubmed_priority ON symptom_pubmed_map(symptom_id, priority);

-- -----------------------------------------------
-- 3. ingredient_pubmed_map 테이블 생성
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS ingredient_pubmed_map (
  id bigserial PRIMARY KEY,
  
  rep_code text NOT NULL REFERENCES foods_master(rep_code) ON DELETE CASCADE,
  
  ingredient_name_en text NOT NULL,
  mesh_term text,
  
  bioactive_compound text,
  compound_mesh text,
  
  search_role text NOT NULL CHECK (search_role IN ('primary', 'compound', 'support')),
  priority int DEFAULT 100,
  note text,
  
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ingredient_pubmed_rep ON ingredient_pubmed_map(rep_code);
CREATE INDEX IF NOT EXISTS idx_ingredient_pubmed_priority ON ingredient_pubmed_map(rep_code, priority);

-- -----------------------------------------------
-- 4. modern_to_mesh_map 시드 데이터
-- -----------------------------------------------
INSERT INTO modern_to_mesh_map (modern_disease_id, mesh_term, mesh_ui, mesh_tree, search_role, priority, note)

-- ===== 수면 장애 =====
SELECT d.id, 'Sleep Initiation and Maintenance Disorders', 'D007319', 'F03.870.400.800', 'primary', 100, '불면증 MeSH 핵심 용어'
FROM disease_master d WHERE d.disease = '不眠'
UNION ALL
SELECT d.id, 'Insomnia', NULL, NULL, 'secondary', 90, '불면 일반 용어'
FROM disease_master d WHERE d.disease = '不眠'
UNION ALL
SELECT d.id, 'Sleep Wake Disorders', 'D012893', 'F03.870', 'context', 80, '수면-각성 장애 상위 개념'
FROM disease_master d WHERE d.disease = '不眠'

UNION ALL
SELECT d.id, 'Dreams', 'D004325', 'F02.830.210', 'primary', 100, '꿈 관련 MeSH'
FROM disease_master d WHERE d.disease = '多夢'

UNION ALL
SELECT d.id, 'Disorders of Excessive Somnolence', 'D006970', 'F03.870.400.360', 'primary', 100, '기면증'
FROM disease_master d WHERE d.disease = '嗜睡'

-- ===== 소화기 장애 =====
UNION ALL
SELECT d.id, 'Dyspepsia', 'D004415', 'C23.888.821.270', 'primary', 100, '소화불량'
FROM disease_master d WHERE d.disease = '消化不良'
UNION ALL
SELECT d.id, 'Indigestion', NULL, NULL, 'secondary', 90, '체함 일반 용어'
FROM disease_master d WHERE d.disease = '消化不良'

UNION ALL
SELECT d.id, 'Anorexia', 'D000855', 'C23.888.821.100', 'primary', 100, '식욕부진'
FROM disease_master d WHERE d.disease = '食慾不振'
UNION ALL
SELECT d.id, 'Loss of Appetite', NULL, NULL, 'secondary', 90, '식욕 감퇴'
FROM disease_master d WHERE d.disease = '食慾不振'

UNION ALL
SELECT d.id, 'Diarrhea', 'D003967', 'C23.888.821.214', 'primary', 100, '설사'
FROM disease_master d WHERE d.disease = '泄瀉'

UNION ALL
SELECT d.id, 'Constipation', 'D003248', 'C23.888.821.150', 'primary', 100, '변비'
FROM disease_master d WHERE d.disease = '便秘'

UNION ALL
SELECT d.id, 'Eructation', 'D004884', 'C23.888.821.280', 'primary', 100, '트림'
FROM disease_master d WHERE d.disease = '噯氣'

UNION ALL
SELECT d.id, 'Abdominal Pain', 'D015746', 'C23.888.646.100', 'primary', 100, '복통'
FROM disease_master d WHERE d.disease = '腹痛'

UNION ALL
SELECT d.id, 'Vomiting', 'D014839', 'C23.888.821.937', 'primary', 100, '구토'
FROM disease_master d WHERE d.disease = '嘔吐'
UNION ALL
SELECT d.id, 'Nausea', 'D009325', 'C23.888.821.597', 'secondary', 90, '오심'
FROM disease_master d WHERE d.disease = '嘔吐'

-- ===== 피로/허약 =====
UNION ALL
SELECT d.id, 'Fatigue', 'D005221', 'C23.888.369', 'primary', 100, '피로'
FROM disease_master d WHERE d.disease = '倦怠'
UNION ALL
SELECT d.id, 'Chronic Fatigue Syndrome', 'D015673', 'C23.888.369.200', 'secondary', 90, '만성피로증후군'
FROM disease_master d WHERE d.disease = '倦怠'

UNION ALL
SELECT d.id, 'Hyperhidrosis', 'D006945', 'C23.888.885.437', 'primary', 100, '다한증'
FROM disease_master d WHERE d.disease = '自汗'

UNION ALL
SELECT d.id, 'Night Sweats', NULL, NULL, 'primary', 100, '야간 발한'
FROM disease_master d WHERE d.disease = '盜汗'

-- ===== 호흡기 =====
UNION ALL
SELECT d.id, 'Cough', 'D003371', 'C23.888.852.293', 'primary', 100, '기침'
FROM disease_master d WHERE d.disease = '咳嗽'

UNION ALL
SELECT d.id, 'Sputum', 'D013183', 'A12.200.666', 'primary', 100, '가래'
FROM disease_master d WHERE d.disease = '痰飮'
UNION ALL
SELECT d.id, 'Phlegm', NULL, NULL, 'secondary', 90, '담'
FROM disease_master d WHERE d.disease = '痰飮'

UNION ALL
SELECT d.id, 'Asthma', 'D001249', 'C08.381.495.108', 'primary', 100, '천식'
FROM disease_master d WHERE d.disease = '喘息'
UNION ALL
SELECT d.id, 'Dyspnea', 'D004417', 'C23.888.852.371', 'secondary', 90, '호흡곤란'
FROM disease_master d WHERE d.disease = '喘息'

UNION ALL
SELECT d.id, 'Pharyngitis', 'D010612', 'C08.730.561', 'primary', 100, '인두염'
FROM disease_master d WHERE d.disease = '咽喉痛'
UNION ALL
SELECT d.id, 'Sore Throat', NULL, NULL, 'secondary', 90, '목 아픔'
FROM disease_master d WHERE d.disease = '咽喉痛'

-- ===== 순환계 =====
UNION ALL
SELECT d.id, 'Headache', 'D006261', 'C23.888.592.612.441', 'primary', 100, '두통'
FROM disease_master d WHERE d.disease = '頭痛'
UNION ALL
SELECT d.id, 'Migraine Disorders', 'D008881', 'C10.228.140.546', 'secondary', 90, '편두통'
FROM disease_master d WHERE d.disease = '頭痛'

UNION ALL
SELECT d.id, 'Dizziness', 'D004244', 'C23.888.592.350', 'primary', 100, '어지러움'
FROM disease_master d WHERE d.disease = '眩暈'
UNION ALL
SELECT d.id, 'Vertigo', 'D014717', 'C23.888.592.350.900', 'secondary', 90, '현기증'
FROM disease_master d WHERE d.disease = '眩暈'

UNION ALL
SELECT d.id, 'Palpitations', 'D006323', 'C23.888.592.612.700', 'primary', 100, '심계항진'
FROM disease_master d WHERE d.disease = '心悸'

-- ===== 피부 =====
UNION ALL
SELECT d.id, 'Eczema', 'D004485', 'C17.800.174.255', 'primary', 100, '습진'
FROM disease_master d WHERE d.disease = '濕疹'
UNION ALL
SELECT d.id, 'Dermatitis', 'D003872', 'C17.800.174', 'secondary', 90, '피부염'
FROM disease_master d WHERE d.disease = '濕疹'

UNION ALL
SELECT d.id, 'Pruritus', 'D011537', 'C17.800.685', 'primary', 100, '가려움'
FROM disease_master d WHERE d.disease = '瘙痒'

-- ===== 정신/신경 =====
UNION ALL
SELECT d.id, 'Anxiety', 'D001007', 'F01.470.132', 'primary', 100, '불안'
FROM disease_master d WHERE d.disease = '心煩'
UNION ALL
SELECT d.id, 'Restlessness', NULL, NULL, 'secondary', 90, '초조'
FROM disease_master d WHERE d.disease = '心煩'

UNION ALL
SELECT d.id, 'Depression', 'D003863', 'F01.145.126.350', 'primary', 100, '우울'
FROM disease_master d WHERE d.disease = '憂鬱'
UNION ALL
SELECT d.id, 'Depressive Disorder', 'D003866', 'F03.600.300', 'secondary', 90, '우울장애'
FROM disease_master d WHERE d.disease = '憂鬱'

UNION ALL
SELECT d.id, 'Memory Disorders', 'D008569', 'C10.597.606.525', 'primary', 100, '기억장애'
FROM disease_master d WHERE d.disease = '健忘'

-- ===== 통증 =====
UNION ALL
SELECT d.id, 'Low Back Pain', 'D017116', 'C23.888.592.612.553', 'primary', 100, '요통'
FROM disease_master d WHERE d.disease = '腰痛'

UNION ALL
SELECT d.id, 'Arthralgia', 'D018771', 'C23.888.592.612.107', 'primary', 100, '관절통'
FROM disease_master d WHERE d.disease = '關節痛'

-- ===== 비뇨/부종 =====
UNION ALL
SELECT d.id, 'Urinary Frequency', NULL, NULL, 'primary', 100, '빈뇨'
FROM disease_master d WHERE d.disease = '頻尿'
UNION ALL
SELECT d.id, 'Pollakiuria', 'D014557', 'C23.888.942.725', 'secondary', 90, '다뇨증'
FROM disease_master d WHERE d.disease = '頻尿'

UNION ALL
SELECT d.id, 'Edema', 'D004487', 'C23.888.277', 'primary', 100, '부종'
FROM disease_master d WHERE d.disease = '浮腫'

-- ===== 면역/감기 =====
UNION ALL
SELECT d.id, 'Common Cold', 'D003139', 'C08.730.162', 'primary', 100, '감기'
FROM disease_master d WHERE d.disease = '感冒'
UNION ALL
SELECT d.id, 'Upper Respiratory Tract Infections', 'D012141', 'C08.730', 'secondary', 90, '상기도감염'
FROM disease_master d WHERE d.disease = '感冒'

UNION ALL
SELECT d.id, 'Fever', 'D005334', 'C23.888.119.344', 'primary', 100, '발열'
FROM disease_master d WHERE d.disease = '發熱'

ON CONFLICT (modern_disease_id, mesh_term) DO UPDATE SET
  mesh_ui = EXCLUDED.mesh_ui,
  mesh_tree = EXCLUDED.mesh_tree,
  search_role = EXCLUDED.search_role,
  priority = EXCLUDED.priority,
  note = EXCLUDED.note,
  updated_at = now();

-- -----------------------------------------------
-- 5. symptom_pubmed_map 시드 데이터
-- -----------------------------------------------
INSERT INTO symptom_pubmed_map (symptom_id, keyword_en, mesh_term, search_role, priority, note)

-- ===== 수면 =====
SELECT d.id, 'insomnia', 'Sleep Initiation and Maintenance Disorders', 'primary', 100, NULL
FROM disease_master d WHERE d.disease = '不眠'
UNION ALL
SELECT d.id, 'sleep disorder', 'Sleep Wake Disorders', 'secondary', 90, NULL
FROM disease_master d WHERE d.disease = '不眠'
UNION ALL
SELECT d.id, 'sleep quality', NULL, 'context', 80, NULL
FROM disease_master d WHERE d.disease = '不眠'

-- ===== 소화 =====
UNION ALL
SELECT d.id, 'dyspepsia', 'Dyspepsia', 'primary', 100, NULL
FROM disease_master d WHERE d.disease = '消化不良'
UNION ALL
SELECT d.id, 'indigestion', NULL, 'secondary', 90, NULL
FROM disease_master d WHERE d.disease = '消化不良'
UNION ALL
SELECT d.id, 'digestive function', NULL, 'context', 80, NULL
FROM disease_master d WHERE d.disease = '消化不良'

UNION ALL
SELECT d.id, 'constipation', 'Constipation', 'primary', 100, NULL
FROM disease_master d WHERE d.disease = '便秘'
UNION ALL
SELECT d.id, 'bowel movement', NULL, 'secondary', 90, NULL
FROM disease_master d WHERE d.disease = '便秘'

UNION ALL
SELECT d.id, 'diarrhea', 'Diarrhea', 'primary', 100, NULL
FROM disease_master d WHERE d.disease = '泄瀉'

-- ===== 피로 =====
UNION ALL
SELECT d.id, 'fatigue', 'Fatigue', 'primary', 100, NULL
FROM disease_master d WHERE d.disease = '倦怠'
UNION ALL
SELECT d.id, 'chronic fatigue', 'Chronic Fatigue Syndrome', 'secondary', 90, NULL
FROM disease_master d WHERE d.disease = '倦怠'
UNION ALL
SELECT d.id, 'energy level', NULL, 'context', 80, NULL
FROM disease_master d WHERE d.disease = '倦怠'

-- ===== 호흡기 =====
UNION ALL
SELECT d.id, 'cough', 'Cough', 'primary', 100, NULL
FROM disease_master d WHERE d.disease = '咳嗽'
UNION ALL
SELECT d.id, 'antitussive', NULL, 'secondary', 90, NULL
FROM disease_master d WHERE d.disease = '咳嗽'

UNION ALL
SELECT d.id, 'asthma', 'Asthma', 'primary', 100, NULL
FROM disease_master d WHERE d.disease = '喘息'
UNION ALL
SELECT d.id, 'bronchial', NULL, 'context', 80, NULL
FROM disease_master d WHERE d.disease = '喘息'

-- ===== 순환 =====
UNION ALL
SELECT d.id, 'headache', 'Headache', 'primary', 100, NULL
FROM disease_master d WHERE d.disease = '頭痛'
UNION ALL
SELECT d.id, 'migraine', 'Migraine Disorders', 'secondary', 90, NULL
FROM disease_master d WHERE d.disease = '頭痛'

UNION ALL
SELECT d.id, 'dizziness', 'Dizziness', 'primary', 100, NULL
FROM disease_master d WHERE d.disease = '眩暈'
UNION ALL
SELECT d.id, 'vertigo', 'Vertigo', 'secondary', 90, NULL
FROM disease_master d WHERE d.disease = '眩暈'

-- ===== 피부 =====
UNION ALL
SELECT d.id, 'eczema', 'Eczema', 'primary', 100, NULL
FROM disease_master d WHERE d.disease = '濕疹'
UNION ALL
SELECT d.id, 'dermatitis', 'Dermatitis', 'secondary', 90, NULL
FROM disease_master d WHERE d.disease = '濕疹'

UNION ALL
SELECT d.id, 'pruritus', 'Pruritus', 'primary', 100, NULL
FROM disease_master d WHERE d.disease = '瘙痒'
UNION ALL
SELECT d.id, 'itching', NULL, 'secondary', 90, NULL
FROM disease_master d WHERE d.disease = '瘙痒'

-- ===== 정신 =====
UNION ALL
SELECT d.id, 'anxiety', 'Anxiety', 'primary', 100, NULL
FROM disease_master d WHERE d.disease = '心煩'
UNION ALL
SELECT d.id, 'anxiolytic', NULL, 'context', 80, NULL
FROM disease_master d WHERE d.disease = '心煩'

UNION ALL
SELECT d.id, 'depression', 'Depression', 'primary', 100, NULL
FROM disease_master d WHERE d.disease = '憂鬱'

ON CONFLICT (symptom_id, keyword_en) DO UPDATE SET
  mesh_term = EXCLUDED.mesh_term,
  search_role = EXCLUDED.search_role,
  priority = EXCLUDED.priority,
  note = EXCLUDED.note,
  updated_at = now();

-- -----------------------------------------------
-- 6. ingredient_pubmed_map 시드 데이터
-- -----------------------------------------------
INSERT INTO ingredient_pubmed_map (rep_code, ingredient_name_en, mesh_term, bioactive_compound, compound_mesh, search_role, priority, note)
VALUES

-- ===== 과일류 =====
('F001', 'Ziziphus jujuba', 'Ziziphus', NULL, NULL, 'primary', 100, '대추 학명'),
('F001', 'Jujube', NULL, NULL, NULL, 'support', 90, '대추 일반명'),
('F001', 'Ziziphus jujuba', NULL, 'Jujuboside A', NULL, 'compound', 85, '대추 주요 사포닌'),
('F001', 'Ziziphus jujuba', NULL, 'Spinosin', NULL, 'compound', 80, '대추 플라보노이드'),

('F002', 'Pyrus pyrifolia', NULL, NULL, NULL, 'primary', 100, '배 학명'),
('F002', 'Asian pear', NULL, NULL, NULL, 'support', 90, '배 일반명'),
('F002', 'Pyrus pyrifolia', NULL, 'Arbutin', NULL, 'compound', 85, '배 폴리페놀'),

('F009', 'Prunus mume', 'Prunus', NULL, NULL, 'primary', 100, '매실 학명'),
('F009', 'Japanese apricot', NULL, NULL, NULL, 'support', 90, '매실 일반명'),
('F009', 'Prunus mume', NULL, 'Citric acid', NULL, 'compound', 85, '매실 유기산'),

('F010', 'Lycium barbarum', 'Lycium', NULL, NULL, 'primary', 100, '구기자 학명'),
('F010', 'Goji berry', NULL, NULL, NULL, 'support', 95, '구기자 일반명'),
('F010', 'Lycium barbarum', NULL, 'Lycium barbarum polysaccharides', 'Polysaccharides', 'compound', 90, 'LBP'),
('F010', 'Lycium barbarum', NULL, 'Zeaxanthin', NULL, 'compound', 85, '제아잔틴'),

-- ===== 채소류 =====
('V001', 'Nelumbo nucifera', 'Nelumbo', NULL, NULL, 'primary', 100, '연근 학명'),
('V001', 'Lotus root', NULL, NULL, NULL, 'support', 90, '연근 일반명'),

('V002', 'Lactuca sativa', 'Lactuca', NULL, NULL, 'primary', 100, '상추 학명'),
('V002', 'Lettuce', NULL, NULL, NULL, 'support', 90, '상추 일반명'),
('V002', 'Lactuca sativa', NULL, 'Lactucin', NULL, 'compound', 85, '상추 수면유도 성분'),

('V003', 'Allium sativum', 'Garlic', NULL, NULL, 'primary', 100, '마늘 학명'),
('V003', 'Garlic', NULL, NULL, NULL, 'support', 95, '마늘 일반명'),
('V003', 'Allium sativum', NULL, 'Allicin', NULL, 'compound', 90, '알리신'),
('V003', 'Allium sativum', NULL, 'S-allyl cysteine', NULL, 'compound', 85, 'SAC'),

('V004', 'Zingiber officinale', 'Ginger', NULL, NULL, 'primary', 100, '생강 학명'),
('V004', 'Ginger', NULL, NULL, NULL, 'support', 95, '생강 일반명'),
('V004', 'Zingiber officinale', NULL, 'Gingerol', NULL, 'compound', 90, '진저롤'),
('V004', 'Zingiber officinale', NULL, 'Shogaol', NULL, 'compound', 85, '쇼가올'),

('V006', 'Raphanus sativus', 'Raphanus', NULL, NULL, 'primary', 100, '무 학명'),
('V006', 'Radish', NULL, NULL, NULL, 'support', 90, '무 일반명'),
('V006', 'Raphanus sativus', NULL, 'Sulforaphane', NULL, 'compound', 85, '설포라판'),

-- ===== 곡물류 =====
('G001', 'Coix lacryma-jobi', 'Coix', NULL, NULL, 'primary', 100, '율무 학명'),
('G001', 'Job tears', NULL, NULL, NULL, 'support', 90, '율무 일반명'),
('G001', 'Coix lacryma-jobi', NULL, 'Coixol', NULL, 'compound', 85, '코익솔'),

('G002', 'Vigna radiata', 'Vigna', NULL, NULL, 'primary', 100, '녹두 학명'),
('G002', 'Mung bean', NULL, NULL, NULL, 'support', 90, '녹두 일반명'),
('G002', 'Vigna radiata', NULL, 'Vitexin', NULL, 'compound', 85, '비텍신'),

('G003', 'Vigna angularis', 'Vigna', NULL, NULL, 'primary', 100, '팥 학명'),
('G003', 'Adzuki bean', NULL, NULL, NULL, 'support', 90, '팥 일반명'),

('G004', 'Glycine max', 'Soybeans', NULL, NULL, 'primary', 100, '검정콩 학명'),
('G004', 'Black soybean', NULL, NULL, NULL, 'support', 95, '검정콩 일반명'),
('G004', 'Glycine max', NULL, 'Anthocyanin', 'Anthocyanins', 'compound', 90, '안토시아닌'),
('G004', 'Glycine max', NULL, 'Isoflavone', 'Isoflavones', 'compound', 85, '이소플라본'),

-- ===== 약재류 =====
('H001', 'Panax ginseng', 'Panax', NULL, NULL, 'primary', 100, '인삼 학명'),
('H001', 'Korean ginseng', NULL, NULL, NULL, 'support', 95, '인삼 일반명'),
('H001', 'Panax ginseng', NULL, 'Ginsenoside', 'Ginsenosides', 'compound', 95, '진세노사이드'),
('H001', 'Panax ginseng', NULL, 'Ginsenoside Rb1', NULL, 'compound', 90, 'Rb1'),
('H001', 'Panax ginseng', NULL, 'Ginsenoside Rg1', NULL, 'compound', 90, 'Rg1'),

('H002', 'Glycyrrhiza glabra', 'Glycyrrhiza', NULL, NULL, 'primary', 100, '감초 학명'),
('H002', 'Licorice', NULL, NULL, NULL, 'support', 95, '감초 일반명'),
('H002', 'Glycyrrhiza glabra', NULL, 'Glycyrrhizin', NULL, 'compound', 90, '글리시리진'),

('H003', 'Astragalus membranaceus', 'Astragalus', NULL, NULL, 'primary', 100, '황기 학명'),
('H003', 'Astragalus', NULL, NULL, NULL, 'support', 95, '황기 일반명'),
('H003', 'Astragalus membranaceus', NULL, 'Astragaloside IV', NULL, 'compound', 90, '아스트라갈로사이드'),
('H003', 'Astragalus membranaceus', NULL, 'Astragalus polysaccharides', 'Polysaccharides', 'compound', 85, 'APS'),

('H004', 'Angelica sinensis', 'Angelica', NULL, NULL, 'primary', 100, '당귀 학명'),
('H004', 'Dong quai', NULL, NULL, NULL, 'support', 95, '당귀 일반명'),
('H004', 'Angelica sinensis', NULL, 'Ferulic acid', 'Coumaric Acids', 'compound', 90, '페룰산'),
('H004', 'Angelica sinensis', NULL, 'Ligustilide', NULL, 'compound', 85, '리구스틸라이드'),

('H005', 'Schisandra chinensis', 'Schisandra', NULL, NULL, 'primary', 100, '오미자 학명'),
('H005', 'Schisandra', NULL, NULL, NULL, 'support', 95, '오미자 일반명'),
('H005', 'Schisandra chinensis', NULL, 'Schisandrin', 'Lignans', 'compound', 90, '시산드린'),

('H006', 'Cinnamomum cassia', 'Cinnamomum', NULL, NULL, 'primary', 100, '계피 학명'),
('H006', 'Cinnamon', NULL, NULL, NULL, 'support', 95, '계피 일반명'),
('H006', 'Cinnamomum cassia', NULL, 'Cinnamaldehyde', NULL, 'compound', 90, '시나몬알데하이드'),

('H007', 'Poria cocos', 'Wolfiporia', NULL, NULL, 'primary', 100, '복령 학명'),
('H007', 'Poria', NULL, NULL, NULL, 'support', 90, '복령 일반명'),
('H007', 'Poria cocos', NULL, 'Pachymic acid', 'Triterpenes', 'compound', 85, '파치믹산'),

('H010', 'Nelumbo nucifera', 'Nelumbo', NULL, NULL, 'primary', 100, '연자 학명'),
('H010', 'Lotus seed', NULL, NULL, NULL, 'support', 90, '연자 일반명'),
('H010', 'Nelumbo nucifera', NULL, 'Neferine', 'Alkaloids', 'compound', 85, '네페린'),

('H011', 'Senna obtusifolia', 'Senna', NULL, NULL, 'primary', 100, '결명자 학명'),
('H011', 'Cassia seed', NULL, NULL, NULL, 'support', 90, '결명자 일반명'),
('H011', 'Senna obtusifolia', NULL, 'Emodin', 'Anthraquinones', 'compound', 85, '에모딘'),

('H012', 'Chrysanthemum morifolium', 'Chrysanthemum', NULL, NULL, 'primary', 100, '국화 학명'),
('H012', 'Chrysanthemum', NULL, NULL, NULL, 'support', 95, '국화 일반명'),
('H012', 'Chrysanthemum morifolium', NULL, 'Luteolin', 'Flavonoids', 'compound', 90, '루테올린'),

-- ===== 해산물 =====
('S001', 'Laminaria japonica', 'Laminaria', NULL, NULL, 'primary', 100, '다시마 학명'),
('S001', 'Kelp', NULL, NULL, NULL, 'support', 95, '다시마 일반명'),
('S001', 'Laminaria japonica', NULL, 'Fucoidan', 'Polysaccharides', 'compound', 90, '후코이단'),

('S003', 'Crassostrea gigas', 'Crassostrea', NULL, NULL, 'primary', 100, '굴 학명'),
('S003', 'Oyster', NULL, NULL, NULL, 'support', 95, '굴 일반명'),
('S003', 'Crassostrea gigas', NULL, 'Zinc', 'Zinc', 'compound', 90, '아연'),

-- ===== 기타 =====
('D001', 'Honey', 'Honey', NULL, NULL, 'primary', 100, '꿀'),
('D001', 'Honey', NULL, 'Flavonoid', 'Flavonoids', 'compound', 85, '플라보노이드'),

('D005', 'Juglans regia', 'Juglans', NULL, NULL, 'primary', 100, '호두 학명'),
('D005', 'Walnut', NULL, NULL, NULL, 'support', 95, '호두 일반명'),
('D005', 'Juglans regia', NULL, 'Alpha-linolenic acid', 'alpha-Linolenic Acid', 'compound', 90, 'ALA'),

('D006', 'Sesamum indicum', 'Sesamum', NULL, NULL, 'primary', 100, '참깨 학명'),
('D006', 'Sesame', NULL, NULL, NULL, 'support', 95, '참깨 일반명'),
('D006', 'Sesamum indicum', NULL, 'Sesamin', 'Lignans', 'compound', 90, '세사민')

ON CONFLICT DO NOTHING;

-- -----------------------------------------------
-- 7. 조회용 뷰
-- -----------------------------------------------
CREATE OR REPLACE VIEW v_pubmed_search_terms AS
SELECT 
  'symptom' AS term_type,
  d.disease AS source_ko,
  d.modern_name_ko,
  s.keyword_en,
  s.mesh_term,
  s.search_role,
  s.priority
FROM symptom_pubmed_map s
JOIN disease_master d ON s.symptom_id = d.id

UNION ALL

SELECT 
  'ingredient' AS term_type,
  f.modern_name AS source_ko,
  f.name_en,
  i.ingredient_name_en AS keyword_en,
  i.mesh_term,
  i.search_role,
  i.priority
FROM ingredient_pubmed_map i
JOIN foods_master f ON i.rep_code = f.rep_code
ORDER BY term_type, priority DESC;
