-- ============================================
-- migration_user_cost_optimized.sql
-- User tables for cost optimization (Supabase/Postgres)
-- ============================================

begin;

-- 0) (Optional) extension checks (pgvector already in use)
-- create extension if not exists vector;

-- 1) user_profiles (thin profile table)
create table if not exists public.user_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  locale text default 'ko-KR',
  timezone text default 'Asia/Seoul',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_user_profiles_locale on public.user_profiles(locale);

-- 2) user_bookmarks (reduce repeated searches/AI calls)
create table if not exists public.user_bookmarks (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  target_type text not null check (target_type in ('food','prescription','disease','ingredient')),
  target_id bigint,
  target_text text,
  note text,
  created_at timestamptz default now()
);

create index if not exists idx_user_bookmarks_user_created
  on public.user_bookmarks(user_id, created_at desc);

create index if not exists idx_user_bookmarks_type
  on public.user_bookmarks(target_type);

-- 3) user_request_dedupe (avoid duplicate requests -> reuse results)
create table if not exists public.user_request_dedupe (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  request_type text not null check (request_type in ('symptom_search','ingredient_search','youtube','commerce')),
  request_hash varchar(64) not null,
  result jsonb not null,                 -- store final response OR references (ai_jobs id etc.)
  expires_at timestamptz not null,
  created_at timestamptz default now(),
  unique (user_id, request_type, request_hash)
);

create index if not exists idx_user_request_dedupe_expires
  on public.user_request_dedupe(expires_at);

create index if not exists idx_user_request_dedupe_user_created
  on public.user_request_dedupe(user_id, created_at desc);

-- 4) user_quota_monthly (hard guardrails against cost spikes)
create table if not exists public.user_quota_monthly (
  user_id uuid not null references auth.users(id) on delete cascade,
  month_yyyymm char(6) not null, -- e.g. '202601'
  ai_requests_limit int default 200,
  ai_requests_used int default 0,
  ext_api_limit int default 500,
  ext_api_used int default 0,
  updated_at timestamptz default now(),
  primary key (user_id, month_yyyymm)
);

create index if not exists idx_user_quota_month
  on public.user_quota_monthly(month_yyyymm);

-- 5) user_daily_stats (avoid expensive GROUP BY on large logs)
create table if not exists public.user_daily_stats (
  user_id uuid not null references auth.users(id) on delete cascade,
  ymd date not null,
  searches int default 0,
  ai_searches int default 0,
  cache_hits int default 0,
  bookmarks_added int default 0,
  last_active_at timestamptz,
  primary key (user_id, ymd)
);

create index if not exists idx_user_daily_stats_recent
  on public.user_daily_stats(user_id, ymd desc);

-- 6) user_preferences (existing table) - add cost-control switches
-- NOTE: If public.user_preferences does not exist yet, create it in your main schema migration first.
alter table public.user_preferences
  add column if not exists ai_personalization_level smallint default 0,
  add column if not exists save_search_history boolean default true;

-- ============================================
-- RLS enable
-- ============================================
alter table public.user_profiles enable row level security;
alter table public.user_bookmarks enable row level security;
alter table public.user_request_dedupe enable row level security;
alter table public.user_quota_monthly enable row level security;
alter table public.user_daily_stats enable row level security;

-- ============================================
-- RLS Policies (idempotent via DO blocks)
-- ============================================

-- user_profiles policies
do $$
begin
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='user_profiles' and policyname='profile_select_own'
  ) then
    create policy profile_select_own on public.user_profiles
      for select using (auth.uid() = user_id);
  end if;

  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='user_profiles' and policyname='profile_insert_own'
  ) then
    create policy profile_insert_own on public.user_profiles
      for insert with check (auth.uid() = user_id);
  end if;

  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='user_profiles' and policyname='profile_update_own'
  ) then
    create policy profile_update_own on public.user_profiles
      for update using (auth.uid() = user_id);
  end if;
end$$;

-- user_bookmarks policies (user can manage own)
do $$
begin
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='user_bookmarks' and policyname='bookmarks_own_all'
  ) then
    create policy bookmarks_own_all on public.user_bookmarks
      for all
      using (auth.uid() = user_id)
      with check (auth.uid() = user_id);
  end if;
end$$;

-- user_daily_stats policies (read own; writes typically by service role)
do $$
begin
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='user_daily_stats' and policyname='daily_stats_select_own'
  ) then
    create policy daily_stats_select_own on public.user_daily_stats
      for select using (auth.uid() = user_id);
  end if;
end$$;

-- user_request_dedupe policies:
-- - allow user to read own cached results
-- - writes/updates recommended via service role key (bypasses RLS)
do $$
begin
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='user_request_dedupe' and policyname='dedupe_select_own'
  ) then
    create policy dedupe_select_own on public.user_request_dedupe
      for select using (auth.uid() = user_id);
  end if;
end$$;

-- user_quota_monthly policies:
-- - allow user to read own quota
-- - writes/updates recommended via service role key (bypasses RLS)
do $$
begin
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='user_quota_monthly' and policyname='quota_select_own'
  ) then
    create policy quota_select_own on public.user_quota_monthly
      for select using (auth.uid() = user_id);
  end if;
end$$;

commit;

-- ============================================
-- Notes:
-- 1) user_request_dedupe / user_quota_monthly updates should be done by backend using SERVICE_ROLE
--    (service role bypasses RLS), or create dedicated RPC functions with security definer.
-- 2) Consider adding a scheduled job to delete expired dedupe rows:
--    delete from public.user_request_dedupe where expires_at < now();
-- ============================================
