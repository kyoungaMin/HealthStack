docs/ai_context.md를 공통 컨텍스트로 사용해.

목표:
traditional_foods 약 32만건을 임베딩하되, 비용 절감을 위해 "유니크 텍스트 캐시(content_hash+model)" 기반으로만 임베딩을 생성한다.
행(row) 단위 row_full 전수 임베딩은 금지한다. content_type별 "짧은 표준 텍스트"만 임베딩한다.

현재 DB:
Supabase(Postgres+pgvector)
테이블 public.embeddings 스키마:
- id bigserial PK
- source_table varchar(50) not null
- source_id bigint not null
- content_type varchar(50) not null
- content text not null
- content_hash varchar(64) not null
- embedding vector null
- model varchar(50) default 'text-embedding-3-small'
- tokens_used int null
- created_at/updated_at
유니크 제약: (source_table, source_id, content_type)
HNSW 인덱스는 이미 생성 성공(embedding vector_cosine_ops).

추가로 반드시 확인/적용:
1) 캐시용 유니크 인덱스가 없으면 생성:
   create unique index if not exists uq_embeddings_content_hash_model on public.embeddings(content_hash, model);

임베딩 정책:
- content_type을 아래로 표준화하고, 각 타입별 텍스트는 짧게 만든다.
  1) indication: 효능/적응증 요약 (한글 중심, 1~2문장 + 키워드)
  2) food_entity: 전통명/대표명/분류/대표재료(짧게)
  3) prescription_entity: 처방명/현대명/별칭(짧게, 없다면 생략)
  4) ingredients_core: 대표 재료 1~5개만 (동의어/한문 원문/빈값 제거)

- 아래와 같은 raw 예시(재료에 동의어+한문 원문+빈값이 많음)를 토큰 절감 규칙으로 정규화해야 한다.
  예: 
  적응증: 기를 아주 잘 내린다./大下氣.
  전통명: 곰국
  처방: 무
  설명: 기를 아주 잘 내린다.
  재료: [蘿葍,나복,...,무,...,蘿葍辛而又甘...]
  종류: 식재료명

구현 요구사항(파이썬):
- 파일: embed_pipeline.py 하나로 작성(모듈형 함수 포함)
- .env 사용: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY
- OpenAI 임베딩 모델: text-embedding-3-small (기본)
- 처리 흐름은 반드시 아래 순서를 지킬 것:
  1) row → content_type별 표준 텍스트 content 생성 (build_content)
  2) content_hash = sha256(content)
  3) Supabase에서 (content_hash, model) 존재 여부 조회 → 존재하면 OpenAI 호출 스킵
  4) 없으면 OpenAI 임베딩 생성 → embeddings 테이블 insert
     - tokens_used 기록
  5) source_table/source_id/content_type 매핑도 유지되어야 함.
     - 단, 동일 content_hash로 캐시 재사용이 되도록 설계할 것
- 에러 처리:
  - rate limit/네트워크 오류에 지수 백오프 재시도
  - 실패 항목은 로그에 남기고 계속 진행
- 재개(resume):
  - checkpoint 파일(예: checkpoints/<source_table>_<content_type>.json)에 last_source_id 저장
  - 중단 후 다시 실행하면 이어서 처리
- 성능:
  - 배치 size 옵션(예: 50~200)
  - 캐시 조회는 한번에 묶어서(batch select) 가능하면 최적화(가능한 범위에서)
- 로그:
  - 처리 건수, 새 임베딩 생성 수, 캐시 히트 수, 평균 tokens_used를 주기적으로 출력

또한 아래 2개의 SQL 모니터링 쿼리를 README 또는 docs/embedding_and_search_design.md에 포함해줘:
1) 전체 임베딩 수:
   select count(*) from public.embeddings where embedding is not null;
2) content_type별 분포:
   select content_type, count(*) from public.embeddings where embedding is not null group by content_type order by count(*) desc;

출력:
1) embed_pipeline.py 전체 코드
2) 실행 방법:
   - python embed_pipeline.py --source-table traditional_foods --content-type indication --limit 1000
   - 재개 옵션 예시
3) content 정규화 규칙 설명(짧게)
