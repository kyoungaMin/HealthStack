**Table 

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


create table public.foods_master (
  id bigserial not null,
  rep_code text not null,
  rep_name text null,
  created_at timestamp with time zone null default now(),
  constraint foods_master_pkey primary key (id),
  constraint foods_master_rep_code_key unique (rep_code)
) TABLESPACE pg_default;

create index IF not exists idx_foods_master_code on public.foods_master using btree (rep_code) TABLESPACE pg_default;

create table public.disease_master (
  id bigserial not null,
  disease text not null,
  disease_read text null,
  disease_alias text null,
  disease_alias_read text null,
  modern_disease text null,
  created_at timestamp with time zone null default now(),
  constraint disease_master_pkey primary key (id),
  constraint disease_master_disease_key unique (disease)
) TABLESPACE pg_default;

create index IF not exists idx_disease_master_modern on public.disease_master using btree (modern_disease) TABLESPACE pg_default;

create index IF not exists idx_disease_master_disease on public.disease_master using btree (disease) TABLESPACE pg_default;

create index IF not exists idx_disease_master_read on public.disease_master using btree (disease_read) TABLESPACE pg_default;

create table public.prescription_master (
  id bigserial not null,
  prescription text not null,
  prescription_read text null,
  prescription_modern text null,
  prescription_alias text null,
  created_at timestamp with time zone null default now(),
  constraint prescription_master_pkey primary key (id),
  constraint prescription_master_prescription_key unique (prescription)
) TABLESPACE pg_default;

create index IF not exists idx_prescription_master_presc on public.prescription_master using btree (prescription) TABLESPACE pg_default;

create index IF not exists idx_prescription_master_read on public.prescription_master using btree (prescription_read) TABLESPACE pg_default;

create index IF not exists idx_prescription_master_modern on public.prescription_master using btree (prescription_modern) TABLESPACE pg_default;