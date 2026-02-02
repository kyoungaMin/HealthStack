-- ============================================================
-- Health Stack: 전체 마이그레이션 (DDL + RLS)
-- 대상: Supabase Postgres (public schema)
-- 포함:
--  1) 확장(extensions)
--  2) 테이블/인덱스/컬럼 보강(DDL)
--  3) RLS 활성화 + 정책 생성(Policy)
--
-- 실행 방법:
--  - Supabase SQL Editor에서 "한 번에" 실행
--
-- 전제:
--  - 기존 테이블 존재 가정:
--    public.user_profiles, public.foods_master(rep_code), public.disease_master(id)
--  - 없을 경우 FK 생성 단계에서 실패합니다.
--
-- 설계 원칙:
--  - 개인 데이터 테이블: user_id = auth.uid()만 접근(CRUD)
--  - 공용 데이터 테이블: SELECT 공개(anon/authenticated), 쓰기 정책 없음(= service_role만 가능)
-- ============================================================

begin;

-- 0) Extensions ------------------------------------------------
create extension if not exists vector;

-- 1) user_profiles 확장 (생활시간) -----------------------------
alter table if exists public.user_profiles
  add column if not exists wake_time time,
  add column if not exists breakfast_time time,
  add column if not exists lunch_time time,
  add column if not exists dinner_time time,
  add column if not exists bed_time time;

-- 2) 카탈로그 (약/건기식 표준) ---------------------------------
create table if not exists public.catalog_drugs (
  id bigserial primary key,
  name text not null,
  generic_name text,
  atc_code text,
  notes text,
  source text,
  updated_at timestamptz default now()
);

create table if not exists public.catalog_supplements (
  id bigserial primary key,
  name text not null,
  ingredient text,
  category text,
  notes text,
  updated_at timestamptz default now()
);

create index if not exists idx_catalog_drugs_name on public.catalog_drugs (name);
create index if not exists idx_catalog_supplements_name on public.catalog_supplements (name);

-- 3) 사용자 복용 스택 ------------------------------------------
create table if not exists public.user_intake_items (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,

  item_type text not null check (item_type in ('drug','supplement','food','tea')),

  catalog_drug_id bigint references public.catalog_drugs(id),
  catalog_supplement_id bigint references public.catalog_supplements(id),
  rep_code text references public.foods_master(rep_code),

  display_name text not null,
  dose_text text,
  route text,
  active boolean default true,

  created_at timestamptz default now(),
  updated_at timestamptz default now(),

  check (
    (item_type='drug' and catalog_drug_id is not null) or
    (item_type='supplement' and catalog_supplement_id is not null) or
    (item_type in ('food','tea') and rep_code is not null) or
    (catalog_drug_id is null and catalog_supplement_id is null and rep_code is null)
  )
);

create index if not exists idx_user_intake_items_user on public.user_intake_items(user_id);
create index if not exists idx_user_intake_items_type on public.user_intake_items(user_id, item_type);

-- 4) 복용 시간표 + 로그 ----------------------------------------
create table if not exists public.intake_schedules (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  intake_item_id bigint not null references public.user_intake_items(id) on delete cascade,

  pattern text not null check (pattern in ('daily','weekly','custom')),
  days_of_week int[],

  time_anchor text not null check (time_anchor in ('wake','breakfast','lunch','dinner','bed','custom_time')),
  custom_time time,
  offset_minutes int default 0,

  rules jsonb default '{}'::jsonb,
  is_enabled boolean default true,

  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_intake_schedules_user on public.intake_schedules(user_id);
create index if not exists idx_intake_schedules_item on public.intake_schedules(intake_item_id);

create table if not exists public.intake_logs (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  schedule_id bigint not null references public.intake_schedules(id) on delete cascade,

  scheduled_at timestamptz not null,
  taken_at timestamptz,
  status text not null check (status in ('scheduled','taken','skipped','snoozed')),
  note text,

  created_at timestamptz default now()
);

create index if not exists idx_intake_logs_user_date on public.intake_logs(user_id, scheduled_at desc);
create index if not exists idx_intake_logs_schedule on public.intake_logs(schedule_id, scheduled_at desc);

-- 5) 알림 토큰 -------------------------------------------------
create table if not exists public.user_push_tokens (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  platform text not null check (platform in ('ios','android','web')),
  token text not null,
  enabled boolean default true,
  last_seen_at timestamptz default now(),
  created_at timestamptz default now(),
  unique(user_id, platform, token)
);

