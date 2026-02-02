# Database 모듈 가이드

DB 담당자가 설계한 스키마를 기반으로 한 Supabase 데이터베이스 모듈입니다.

## 디렉토리 구조

```
database/
├── __init__.py              # 모듈 초기화
├── supabase_client.py       # Supabase 클라이언트 (기존)
├── test_connection.py       # 연결 테스트 (기존)
├── schema.sql               # 데이터베이스 스키마 (NEW)
├── mock_data.py             # 목업 데이터 생성 (NEW)
├── seed_data.py             # 데이터 삽입 스크립트 (NEW)
├── test_crud.py             # CRUD 테스트 (NEW)
└── README.md                # 이 파일
```

## 데이터베이스 스키마

### products 테이블
iHerb 건강기능식품 제품 정보

| 컬럼                | 타입      | 설명                        |
|---------------------|-----------|----------------------------|
| id                  | BIGSERIAL | 기본키 (자동 생성)          |
| source              | TEXT      | 출처 (기본값: 'iherb')      |
| source_product_id   | TEXT      | iHerb 상품 ID              |
| url                 | TEXT      | 제품 URL                   |
| title               | TEXT      | 제품명                     |
| brand               | TEXT      | 브랜드명                   |
| category            | TEXT      | 카테고리                   |
| price               | NUMERIC   | 가격                       |
| currency            | TEXT      | 통화 (기본값: 'USD')       |
| rating_avg          | NUMERIC   | 평균 평점                  |
| rating_count        | INT       | 평점 개수                  |
| created_at          | TIMESTAMPTZ | 생성 시간                |
| updated_at          | TIMESTAMPTZ | 수정 시간 (자동 갱신)    |

**제약조건**: `UNIQUE(source, source_product_id)`

### reviews 테이블
iHerb 제품 리뷰 데이터

| 컬럼                | 타입      | 설명                        |
|---------------------|-----------|----------------------------|
| id                  | BIGSERIAL | 기본키 (자동 생성)          |
| product_id          | BIGINT    | 제품 FK (CASCADE 삭제)     |
| source              | TEXT      | 출처 (기본값: 'iherb')      |
| source_review_id    | TEXT      | iHerb 리뷰 ID (선택)       |
| author              | TEXT      | 작성자                     |
| rating              | INT       | 평점 (1-5)                 |
| title               | TEXT      | 리뷰 제목                  |
| body                | TEXT      | 리뷰 본문                  |
| language            | TEXT      | 언어 (기본값: 'ko')        |
| review_date         | DATE      | 리뷰 작성일                |
| helpful_count       | INT       | 도움이 됨 투표 수          |
| created_at          | TIMESTAMPTZ | 생성 시간                |

**제약조건**: `UNIQUE(source, source_review_id)`

## 목업 데이터

### 제품 데이터 (5종)
- Now Foods - Lutein 10mg
- Jarrow Formulas - Lutein 20mg
- Doctor's Best - Lutein with OptiLut 10mg
- Solgar - Lutein 20mg
- Life Extension - MacuGuard Ocular Support

### 리뷰 데이터 (100개)
- 제품당 20개 리뷰
- 정상 리뷰 60% (12개/제품)
- 광고성 리뷰 40% (8개/제품)
- 팩트체크 시스템 테스트용

## 사용 방법

### 1. 환경 설정

#### 1.1 .env 파일 생성

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# Anthropic Claude API
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Supabase 설정
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

