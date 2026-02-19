create table public.traditional_foods (
  id bigserial not null,
  rep_code text null,
  rep_name text null,
  trad_code text null,
  trad_name text null,
  disease text null,
  disease_read text null,
  disease_alias text null,
  disease_alias_read text null,
  modern_disease text null,
  disease_src text null,
  disease_src_read text null,
  disease_src_year text null,
  disease_src_section text null,
  disease_content text null,
  prescription text null,
  prescription_read text null,
  prescription_modern text null,
  prescription_alias text null,
  presc_src text null,
  presc_src_read text null,
  presc_src_year text null,
  presc_src_section text null,
  indication text null,
  etc text null,
  food_type text null,
  ingredients text null,
  preparation text null,
  dosage text null,
  created_at timestamp with time zone null default now(),
  constraint traditional_foods_pkey primary key (id)
) TABLESPACE pg_default;

create index IF not exists idx_tf_rep_code on public.traditional_foods using btree (rep_code) TABLESPACE pg_default;

create index IF not exists idx_tf_trad_code on public.traditional_foods using btree (trad_code) TABLESPACE pg_default;

create index IF not exists idx_tf_disease on public.traditional_foods using btree (disease) TABLESPACE pg_default;