create index if not exists idx_user_push_tokens_user on public.user_push_tokens(user_id);

-- 6) 상호작용 지식베이스 ---------------------------------------
create table if not exists public.interaction_facts (
  id bigserial primary key,

  a_type text not null check (a_type in ('drug','supplement','food')),
  a_ref text not null,
  b_type text not null check (b_type in ('drug','supplement','food')),
  b_ref text not null,

  severity text not null check (severity in ('low','moderate','high')),
  evidence_level text not null check (evidence_level in ('established','likely','limited')),

  mechanism text,
  summary_ko text not null,
  action_ko text,
  sources jsonb,
  pmids text[],

  updated_at timestamptz default now(),

  unique(a_type, a_ref, b_type, b_ref)
);

create index if not exists idx_interaction_a on public.interaction_facts(a_type, a_ref);
create index if not exists idx_interaction_b on public.interaction_facts(b_type, b_ref);

-- 7) 증상 ↔ 식재료/레시피/영상 큐레이션 -------------------------
create table if not exists public.symptom_ingredient_map (
  id bigserial primary key,
  symptom_id bigint not null references public.disease_master(id) on delete cascade,
  rep_code text not null references public.foods_master(rep_code),

  direction text not null check (direction in ('helpful','avoid')),
  rationale_ko text,
  priority int default 100,

  created_at timestamptz default now(),
  unique(symptom_id, rep_code, direction)
);

create index if not exists idx_symptom_ingredient_priority
  on public.symptom_ingredient_map(symptom_id, priority);

create table if not exists public.recipes (
  id bigserial primary key,
  title text not null,
  description text,
  ingredients jsonb not null,
  steps jsonb not null,
  tags text[],
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.symptom_recipe_map (
  id bigserial primary key,
  symptom_id bigint not null references public.disease_master(id) on delete cascade,
  recipe_id bigint not null references public.recipes(id) on delete cascade,
  meal_slot text check (meal_slot in ('breakfast','lunch','dinner','snack')),
  priority int default 100,
  unique(symptom_id, recipe_id)
);

create index if not exists idx_symptom_recipe_priority
  on public.symptom_recipe_map(symptom_id, priority);

create table if not exists public.content_videos (
  id bigserial primary key,
  provider text not null default 'youtube',
  video_id text not null,
  title text,
  channel text,
  tags text[],
  created_at timestamptz default now(),
  unique(provider, video_id)
);

create table if not exists public.symptom_video_map (
  id bigserial primary key,
  symptom_id bigint not null references public.disease_master(id) on delete cascade,
  video_pk bigint not null references public.content_videos(id) on delete cascade,
  priority int default 100,
  unique(symptom_id, video_pk)
);

create index if not exists idx_symptom_video_priority
  on public.symptom_video_map(symptom_id, priority);

create table if not exists public.ingredient_product_links (
  id bigserial primary key,
  rep_code text not null references public.foods_master(rep_code),
  provider text not null,
  query_template text not null,
  disclaimer_ko text,
  created_at timestamptz default now(),
  unique(rep_code, provider)
);

create index if not exists idx_ingredient_product_links_rep on public.ingredient_product_links(rep_code);

-- 8) PDF 리포트 -------------------------------------------------
create table if not exists public.reports (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,

  report_type text not null check (report_type in ('stack_safety','symptom_mealplan','family_check')),
  title text,
  inputs jsonb not null,
  content_md text,
  pdf_path text,
  status text not null default 'draft' check (status in ('draft','generated','failed')),

  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_reports_user_date on public.reports(user_id, created_at desc);

-- 9) 구독/결제 --------------------------------------------------
create table if not exists public.plans (
  id bigserial primary key,
  code text unique not null,
  name text not null,
  price int not null default 0,
  currency text not null default 'KRW',
  features jsonb not null default '{}'::jsonb,
  is_active boolean default true
);

