-- =============================================
-- Seed Data: foods_master (식재료 마스터)
-- Date: 2026-02-06
-- Description: 동의보감 기반 주요 식재료 + 현대명/영문명 매핑
-- =============================================

-- UPSERT 방식: rep_code 기준으로 존재하면 UPDATE, 없으면 INSERT
-- 기존 traditional_foods에서 추출된 데이터와 병합 가능

INSERT INTO foods_master (rep_code, rep_name, modern_name, name_en, aliases, category, nutrients) VALUES

-- ===== 과일류 (Fruits) =====
('F001', '大棗', '대추', 'Jujube', ARRAY['대조', '홍대추', 'Red Date', 'Chinese Date'], '과일', '{"vitamin_c": "high", "iron": "moderate", "fiber": "high"}'::jsonb),
('F002', '梨', '배', 'Asian Pear', ARRAY['이', '청배', 'Korean Pear', 'Nashi'], '과일', '{"vitamin_c": "moderate", "fiber": "high", "water": "very_high"}'::jsonb),
('F003', '柿', '감', 'Persimmon', ARRAY['시', '단감', '홍시', 'Kaki'], '과일', '{"vitamin_a": "high", "vitamin_c": "high", "fiber": "moderate"}'::jsonb),
('F004', '杏', '살구', 'Apricot', ARRAY['행', '개살구', '행자'], '과일', '{"vitamin_a": "very_high", "potassium": "high"}'::jsonb),
('F005', '桃', '복숭아', 'Peach', ARRAY['도', '백도', '황도'], '과일', '{"vitamin_c": "moderate", "fiber": "moderate"}'::jsonb),
('F006', '葡萄', '포도', 'Grape', ARRAY['포도', 'Vitis vinifera'], '과일', '{"antioxidants": "high", "vitamin_k": "moderate"}'::jsonb),
('F007', '石榴', '석류', 'Pomegranate', ARRAY['석류', 'Punica granatum'], '과일', '{"antioxidants": "very_high", "vitamin_c": "high"}'::jsonb),
('F008', '柚子', '유자', 'Yuzu', ARRAY['유자', 'Citrus junos'], '과일', '{"vitamin_c": "very_high", "limonene": "high"}'::jsonb),
('F009', '梅實', '매실', 'Japanese Apricot', ARRAY['매', '청매', 'Ume', 'Plum'], '과일', '{"citric_acid": "very_high", "minerals": "high"}'::jsonb),
('F010', '枸杞子', '구기자', 'Goji Berry', ARRAY['구기', 'Wolfberry', 'Lycium barbarum'], '과일', '{"vitamin_a": "very_high", "antioxidants": "very_high"}'::jsonb),

-- ===== 채소류 (Vegetables) =====
('V001', '蓮根', '연근', 'Lotus Root', ARRAY['연뿌리', 'Nelumbo nucifera'], '채소', '{"vitamin_c": "high", "fiber": "high", "iron": "moderate"}'::jsonb),
('V002', '萵苣', '상추', 'Lettuce', ARRAY['와거', 'Lactuca sativa'], '채소', '{"vitamin_k": "high", "folate": "moderate"}'::jsonb),
('V003', '蒜', '마늘', 'Garlic', ARRAY['산', '대산', 'Allium sativum'], '채소', '{"allicin": "very_high", "vitamin_b6": "high"}'::jsonb),
('V004', '生薑', '생강', 'Ginger', ARRAY['강', '건강', 'Zingiber officinale'], '채소', '{"gingerol": "very_high", "vitamin_b6": "moderate"}'::jsonb),
('V005', '蔥', '파', 'Green Onion', ARRAY['총', '대파', '쪽파', 'Scallion'], '채소', '{"vitamin_k": "high", "vitamin_c": "moderate"}'::jsonb),
('V006', '蘿蔔', '무', 'Radish', ARRAY['나복', '무우', 'Daikon'], '채소', '{"vitamin_c": "high", "digestive_enzymes": "high"}'::jsonb),
('V007', '冬瓜', '동과', 'Winter Melon', ARRAY['동아', 'Wax Gourd'], '채소', '{"water": "very_high", "vitamin_c": "moderate"}'::jsonb),
('V008', '南瓜', '호박', 'Pumpkin', ARRAY['남과', 'Squash', 'Cucurbita'], '채소', '{"vitamin_a": "very_high", "fiber": "high"}'::jsonb),
('V009', '菠薐', '시금치', 'Spinach', ARRAY['파릉', 'Spinacia oleracea'], '채소', '{"iron": "high", "vitamin_k": "very_high", "folate": "high"}'::jsonb),
('V010', '芹菜', '미나리', 'Water Parsley', ARRAY['근채', 'Oenanthe javanica', 'Water Dropwort'], '채소', '{"vitamin_a": "high", "fiber": "high"}'::jsonb),
('V011', '白菜', '배추', 'Napa Cabbage', ARRAY['백채', 'Chinese Cabbage'], '채소', '{"vitamin_c": "high", "vitamin_k": "high"}'::jsonb),
('V012', '茄子', '가지', 'Eggplant', ARRAY['가', 'Aubergine', 'Solanum melongena'], '채소', '{"anthocyanins": "high", "fiber": "moderate"}'::jsonb),
('V013', '黃瓜', '오이', 'Cucumber', ARRAY['황과', 'Cucumis sativus'], '채소', '{"water": "very_high", "vitamin_k": "moderate"}'::jsonb),
('V014', '韮', '부추', 'Chives', ARRAY['구', 'Garlic Chives', 'Allium tuberosum'], '채소', '{"vitamin_k": "very_high", "vitamin_a": "high"}'::jsonb),
('V015', '苦菜', '씀바귀', 'Bitter Herb', ARRAY['고채', 'Ixeris dentata'], '채소', '{"fiber": "high", "minerals": "moderate"}'::jsonb),

