# Supabase Migrations

이 폴더는 Supabase CLI 마이그레이션 형식의 SQL 파일들을 포함합니다.

## 파일 명명 규칙

```
{YYYYMMDDHHMMSS}_{description}.sql
```

예: `20260206220000_extend_master_tables.sql`

## 마이그레이션 목록

| 타임스탬프 | 파일명 | 설명 |
|-----------|--------|------|
| 20260206220000 | extend_master_tables.sql | 마스터 테이블 확장 (foods_master, disease_master) |
| 20260206220100 | foods_master_seed.sql | 식재료 마스터 시드 (70+ 항목) |
| 20260206220200 | disease_master_seed.sql | 질환 마스터 시드 (55+ 항목) |
| 20260206220300 | tkm_symptom_master_seed.sql | TKM 증상 마스터 시드 (40+ 항목) |
| 20260206220400 | tkm_to_modern_map_seed.sql | TKM→현대 질환 매핑 (40+ 매핑) |
| 20260206220500 | symptom_ingredient_map_seed.sql | 증상→식재료 추천 (70+ 매핑) |
| 20260206220600 | recipes_symptom_recipe_map_seed.sql | 레시피 + 증상→레시피 매핑 |
| 20260206220700 | pubmed_search_seed.sql | PubMed MeSH/키워드/화합물 |

## 실행 방법

### 1. Supabase CLI 사용 (권장)

```bash
# Supabase CLI 초기화 (최초 1회)
supabase init

# 로컬 DB에 마이그레이션 적용
supabase db reset

# 리모트 DB에 마이그레이션 적용
supabase db push
```

### 2. 수동 실행 (Supabase Dashboard)

1. [Supabase Dashboard](https://app.supabase.com) 접속
2. 프로젝트 선택 → SQL Editor
3. 타임스탬프 순서대로 각 파일 내용 붙여넣기 → Run

### 3. psql 사용

```bash
# 환경 변수 설정
export SUPABASE_URL=your-project-url
export SUPABASE_DB_PASSWORD=your-password

# 마이그레이션 실행
psql -h db.$SUPABASE_URL -U postgres -d postgres -f migrations/20260206220000_extend_master_tables.sql
```

## 주의사항

1. **순서 중요**: 타임스탬프 순서대로 실행해야 합니다 (FK 의존성)
2. **멱등성**: 대부분의 파일이 `ON CONFLICT DO UPDATE` 사용으로 재실행 가능
3. **롤백**: 현재 롤백 스크립트 없음 (필요시 별도 생성)

## 관련 파일

- 원본 SQL: `database/sql/`
- 스키마 문서: `docs/erd/schema.integrated.dbml`
- 테스트 질문: `docs/test/golden_questions_v1.md`