create table if not exists public.subscriptions (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  plan_code text not null references public.plans(code),

  status text not null check (status in ('active','past_due','canceled','expired')),
  current_period_start timestamptz,
  current_period_end timestamptz,

  provider text,
  provider_sub_id text,

  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

do $$
begin
  if not exists (
    select 1 from pg_indexes
    where schemaname='public' and indexname='uq_subscriptions_user_active'
  ) then
    execute 'create unique index uq_subscriptions_user_active on public.subscriptions(user_id) where (status = ''active'')';
  end if;
end$$;

create index if not exists idx_subscriptions_user on public.subscriptions(user_id, status);

create table if not exists public.payments (
  id bigserial primary key,
  user_id uuid references auth.users(id) on delete set null,

  amount int not null,
  currency text not null default 'KRW',

  provider text not null,
  provider_payment_id text not null,

  payment_type text not null check (payment_type in ('subscription','report')),
  reference_id bigint,

  status text not null check (status in ('paid','failed','refunded')),
  created_at timestamptz default now(),

  unique(provider, provider_payment_id)
);

create index if not exists idx_payments_user_date on public.payments(user_id, created_at desc);

-- 10) PubMed RAG 저장 레이어 -----------------------------------
create table if not exists public.pubmed_papers (
  pmid text primary key,
  title text not null,
  abstract text,
  journal text,
  pub_year int,
  publication_types text[],
  mesh_terms text[],
  url text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.pubmed_embeddings (
  pmid text not null references public.pubmed_papers(pmid) on delete cascade,
  chunk_index int not null,
  content text not null,
  embedding vector(1536),
  created_at timestamptz default now(),
  primary key (pmid, chunk_index)
);

do $$
begin
  if not exists (
    select 1 from pg_indexes
    where schemaname='public' and indexname='idx_pubmed_embeddings_vec'
  ) then
    execute 'create index idx_pubmed_embeddings_vec on public.pubmed_embeddings using ivfflat (embedding vector_cosine_ops) with (lists = 100)';
  end if;
end$$;

create index if not exists idx_pubmed_embeddings_pmid on public.pubmed_embeddings(pmid);

-- ============================================================
-- RLS + POLICIES
-- ============================================================

-- Helper: drop policy if exists (safe re-run)
-- (Postgres supports: drop policy if exists <name> on <table>)
-- We'll use fixed policy names to avoid duplicates.

-- 11) 개인 데이터 테이블: RLS ON + 본인만 CRUD -------------------

-- user_profiles (이미 있을 수 있음)
alter table if exists public.user_profiles enable row level security;

drop policy if exists "profiles_select_own" on public.user_profiles;
create policy "profiles_select_own"
on public.user_profiles for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "profiles_insert_own" on public.user_profiles;
create policy "profiles_insert_own"
on public.user_profiles for insert
to authenticated
with check (user_id = auth.uid());

drop policy if exists "profiles_update_own" on public.user_profiles;
create policy "profiles_update_own"
on public.user_profiles for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

drop policy if exists "profiles_delete_own" on public.user_profiles;
create policy "profiles_delete_own"
on public.user_profiles for delete
to authenticated
using (user_id = auth.uid());

-- user_intake_items
alter table public.user_intake_items enable row level security;

drop policy if exists "intake_items_select_own" on public.user_intake_items;
create policy "intake_items_select_own"
on public.user_intake_items for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "intake_items_insert_own" on public.user_intake_items;
create policy "intake_items_insert_own"
on public.user_intake_items for insert
to authenticated
with check (user_id = auth.uid());