-- ===== 곡물류 (Grains) =====
('G001', '薏苡仁', '율무', 'Job''s Tears', ARRAY['의이인', 'Coix lacryma-jobi', 'Adlay'], '곡물', '{"protein": "high", "fiber": "high"}'::jsonb),
('G002', '綠豆', '녹두', 'Mung Bean', ARRAY['녹두', 'Vigna radiata'], '곡물', '{"protein": "high", "folate": "high"}'::jsonb),
('G003', '赤小豆', '팥', 'Red Bean', ARRAY['적소두', 'Adzuki Bean', 'Vigna angularis'], '곡물', '{"protein": "high", "iron": "high", "fiber": "very_high"}'::jsonb),
('G004', '黑豆', '검정콩', 'Black Bean', ARRAY['흑두', '서리태', 'Black Soybean'], '곡물', '{"protein": "very_high", "anthocyanins": "high"}'::jsonb),
('G005', '玄米', '현미', 'Brown Rice', ARRAY['현미', 'Unpolished Rice'], '곡물', '{"fiber": "high", "vitamin_b": "high", "manganese": "high"}'::jsonb),
('G006', '糯米', '찹쌀', 'Glutinous Rice', ARRAY['나미', 'Sticky Rice', 'Sweet Rice'], '곡물', '{"carbohydrates": "high", "protein": "moderate"}'::jsonb),
('G007', '粟', '조', 'Millet', ARRAY['속', 'Foxtail Millet', 'Setaria italica'], '곡물', '{"iron": "high", "magnesium": "high"}'::jsonb),
('G008', '蕎麥', '메밀', 'Buckwheat', ARRAY['교맥', 'Fagopyrum esculentum'], '곡물', '{"rutin": "very_high", "protein": "high"}'::jsonb),
('G009', '大麥', '보리', 'Barley', ARRAY['대맥', 'Hordeum vulgare'], '곡물', '{"fiber": "very_high", "selenium": "high"}'::jsonb),
('G010', '燕麥', '귀리', 'Oat', ARRAY['연맥', 'Avena sativa'], '곡물', '{"beta_glucan": "very_high", "fiber": "very_high"}'::jsonb),

-- ===== 약재류 (Medicinal Herbs) =====
('H001', '人蔘', '인삼', 'Ginseng', ARRAY['인삼', 'Panax ginseng', 'Korean Ginseng'], '약재', '{"ginsenosides": "very_high", "saponins": "high"}'::jsonb),
('H002', '甘草', '감초', 'Licorice Root', ARRAY['감초', 'Glycyrrhiza glabra'], '약재', '{"glycyrrhizin": "very_high"}'::jsonb),
('H003', '黃芪', '황기', 'Astragalus', ARRAY['황기', 'Astragalus membranaceus'], '약재', '{"polysaccharides": "high", "saponins": "high"}'::jsonb),
('H004', '當歸', '당귀', 'Angelica Root', ARRAY['당귀', 'Angelica sinensis', 'Dong Quai'], '약재', '{"ferulic_acid": "high"}'::jsonb),
('H005', '五味子', '오미자', 'Schisandra', ARRAY['오미자', 'Schisandra chinensis', 'Five Flavor Berry'], '약재', '{"lignans": "very_high"}'::jsonb),
('H006', '桂皮', '계피', 'Cinnamon', ARRAY['육계', 'Cinnamomum cassia'], '약재', '{"cinnamaldehyde": "very_high"}'::jsonb),
('H007', '茯苓', '복령', 'Poria', ARRAY['백복령', 'Poria cocos'], '약재', '{"polysaccharides": "high"}'::jsonb),
('H008', '陳皮', '진피', 'Dried Tangerine Peel', ARRAY['귤피', 'Citrus reticulata peel'], '약재', '{"hesperidin": "high", "vitamin_c": "moderate"}'::jsonb),
('H009', '山藥', '산약', 'Chinese Yam', ARRAY['마', '산마', 'Dioscorea opposita'], '약재', '{"diosgenin": "high", "mucin": "high"}'::jsonb),
('H010', '蓮子', '연자', 'Lotus Seed', ARRAY['연자육', 'Nelumbo nucifera seed'], '약재', '{"protein": "high", "minerals": "high"}'::jsonb),
('H011', '決明子', '결명자', 'Cassia Seed', ARRAY['결명자', 'Senna obtusifolia'], '약재', '{"anthraquinones": "high"}'::jsonb),
('H012', '菊花', '국화', 'Chrysanthemum', ARRAY['감국', 'Chrysanthemum morifolium'], '약재', '{"flavonoids": "high", "vitamin_a": "moderate"}'::jsonb),

