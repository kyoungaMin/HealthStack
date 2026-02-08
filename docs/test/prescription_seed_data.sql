-- 처방전 분석 로직 테스트를 위한 샘플 데이터 (PostgreSQL)
-- User ID: '00000000-0000-0000-0000-000000000001' (Test User)

-- 0. 테스트 유저 생성 (FK 제약조건 해결용)
INSERT INTO auth.users (id, instance_id, aud, role, email, encrypted_password, email_confirmed_at, created_at, updated_at, raw_app_meta_data, raw_user_meta_data)
VALUES (
  '00000000-0000-0000-0000-000000000001', 
  '00000000-0000-0000-0000-000000000000', 
  'authenticated', 
  'authenticated', 
  'test_seed@healthstack.ai', 
  'encrypted_dummy_password', 
  NOW(), 
  NOW(), 
  NOW(), 
  '{"provider":"email","providers":["email"]}', 
  '{}'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.user_profiles (user_id, display_name)
VALUES ('00000000-0000-0000-0000-000000000001', 'Test Seed User')
ON CONFLICT (user_id) DO NOTHING;


-- 1. 입력 세션 (Session) 생성
INSERT INTO user_input_sessions (id, user_id, input_type, input_summary, created_at) VALUES
(101, '00000000-0000-0000-0000-000000000001', 'prescription', '감기 증상으로 인한 처방전', NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_input_sessions (id, user_id, input_type, input_summary, created_at) VALUES
(102, '00000000-0000-0000-0000-000000000001', 'prescription', '속쓰림 및 역류성 식도염 처방', NOW() - INTERVAL '3 days')
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_input_sessions (id, user_id, input_type, input_summary, created_at) VALUES
(103, '00000000-0000-0000-0000-000000000001', 'combined', '혈압 관리 정기 처방', NOW() - INTERVAL '1 month')
ON CONFLICT (id) DO NOTHING;


-- 2. 처방전 메타 정보 (Prescription) 생성
INSERT INTO user_prescriptions (id, user_id, session_id, prescription_image_url, prescribed_at, created_at) VALUES
(201, '00000000-0000-0000-0000-000000000001', 101, 'https://s3.example.com/prescriptions/cold_001.jpg', '2025-02-07', NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_prescriptions (id, user_id, session_id, prescription_image_url, prescribed_at, created_at) VALUES
(202, '00000000-0000-0000-0000-000000000001', 102, 'https://s3.example.com/prescriptions/gerd_002.jpg', '2025-02-04', NOW() - INTERVAL '3 days')
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_prescriptions (id, user_id, session_id, prescription_image_url, prescribed_at, created_at) VALUES
(203, '00000000-0000-0000-0000-000000000001', 103, 'https://s3.example.com/prescriptions/htn_003.jpg', '2025-01-07', NOW() - INTERVAL '1 month')
ON CONFLICT (id) DO NOTHING;


-- 3. 처방 약물 상세 (Drugs) 생성

-- Case A: 호흡기 (감기)
INSERT INTO user_prescription_drugs (prescription_id, drug_name, dosage, frequency, duration, created_at) VALUES
(201, '코대원포르테시럽', '20ml', '1일 3회', '3일분', NOW()),
(201, '슈다페드정', '1정', '1일 3회', '3일분', NOW()),
(201, '타이레놀8시간이알서방정', '1정', '1일 3회', '3일분', NOW());

-- Case B: 소화기 (위염/식도염)
INSERT INTO user_prescription_drugs (prescription_id, drug_name, dosage, frequency, duration, created_at) VALUES
(202, '케이캡정50mg', '1정', '1일 1회', '14일분', NOW()),
(202, '가스티인CR정', '1정', '1일 1회', '14일분', NOW()),
(202, '알마게이트현탁액', '1포', '1일 3회', '14일분', NOW());

-- Case C: 만성질환 (고혈압/고지혈증)
INSERT INTO user_prescription_drugs (prescription_id, drug_name, dosage, frequency, duration, created_at) VALUES
(203, '아모디핀정5mg', '1정', '1일 1회', '30일분', NOW()),
(203, '로수젯정10/5mg', '1정', '1일 1회', '30일분', NOW()),
(203, '바이주명정100mg', '1정', '1일 1회', '30일분', NOW());
