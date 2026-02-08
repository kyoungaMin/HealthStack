-- Golden Questions(GQ) 시나리오 매칭 처방전 데이터
-- 각 처방전은 GQ 카테고리(A, B, C, D)와 1:1로 대응되는 상황을 가정함.
-- User ID: '00000000-0000-0000-0000-000000000001' (Test User)

-- 0. 테스트 유저 생성 (FK 제약조건 해결용)
-- auth.users 테이블에 테스트 계정 생성 (Supabase Auth)
INSERT INTO auth.users (id, instance_id, aud, role, email, encrypted_password, email_confirmed_at, created_at, updated_at, raw_app_meta_data, raw_user_meta_data)
VALUES (
  '00000000-0000-0000-0000-000000000001', 
  '00000000-0000-0000-0000-000000000000', 
  'authenticated', 
  'authenticated', 
  'test_gq@healthstack.ai', 
  'encrypted_dummy_password', 
  NOW(), 
  NOW(), 
  NOW(), 
  '{"provider":"email","providers":["email"]}', 
  '{}'
)
ON CONFLICT (id) DO NOTHING;

-- public.user_profiles 테이블 동기화 (만약 트리거가 없다면 수동 삽입)
-- schema.integrated.dbml에 정의된 user_profiles 테이블 사용
INSERT INTO public.user_profiles (user_id, display_name)
VALUES ('00000000-0000-0000-0000-000000000001', 'Test User')
ON CONFLICT (user_id) DO NOTHING;


/*
  [GQ-A: 소화/장 매칭]
  - 상황: "식후 더부룩하고 트림이 잦아", "속쓰림/역류가 있는데..."
  - 처방: 위산분비억제제(PPI/P-CAB) + 위장관운동조절제
*/
INSERT INTO user_input_sessions (id, user_id, input_type, input_summary, created_at) VALUES
(301, '00000000-0000-0000-0000-000000000001', 'prescription', 'GQ-A: 역류성 식도염 및 기능성 소화불량', NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_prescriptions (id, user_id, session_id, prescription_image_url, prescribed_at, created_at) VALUES
(301, '00000000-0000-0000-0000-000000000001', 301, 'https://cdn.healthstack/rx/gq_digest_01.jpg', CURRENT_DATE, NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_prescription_drugs (prescription_id, drug_name, dosage, frequency, duration, created_at) VALUES
(301, '케이캡정50mg (테고프라잔)', '1정', '1일 1회', '14일', NOW()), -- P-CAB: 위산분비억제
(301, '가스모틴정5mg (모사프리드)', '1정', '1일 3회', '14일', NOW()), -- 위장관운동촉진제
(301, '스티렌투엑스정 (쑥추출물)', '1정', '1일 2회', '14일', NOW()); -- 위점막보호제


/*
  [GQ-B: 수면/스트레스 매칭]
  - 상황: "잠이 얕고 새벽에 자주 깨", "긴장성 두통이 잦아"
  - 처방: 수면유도제(Z-drug) + 항불안제(Benzodiazepine)
*/
INSERT INTO user_input_sessions (id, user_id, input_type, input_summary, created_at) VALUES
(302, '00000000-0000-0000-0000-000000000001', 'prescription', 'GQ-B: 불면증 및 불안장애', NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_prescriptions (id, user_id, session_id, prescription_image_url, prescribed_at, created_at) VALUES
(302, '00000000-0000-0000-0000-000000000001', 302, 'https://cdn.healthstack/rx/gq_sleep_01.jpg', CURRENT_DATE - 2, NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_prescription_drugs (prescription_id, drug_name, dosage, frequency, duration, created_at) VALUES
(302, '스틸녹스정10mg (졸피뎀타르타르산염)', '1정', '취침 전', '7일', NOW()), -- 수면제
(302, '자낙스정0.25mg (알프라졸람)', '0.5정', '필요시', '7일', NOW()), -- 항불안제
(302, '인데놀정10mg (프로프라놀롤)', '1정', '1일 2회', '7일', NOW()); -- 베타차단제(심계항진 완화)


/*
  [GQ-C: 면역/호흡기/피부 매칭]
  - 상황: "기침/가래가 오래가", "비염이 심한 날", "피부 염증"
  - 처방: 항히스타민제 + 소염진통제 + 스테로이드(단기)
*/
INSERT INTO user_input_sessions (id, user_id, input_type, input_summary, created_at) VALUES
(303, '00000000-0000-0000-0000-000000000001', 'prescription', 'GQ-C: 알레르기 비염 및 피부염', NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_prescriptions (id, user_id, session_id, prescription_image_url, prescribed_at, created_at) VALUES
(303, '00000000-0000-0000-0000-000000000001', 303, 'https://cdn.healthstack/rx/gq_immune_01.jpg', CURRENT_DATE - 5, NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_prescription_drugs (prescription_id, drug_name, dosage, frequency, duration, created_at) VALUES
(303, '씨잘정5mg (레보세티리지염산염)', '1정', '취침 전', '5일', NOW()), -- 항히스타민제
(303, '소론도정 (프레드니솔론)', '1정', '1일 2회', '3일', NOW()), -- 스테로이드(염증 완화)
(303, '슈다페드정 (슈도에페드린)', '1정', '1일 3회', '5일', NOW()); -- 비충혈제거제


/*
  [GQ-D: 대사/만성질환 매칭]
  - 상황: "혈당이 식후에 튀어", "혈압이 경계선", "중성지방이 높아"
  - 처방: 당뇨병용제 + 고혈압/고지혈증 복합제
*/
INSERT INTO user_input_sessions (id, user_id, input_type, input_summary, created_at) VALUES
(304, '00000000-0000-0000-0000-000000000001', 'prescription', 'GQ-D: 당뇨 및 고지혈증 관리', NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_prescriptions (id, user_id, session_id, prescription_image_url, prescribed_at, created_at) VALUES
(304, '00000000-0000-0000-0000-000000000001', 304, 'https://cdn.healthstack/rx/gq_metabolic_01.jpg', CURRENT_DATE - 10, NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_prescription_drugs (prescription_id, drug_name, dosage, frequency, duration, created_at) VALUES
(304, '다이아벡스정500mg (메트포르민)', '1정', '식후 즉시', '30일', NOW()), -- 당뇨약
(304, '트윈스타정40/5mg (텔미사르탄/암로디핀)', '1정', '1일 1회', '30일', NOW()), -- 고혈압 복합제
(304, '리피토정10mg (아토르바스타틴)', '1정', '1일 1회', '30일', NOW()); -- 고지혈증 치료제