-- ===== 해산물류 (Seafood) =====
('S001', '海帶', '다시마', 'Kelp', ARRAY['해대', 'Laminaria', 'Kombu'], '해산물', '{"iodine": "very_high", "fiber": "high"}'::jsonb),
('S002', '紫菜', '김', 'Seaweed', ARRAY['자채', 'Laver', 'Nori', 'Porphyra'], '해산물', '{"iodine": "high", "vitamin_b12": "high"}'::jsonb),
('S003', '牡蠣', '굴', 'Oyster', ARRAY['모려', 'Crassostrea gigas'], '해산물', '{"zinc": "very_high", "vitamin_b12": "high"}'::jsonb),
('S004', '鰒魚', '전복', 'Abalone', ARRAY['복어', 'Haliotis'], '해산물', '{"protein": "high", "selenium": "high"}'::jsonb),
('S005', '蝦', '새우', 'Shrimp', ARRAY['하', 'Prawn'], '해산물', '{"protein": "high", "selenium": "high", "vitamin_b12": "high"}'::jsonb),
('S006', '蟹', '게', 'Crab', ARRAY['해', '꽃게', '대게'], '해산물', '{"protein": "high", "zinc": "high", "copper": "high"}'::jsonb),
('S007', '烏賊', '오징어', 'Squid', ARRAY['오적어', 'Calamari'], '해산물', '{"protein": "very_high", "vitamin_b12": "high"}'::jsonb),
('S008', '海蔘', '해삼', 'Sea Cucumber', ARRAY['해삼', 'Holothuroidea'], '해산물', '{"collagen": "very_high", "protein": "high"}'::jsonb),

-- ===== 육류 (Meat) =====
('M001', '雞肉', '닭고기', 'Chicken', ARRAY['계육', '닭', 'Poultry'], '육류', '{"protein": "very_high", "vitamin_b6": "high"}'::jsonb),
('M002', '豬肉', '돼지고기', 'Pork', ARRAY['저육', '돼지'], '육류', '{"protein": "high", "thiamin": "very_high"}'::jsonb),
('M003', '牛肉', '소고기', 'Beef', ARRAY['우육', '소'], '육류', '{"protein": "very_high", "iron": "high", "zinc": "high"}'::jsonb),
('M004', '羊肉', '양고기', 'Lamb', ARRAY['양육', '양', 'Mutton'], '육류', '{"protein": "high", "zinc": "high", "vitamin_b12": "high"}'::jsonb),
('M005', '鴨肉', '오리고기', 'Duck', ARRAY['압육', '오리'], '육류', '{"protein": "high", "iron": "high"}'::jsonb),

-- ===== 유제품/기타 (Dairy & Others) =====
('D001', '蜂蜜', '꿀', 'Honey', ARRAY['봉밀', '벌꿀'], '기타', '{"carbohydrates": "very_high", "antioxidants": "moderate"}'::jsonb),
('D002', '牛乳', '우유', 'Milk', ARRAY['우유', '牛奶'], '유제품', '{"calcium": "very_high", "vitamin_d": "high"}'::jsonb),
('D003', '鷄卵', '달걀', 'Egg', ARRAY['계란', '달걀', 'Chicken Egg'], '기타', '{"protein": "very_high", "choline": "very_high"}'::jsonb),
('D004', '松子', '잣', 'Pine Nut', ARRAY['송자', '해송자', 'Pinus koraiensis'], '견과류', '{"healthy_fats": "very_high", "vitamin_e": "high"}'::jsonb),
('D005', '胡桃', '호두', 'Walnut', ARRAY['호도', 'Juglans regia'], '견과류', '{"omega3": "very_high", "vitamin_e": "high"}'::jsonb),
('D006', '芝麻', '참깨', 'Sesame', ARRAY['지마', '흑임자', 'Sesame Seed'], '견과류', '{"calcium": "very_high", "healthy_fats": "high"}'::jsonb),
('D007', '落花生', '땅콩', 'Peanut', ARRAY['낙화생', 'Arachis hypogaea'], '견과류', '{"protein": "high", "niacin": "high"}'::jsonb),
('D008', '栗', '밤', 'Chestnut', ARRAY['율', 'Castanea crenata'], '견과류', '{"vitamin_c": "high", "carbohydrates": "high"}'::jsonb)

ON CONFLICT (rep_code) DO UPDATE SET
  modern_name = EXCLUDED.modern_name,
  name_en = EXCLUDED.name_en,
  aliases = EXCLUDED.aliases,
  category = EXCLUDED.category,
  nutrients = EXCLUDED.nutrients,
  updated_at = now();