drop policy if exists "intake_items_update_own" on public.user_intake_items;
create policy "intake_items_update_own"
on public.user_intake_items for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

drop policy if exists "intake_items_delete_own" on public.user_intake_items;
create policy "intake_items_delete_own"
on public.user_intake_items for delete
to authenticated
using (user_id = auth.uid());

-- intake_schedules
alter table public.intake_schedules enable row level security;

drop policy if exists "schedules_select_own" on public.intake_schedules;
create policy "schedules_select_own"
on public.intake_schedules for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "schedules_insert_own" on public.intake_schedules;
create policy "schedules_insert_own"
on public.intake_schedules for insert
to authenticated
with check (user_id = auth.uid());

drop policy if exists "schedules_update_own" on public.intake_schedules;
create policy "schedules_update_own"
on public.intake_schedules for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

drop policy if exists "schedules_delete_own" on public.intake_schedules;
create policy "schedules_delete_own"
on public.intake_schedules for delete
to authenticated
using (user_id = auth.uid());

-- intake_logs
alter table public.intake_logs enable row level security;

drop policy if exists "logs_select_own" on public.intake_logs;
create policy "logs_select_own"
on public.intake_logs for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "logs_insert_own" on public.intake_logs;
create policy "logs_insert_own"
on public.intake_logs for insert
to authenticated
with check (user_id = auth.uid());

drop policy if exists "logs_update_own" on public.intake_logs;
create policy "logs_update_own"
on public.intake_logs for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

drop policy if exists "logs_delete_own" on public.intake_logs;
create policy "logs_delete_own"
on public.intake_logs for delete
to authenticated
using (user_id = auth.uid());

-- user_push_tokens
alter table public.user_push_tokens enable row level security;

drop policy if exists "push_tokens_select_own" on public.user_push_tokens;
create policy "push_tokens_select_own"
on public.user_push_tokens for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "push_tokens_insert_own" on public.user_push_tokens;
create policy "push_tokens_insert_own"
on public.user_push_tokens for insert
to authenticated
with check (user_id = auth.uid());

drop policy if exists "push_tokens_update_own" on public.user_push_tokens;
create policy "push_tokens_update_own"
on public.user_push_tokens for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

drop policy if exists "push_tokens_delete_own" on public.user_push_tokens;
create policy "push_tokens_delete_own"
on public.user_push_tokens for delete
to authenticated
using (user_id = auth.uid());

-- reports
alter table public.reports enable row level security;

drop policy if exists "reports_select_own" on public.reports;
create policy "reports_select_own"
on public.reports for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "reports_insert_own" on public.reports;
create policy "reports_insert_own"
on public.reports for insert
to authenticated
with check (user_id = auth.uid());

drop policy if exists "reports_update_own" on public.reports;
create policy "reports_update_own"
on public.reports for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

drop policy if exists "reports_delete_own" on public.reports;
create policy "reports_delete_own"
on public.reports for delete
to authenticated
using (user_id = auth.uid());

-- subscriptions
alter table public.subscriptions enable row level security;

drop policy if exists "subs_select_own" on public.subscriptions;
create policy "subs_select_own"
on public.subscriptions for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "subs_insert_own" on public.subscriptions;
create policy "subs_insert_own"
on public.subscriptions for insert
to authenticated
with check (user_id = auth.uid());

drop policy if exists "subs_update_own" on public.subscriptions;
create policy "subs_update_own"
on public.subscriptions for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

drop policy if exists "subs_delete_own" on public.subscriptions;
create policy "subs_delete_own"
on public.subscriptions for delete
to authenticated
using (user_id = auth.uid());

-- payments
alter table public.payments enable row level security;

drop policy if exists "payments_select_own" on public.payments;
create policy "payments_select_own"
on public.payments for select
to authenticated
using (user_id = auth.uid());

