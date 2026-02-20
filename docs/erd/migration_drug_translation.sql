-- 약물명 한글↔영어 매핑 테이블
CREATE TABLE IF NOT EXISTS drug_translation (
    id SERIAL PRIMARY KEY,
    korean_name TEXT NOT NULL UNIQUE,
    english_name TEXT NOT NULL,
    source TEXT DEFAULT 'manual', -- 'manual', 'mymemory', 'openai' etc
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성 (빠른 검색)
CREATE INDEX idx_drug_translation_korean ON drug_translation(korean_name);
CREATE INDEX idx_drug_translation_english ON drug_translation(english_name);

-- 자주 사용되는 약물명 미리 입력
INSERT INTO drug_translation (korean_name, english_name, source, verified) VALUES
    ('타이레놀', 'Tylenol', 'manual', TRUE),
    ('아스피린', 'Aspirin', 'manual', TRUE),
    ('넥시움', 'Nexium', 'manual', TRUE),
    ('레트로졸', 'Letrozole', 'manual', TRUE),
    ('이부프로fen', 'Ibuprofen', 'manual', TRUE),
    ('아세트아미노펜', 'Acetaminophen', 'manual', TRUE),
    ('메트포르민', 'Metformin', 'manual', TRUE),
    ('오메프라졸', 'Omeprazole', 'manual', TRUE),
    ('심바스타틴', 'Simvastatin', 'manual', TRUE),
    ('아토르바스타틴', 'Atorvastatin', 'manual', TRUE),
    ('암로디핀', 'Amlodipine', 'manual', TRUE),
    ('로사르탄', 'Losartan', 'manual', TRUE),
    ('클로피도그렐', 'Clopidogrel', 'manual', TRUE),
    ('레보티록신', 'Levothyroxine', 'manual', TRUE),
    ('알프라졸람', 'Alprazolam', 'manual', TRUE)
ON CONFLICT (korean_name) DO NOTHING;

COMMENT ON TABLE drug_translation IS '약물명 한글-영어 매핑 테이블 (번역 캐시)';
COMMENT ON COLUMN drug_translation.source IS '번역 출처: manual(수동입력), mymemory(MyMemory API), openai(OpenAI), google(Google Translate)';
COMMENT ON COLUMN drug_translation.verified IS '의학 전문가 검증 여부';