**Supabase 키 확인 방법**:
1. [Supabase Dashboard](https://supabase.com/dashboard) 접속
2. 프로젝트 선택
3. **Settings** → **API** 메뉴
4. Project URL, anon key, service_role key 복사

#### 1.2 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 데이터베이스 스키마 적용

Supabase Dashboard → **SQL Editor**에서 `database/schema.sql` 실행:

```bash
# SQL 파일 내용을 복사하여 Supabase SQL Editor에 붙여넣고 실행
```

또는 Supabase CLI 사용:
```bash
supabase db push
```

### 3. 연결 테스트

```bash
python database/test_connection.py
```

**예상 출력**:
```
==================================================
Supabase 연결 테스트
==================================================

✅ Supabase 연결 성공!

📊 Supabase URL: https://your-project.supabase.co
🔑 API Key 설정: ✅
```

### 4. 목업 데이터 삽입

```bash
python database/seed_data.py
```

**실행 과정**:
1. 기존 데이터 삭제 여부 확인 (선택)
2. 제품 5개 삽입
3. 리뷰 100개 삽입
4. 데이터 검증

**예상 출력**:
```
============================================================
🚀 Supabase 목업 데이터 삽입 시작
============================================================
✅ Supabase 연결 성공

📦 제품 데이터 삽입 중...
  ✅ [1/5] Now Foods - Lutein, 10 mg, 120 Softgels...
  ✅ [2/5] Jarrow Formulas - Lutein, 20 mg, 60 Softgels...
  ...

💬 리뷰 데이터 삽입 중...
  ✅ [1/5] Lutein, 10 mg, 120 Softgel... - 20개 리뷰 삽입
  ...

🔍 데이터 검증 중...
  ✅ 총 제품 수: 5개
  ✅ 총 리뷰 수: 100개

============================================================
✅ 목업 데이터 삽입 완료!
============================================================
```

### 5. CRUD 테스트 실행

```bash
python database/test_crud.py
```

**테스트 항목**:
1. 제품 생성 (CREATE)
2. 제품 조회 (READ)
3. 제품 수정 (UPDATE)
4. 리뷰 생성 (CREATE)
5. 리뷰 조회 (READ)
6. 리뷰 수정 (UPDATE)
7. 조인 쿼리 (JOIN)
8. 리뷰 삭제 (DELETE)
9. 제품 삭제 (DELETE)

**예상 출력**:
```
============================================================
🧪 Supabase CRUD 테스트 시작
============================================================

📝 CREATE 테스트 - 제품 생성
✅ 제품 생성 성공!

📖 READ 테스트 - 제품 조회
✅ 전체 제품 수: 5개
...

📊 테스트 결과 요약
============================================================
  ✅ PASS - 제품 생성
  ✅ PASS - 제품 조회
  ...

총 9/9개 테스트 통과
============================================================
```

## Python 코드에서 사용

### 기본 사용

```python
from database import get_supabase_client

# 클라이언트 가져오기
supabase = get_supabase_client()

# 제품 조회
products = supabase.table('products').select('*').execute()
print(f"총 {len(products.data)}개 제품")

# 특정 브랜드 조회
now_foods = supabase.table('products')\
    .select('*')\
    .eq('brand', 'Now Foods')\
    .execute()

# 제품의 리뷰 조회 (조인)
reviews = supabase.table('reviews')\
    .select('*, products(brand, title)')\
    .eq('product_id', 1)\
    .execute()
```

### 관리자 권한 사용

```python
from database import get_supabase_service_client

# 서비스 역할 클라이언트 (RLS 우회)
supabase = get_supabase_service_client()

# 대량 삽입, 삭제 등 관리 작업 수행
```

### 목업 데이터 직접 사용

```python
from database.mock_data import get_all_mock_data

# 목업 데이터 가져오기
data = get_all_mock_data()

print(f"제품 수: {len(data['products'])}")
print(f"리뷰 수: {len(data['reviews'])}")
```

## 쿼리 예제

### 1. 제품 검색

```python
# 가격 범위 검색
products = supabase.table('products')\
    .select('*')\
    .gte('price', 15.0)\
    .lte('price', 20.0)\
    .execute()

# 브랜드별 정렬
products = supabase.table('products')\
    .select('*')\
    .order('brand')\
    .execute()
```

### 2. 리뷰 분석

```python
# 평점별 리뷰 수
rating_counts = {}
for rating in range(1, 6):
    result = supabase.table('reviews')\
        .select('id', count='exact')\
        .eq('rating', rating)\
        .execute()
    rating_counts[rating] = result.count

# 최근 리뷰
recent_reviews = supabase.table('reviews')\
    .select('*')\
    .order('review_date', desc=True)\
    .limit(10)\
    .execute()
```

### 3. 제품 + 리뷰 조인

```python
# 제품 정보와 함께 리뷰 조회
reviews_with_product = supabase.table('reviews')\
    .select('*, products(brand, title, price)')\
    .execute()

for review in reviews_with_product.data:
    print(f"[{review['rating']}★] {review['title']}")
    print(f"제품: {review['products']['brand']} - {review['products']['title']}")
```

### 4. 통계 쿼리

```python
# 제품별 평균 평점 계산
products = supabase.table('products').select('id, brand, title').execute()

for product in products.data:
    reviews = supabase.table('reviews')\
        .select('rating')\
        .eq('product_id', product['id'])\
        .execute()

    if reviews.data:
        avg_rating = sum(r['rating'] for r in reviews.data) / len(reviews.data)
        print(f"{product['brand']}: {avg_rating:.2f}점 (리뷰 {len(reviews.data)}개)")
```

## 문제 해결

### 연결 실패
1. `.env` 파일이 프로젝트 루트에 있는지 확인
2. 환경 변수 이름 확인 (대소문자 구분)
3. Supabase 프로젝트 활성화 여부 확인

### 데이터 삽입 오류
1. 스키마가 적용되었는지 확인 (`schema.sql` 실행)
2. UNIQUE 제약조건 충돌 확인 (기존 데이터 삭제)
3. 외래키 제약조건 확인 (product_id 존재 여부)

### 권한 오류
1. `SUPABASE_SERVICE_ROLE_KEY` 사용 확인
2. RLS(Row Level Security) 정책 확인
3. 테이블 권한 설정 확인

## 다음 단계

1. **팀원 B (logic_designer)**: 리뷰 분석 로직과 연동
2. **팀원 C (ui_integration)**: Streamlit 대시보드에서 데이터 조회
3. **데이터 수집**: 실제 iHerb 스크래핑 (선택)

## 참고 자료

- [Supabase 공식 문서](https://supabase.com/docs)
- [Supabase Python 클라이언트](https://github.com/supabase/supabase-py)
- [프로젝트 Supabase 설정](../docs/SUPABASE_SETUP.md)