-- 결제 이벤트는 보통 서버(webhook, service_role)만 insert/update 합니다.
-- 따라서 사용자 insert/update/delete 정책은 만들지 않습니다.
-- (service_role은 RLS를 우회)
-- 필요 시, client에서 결제 시도 기록을 남기려면 별도 테이블을 두는 것을 권장.

-- 12) 공용 데이터 테이블: RLS ON + SELECT 공개 ------------------
-- (쓰기 정책 없음 => anon/authenticated는 INSERT/UPDATE/DELETE 불가)

-- catalog_drugs
alter table public.catalog_drugs enable row level security;

drop policy if exists "catalog_drugs_read" on public.catalog_drugs;
create policy "catalog_drugs_read"
on public.catalog_drugs for select
to anon, authenticated
using (true);

-- catalog_supplements
alter table public.catalog_supplements enable row level security;

drop policy if exists "catalog_supplements_read" on public.catalog_supplements;
create policy "catalog_supplements_read"
on public.catalog_supplements for select
to anon, authenticated
using (true);

-- interaction_facts
alter table public.interaction_facts enable row level security;

drop policy if exists "interaction_facts_read" on public.interaction_facts;
create policy "interaction_facts_read"
on public.interaction_facts for select
to anon, authenticated
using (true);

-- symptom_ingredient_map
alter table public.symptom_ingredient_map enable row level security;

drop policy if exists "symptom_ingredient_read" on public.symptom_ingredient_map;
create policy "symptom_ingredient_read"
on public.symptom_ingredient_map for select
to anon, authenticated
using (true);

-- recipes
alter table public.recipes enable row level security;

drop policy if exists "recipes_read" on public.recipes;
create policy "recipes_read"
on public.recipes for select
to anon, authenticated
using (true);

-- symptom_recipe_map
alter table public.symptom_recipe_map enable row level security;

drop policy if exists "symptom_recipe_map_read" on public.symptom_recipe_map;
create policy "symptom_recipe_map_read"
on public.symptom_recipe_map for select
to anon, authenticated
using (true);

-- content_videos
alter table public.content_videos enable row level security;

drop policy if exists "content_videos_read" on public.content_videos;
create policy "content_videos_read"
on public.content_videos for select
to anon, authenticated
using (true);

-- symptom_video_map
alter table public.symptom_video_map enable row level security;

drop policy if exists "symptom_video_map_read" on public.symptom_video_map;
create policy "symptom_video_map_read"
on public.symptom_video_map for select
to anon, authenticated
using (true);

-- ingredient_product_links
alter table public.ingredient_product_links enable row level security;

drop policy if exists "ingredient_product_links_read" on public.ingredient_product_links;
create policy "ingredient_product_links_read"
on public.ingredient_product_links for select
to anon, authenticated
using (true);

-- plans (플랜 정보는 공개)
alter table public.plans enable row level security;

drop policy if exists "plans_read" on public.plans;
create policy "plans_read"
on public.plans for select
to anon, authenticated
using (true);

-- PubMed RAG: papers & embeddings (일반적으로는 읽기 허용)
alter table public.pubmed_papers enable row level security;
drop policy if exists "pubmed_papers_read" on public.pubmed_papers;
create policy "pubmed_papers_read"
on public.pubmed_papers for select
to anon, authenticated
using (true);

alter table public.pubmed_embeddings enable row level security;
drop policy if exists "pubmed_embeddings_read" on public.pubmed_embeddings;
create policy "pubmed_embeddings_read"
on public.pubmed_embeddings for select
to anon, authenticated
using (true);

commit;

-- ============================================================
-- 참고:
-- 1) payments는 client 쓰기 정책을 intentionally 미설정.
--    결제/구독/리포트 생성은 server(webhook/service_role)에서 처리 권장.
--
-- 2) pubmed_embeddings의 vector(1536)은 임베딩 모델 차원에 맞게 수정 필요.
-- ============================================================
