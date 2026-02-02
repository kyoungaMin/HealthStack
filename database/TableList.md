| table_name          | column_name               | data_type                | is_nullable | column_default                                  | is_primary_key |
| ------------------- | ------------------------- | ------------------------ | ----------- | ----------------------------------------------- | -------------- |
| affiliate_clicks    | id                        | bigint                   | NO          | nextval('affiliate_clicks_id_seq'::regclass)    | 1              |
| affiliate_clicks    | session_id                | character varying        | YES         | null                                            | 0              |
| affiliate_clicks    | user_id                   | uuid                     | YES         | null                                            | 1              |
| affiliate_clicks    | food_id                   | bigint                   | YES         | null                                            | 1              |
| affiliate_clicks    | ingredient_name           | text                     | YES         | null                                            | 0              |
| affiliate_clicks    | provider                  | character varying        | NO          | null                                            | 0              |
| affiliate_clicks    | product_url               | text                     | NO          | null                                            | 0              |
| affiliate_clicks    | referrer                  | text                     | YES         | null                                            | 0              |
| affiliate_clicks    | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| ai_jobs             | id                        | bigint                   | NO          | nextval('ai_jobs_id_seq'::regclass)             | 1              |
| ai_jobs             | job_id                    | character varying        | NO          | null                                            | 1              |
| ai_jobs             | status                    | character varying        | YES         | 'queued'::character varying                     | 0              |
| ai_jobs             | job_type                  | character varying        | NO          | null                                            | 0              |
| ai_jobs             | input                     | jsonb                    | NO          | null                                            | 0              |
| ai_jobs             | result                    | jsonb                    | YES         | null                                            | 0              |
| ai_jobs             | error_message             | text                     | YES         | null                                            | 0              |
| ai_jobs             | models_used               | ARRAY                    | YES         | null                                            | 0              |
| ai_jobs             | tokens_used               | jsonb                    | YES         | null                                            | 0              |
| ai_jobs             | processing_time_ms        | integer                  | YES         | null                                            | 0              |
| ai_jobs             | retry_count               | integer                  | YES         | 0                                               | 0              |
| ai_jobs             | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| ai_jobs             | started_at                | timestamp with time zone | YES         | null                                            | 0              |
| ai_jobs             | completed_at              | timestamp with time zone | YES         | null                                            | 0              |
| commerce_cache      | id                        | bigint                   | NO          | nextval('commerce_cache_id_seq'::regclass)      | 1              |
| commerce_cache      | query_hash                | character varying        | NO          | null                                            | 1              |
| commerce_cache      | query                     | text                     | NO          | null                                            | 0              |
| commerce_cache      | provider                  | character varying        | NO          | null                                            | 0              |
| commerce_cache      | results                   | jsonb                    | NO          | null                                            | 0              |
| commerce_cache      | result_count              | integer                  | YES         | 0                                               | 0              |
| commerce_cache      | expires_at                | timestamp with time zone | NO          | null                                            | 0              |
| commerce_cache      | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| disease_master      | id                        | bigint                   | NO          | nextval('disease_master_id_seq'::regclass)      | 1              |
| disease_master      | disease                   | text                     | NO          | null                                            | 1              |
| disease_master      | disease_read              | text                     | YES         | null                                            | 0              |
| disease_master      | disease_alias             | text                     | YES         | null                                            | 0              |
| disease_master      | disease_alias_read        | text                     | YES         | null                                            | 0              |
| disease_master      | modern_disease            | text                     | YES         | null                                            | 0              |
| disease_master      | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| embeddings          | id                        | bigint                   | NO          | nextval('embeddings_id_seq'::regclass)          | 1              |
| embeddings          | source_table              | character varying        | NO          | null                                            | 1              |
| embeddings          | source_id                 | bigint                   | NO          | null                                            | 1              |
| embeddings          | content_type              | character varying        | NO          | null                                            | 1              |
| embeddings          | content                   | text                     | NO          | null                                            | 0              |
| embeddings          | content_hash              | character varying        | NO          | null                                            | 0              |
| embeddings          | embedding                 | USER-DEFINED             | YES         | null                                            | 0              |
| embeddings          | model                     | character varying        | YES         | 'text-embedding-3-small'::character varying     | 0              |
| embeddings          | tokens_used               | integer                  | YES         | null                                            | 0              |
| embeddings          | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| embeddings          | updated_at                | timestamp with time zone | YES         | now()                                           | 0              |
| foods_master        | id                        | bigint                   | NO          | nextval('foods_master_id_seq'::regclass)        | 1              |
| foods_master        | rep_code                  | text                     | NO          | null                                            | 1              |
| foods_master        | rep_name                  | text                     | YES         | null                                            | 0              |
| foods_master        | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| nutrition_info      | id                        | bigint                   | NO          | nextval('nutrition_info_id_seq'::regclass)      | 1              |
| nutrition_info      | food_code                 | text                     | NO          | null                                            | 1              |
| nutrition_info      | food_name                 | text                     | YES         | null                                            | 0              |
| nutrition_info      | data_category_code        | text                     | YES         | null                                            | 0              |
| nutrition_info      | data_category_name        | text                     | YES         | null                                            | 0              |
| nutrition_info      | food_origin_code          | text                     | YES         | null                                            | 0              |
| nutrition_info      | food_origin_name          | text                     | YES         | null                                            | 0              |
| nutrition_info      | food_large_category_code  | text                     | YES         | null                                            | 0              |
| nutrition_info      | food_large_category_name  | text                     | YES         | null                                            | 0              |
| nutrition_info      | representative_food_code  | text                     | YES         | null                                            | 0              |
| nutrition_info      | representative_food_name  | text                     | YES         | null                                            | 0              |
| nutrition_info      | food_medium_category_code | text                     | YES         | null                                            | 0              |
| nutrition_info      | food_medium_category_name | text                     | YES         | null                                            | 0              |
| nutrition_info      | food_small_category_code  | text                     | YES         | null                                            | 0              |
| nutrition_info      | food_small_category_name  | text                     | YES         | null                                            | 0              |
| nutrition_info      | food_detail_category_code | text                     | YES         | null                                            | 0              |
| nutrition_info      | food_detail_category_name | text                     | YES         | null                                            | 0              |
| nutrition_info      | type_name                 | text                     | YES         | null                                            | 0              |
| nutrition_info      | serving_unit              | text                     | YES         | null                                            | 0              |
| nutrition_info      | energy_kcal               | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | water_g                   | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | protein_g                 | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | fat_g                     | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | ash_g                     | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | carbohydrate_g            | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | sugar_g                   | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | dietary_fiber_g           | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | calcium_mg                | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | iron_mg                   | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | phosphorus_mg             | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | potassium_mg              | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | sodium_mg                 | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | vitamin_a_ug_rae          | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | retinol_ug                | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | beta_carotene_ug          | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | thiamine_mg               | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | riboflavin_mg             | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | niacin_mg                 | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | vitamin_c_mg              | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | vitamin_d_ug              | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | cholesterol_mg            | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | saturated_fatty_acid_g    | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | trans_fatty_acid_g        | numeric                  | YES         | null                                            | 0              |
| nutrition_info      | source_code               | text                     | YES         | null                                            | 0              |
| nutrition_info      | source_name               | text                     | YES         | null                                            | 0              |
| nutrition_info      | serving_size              | text                     | YES         | null                                            | 0              |
| nutrition_info      | serving_weight_volume     | text                     | YES         | null                                            | 0              |
| nutrition_info      | daily_intake_frequency    | text                     | YES         | null                                            | 0              |
| nutrition_info      | intake_target             | text                     | YES         | null                                            | 0              |
| nutrition_info      | food_weight_volume        | text                     | YES         | null                                            | 0              |
| nutrition_info      | product_report_number     | text                     | YES         | null                                            | 0              |
| nutrition_info      | manufacturer_name         | text                     | YES         | null                                            | 0              |
| nutrition_info      | importer_name             | text                     | YES         | null                                            | 0              |
| nutrition_info      | distributor_name          | text                     | YES         | null                                            | 0              |
| nutrition_info      | import_yn                 | text                     | YES         | null                                            | 0              |
| nutrition_info      | origin_country_code       | text                     | YES         | null                                            | 0              |
| nutrition_info      | origin_country_name       | text                     | YES         | null                                            | 0              |
| nutrition_info      | data_creation_method_code | text                     | YES         | null                                            | 0              |
| nutrition_info      | data_creation_method_name | text                     | YES         | null                                            | 0              |
| nutrition_info      | data_creation_date        | date                     | YES         | null                                            | 0              |
| nutrition_info      | data_standard_date        | date                     | YES         | null                                            | 0              |
| nutrition_info      | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| nutrition_info      | updated_at                | timestamp with time zone | YES         | now()                                           | 0              |
| prescription_master | id                        | bigint                   | NO          | nextval('prescription_master_id_seq'::regclass) | 1              |
| prescription_master | prescription              | text                     | NO          | null                                            | 1              |
| prescription_master | prescription_read         | text                     | YES         | null                                            | 0              |
| prescription_master | prescription_modern       | text                     | YES         | null                                            | 0              |
| prescription_master | prescription_alias        | text                     | YES         | null                                            | 0              |
| prescription_master | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| products            | id                        | bigint                   | NO          | nextval('products_id_seq'::regclass)            | 1              |
| products            | source                    | text                     | NO          | 'iherb'::text                                   | 1              |
| products            | source_product_id         | text                     | NO          | null                                            | 1              |
| products            | url                       | text                     | YES         | null                                            | 0              |
| products            | title                     | text                     | YES         | null                                            | 0              |
| products            | brand                     | text                     | YES         | null                                            | 0              |
| products            | category                  | text                     | YES         | null                                            | 0              |
| products            | price                     | numeric                  | YES         | null                                            | 0              |
| products            | currency                  | text                     | YES         | 'USD'::text                                     | 0              |
| products            | rating_avg                | numeric                  | YES         | null                                            | 0              |
| products            | rating_count              | integer                  | YES         | null                                            | 0              |
| products            | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| products            | updated_at                | timestamp with time zone | YES         | now()                                           | 0              |
| reviews             | id                        | bigint                   | NO          | nextval('reviews_id_seq'::regclass)             | 1              |
| reviews             | product_id                | bigint                   | NO          | null                                            | 1              |
| reviews             | source                    | text                     | NO          | 'iherb'::text                                   | 1              |
| reviews             | source_review_id          | text                     | YES         | null                                            | 1              |
| reviews             | author                    | text                     | YES         | null                                            | 0              |
| reviews             | rating                    | integer                  | YES         | null                                            | 0              |
| reviews             | title                     | text                     | YES         | null                                            | 0              |
| reviews             | body                      | text                     | YES         | null                                            | 0              |
| reviews             | language                  | text                     | YES         | 'ko'::text                                      | 0              |
| reviews             | review_date               | date                     | YES         | null                                            | 0              |
| reviews             | helpful_count             | integer                  | YES         | null                                            | 0              |
| reviews             | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| search_logs         | id                        | bigint                   | NO          | nextval('search_logs_id_seq'::regclass)         | 1              |
| search_logs         | session_id                | character varying        | YES         | null                                            | 0              |
| search_logs         | user_id                   | uuid                     | YES         | null                                            | 1              |
| search_logs         | query                     | text                     | NO          | null                                            | 0              |
| search_logs         | query_type                | character varying        | YES         | 'keyword'::character varying                    | 0              |
| search_logs         | matched_codes             | ARRAY                    | YES         | null                                            | 0              |
| search_logs         | result_count              | integer                  | YES         | 0                                               | 0              |
| search_logs         | response_time_ms          | integer                  | YES         | null                                            | 0              |
| search_logs         | cache_hit                 | boolean                  | YES         | false                                           | 0              |
| search_logs         | model_used                | character varying        | YES         | null                                            | 0              |
| search_logs         | client_ip                 | inet                     | YES         | null                                            | 0              |
| search_logs         | user_agent                | text                     | YES         | null                                            | 0              |
| search_logs         | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| test_table          | id                        | bigint                   | NO          | nextval('test_table_id_seq'::regclass)          | 1              |
| test_table          | name                      | text                     | YES         | null                                            | 0              |
| test_table          | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| traditional_foods   | id                        | bigint                   | NO          | nextval('traditional_foods_id_seq'::regclass)   | 1              |
| traditional_foods   | rep_code                  | text                     | YES         | null                                            | 0              |
| traditional_foods   | rep_name                  | text                     | YES         | null                                            | 0              |
| traditional_foods   | trad_code                 | text                     | YES         | null                                            | 0              |
| traditional_foods   | trad_name                 | text                     | YES         | null                                            | 0              |
| traditional_foods   | disease                   | text                     | YES         | null                                            | 0              |
| traditional_foods   | disease_read              | text                     | YES         | null                                            | 0              |
| traditional_foods   | disease_alias             | text                     | YES         | null                                            | 0              |
| traditional_foods   | disease_alias_read        | text                     | YES         | null                                            | 0              |
| traditional_foods   | modern_disease            | text                     | YES         | null                                            | 0              |
| traditional_foods   | disease_src               | text                     | YES         | null                                            | 0              |
| traditional_foods   | disease_src_read          | text                     | YES         | null                                            | 0              |
| traditional_foods   | disease_src_year          | text                     | YES         | null                                            | 0              |
| traditional_foods   | disease_src_section       | text                     | YES         | null                                            | 0              |
| traditional_foods   | disease_content           | text                     | YES         | null                                            | 0              |
| traditional_foods   | prescription              | text                     | YES         | null                                            | 0              |
| traditional_foods   | prescription_read         | text                     | YES         | null                                            | 0              |
| traditional_foods   | prescription_modern       | text                     | YES         | null                                            | 0              |
| traditional_foods   | prescription_alias        | text                     | YES         | null                                            | 0              |
| traditional_foods   | presc_src                 | text                     | YES         | null                                            | 0              |
| traditional_foods   | presc_src_read            | text                     | YES         | null                                            | 0              |
| traditional_foods   | presc_src_year            | text                     | YES         | null                                            | 0              |
| traditional_foods   | presc_src_section         | text                     | YES         | null                                            | 0              |
| traditional_foods   | indication                | text                     | YES         | null                                            | 0              |
| traditional_foods   | etc                       | text                     | YES         | null                                            | 0              |
| traditional_foods   | food_type                 | text                     | YES         | null                                            | 0              |
| traditional_foods   | ingredients               | text                     | YES         | null                                            | 0              |
| traditional_foods   | preparation               | text                     | YES         | null                                            | 0              |
| traditional_foods   | dosage                    | text                     | YES         | null                                            | 0              |
| traditional_foods   | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| user_bookmarks      | id                        | bigint                   | NO          | nextval('user_bookmarks_id_seq'::regclass)      | 1              |
| user_bookmarks      | user_id                   | uuid                     | NO          | null                                            | 1              |
| user_bookmarks      | target_type               | text                     | NO          | null                                            | 0              |
| user_bookmarks      | target_id                 | bigint                   | YES         | null                                            | 0              |
| user_bookmarks      | target_text               | text                     | YES         | null                                            | 0              |
| user_bookmarks      | note                      | text                     | YES         | null                                            | 0              |
| user_bookmarks      | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| user_daily_stats    | user_id                   | uuid                     | NO          | null                                            | 2              |
| user_daily_stats    | ymd                       | date                     | NO          | null                                            | 1              |
| user_daily_stats    | searches                  | integer                  | YES         | 0                                               | 0              |
| user_daily_stats    | ai_searches               | integer                  | YES         | 0                                               | 0              |
| user_daily_stats    | cache_hits                | integer                  | YES         | 0                                               | 0              |
| user_daily_stats    | bookmarks_added           | integer                  | YES         | 0                                               | 0              |
| user_daily_stats    | last_active_at            | timestamp with time zone | YES         | null                                            | 0              |
| user_preferences    | id                        | bigint                   | NO          | nextval('user_preferences_id_seq'::regclass)    | 1              |
| user_preferences    | user_id                   | uuid                     | YES         | null                                            | 2              |
| user_preferences    | preferred_categories      | ARRAY                    | YES         | null                                            | 0              |
| user_preferences    | excluded_ingredients      | ARRAY                    | YES         | null                                            | 0              |
| user_preferences    | health_conditions         | jsonb                    | YES         | null                                            | 0              |
| user_preferences    | notification_enabled      | boolean                  | YES         | true                                            | 0              |
| user_preferences    | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| user_preferences    | updated_at                | timestamp with time zone | YES         | now()                                           | 0              |
| user_profiles       | user_id                   | uuid                     | NO          | null                                            | 2              |
| user_profiles       | display_name              | text                     | YES         | null                                            | 0              |
| user_profiles       | locale                    | text                     | YES         | 'ko-KR'::text                                   | 0              |
| user_profiles       | timezone                  | text                     | YES         | 'Asia/Seoul'::text                              | 0              |
| user_profiles       | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| user_profiles       | updated_at                | timestamp with time zone | YES         | now()                                           | 0              |
| user_quota_monthly  | user_id                   | uuid                     | NO          | null                                            | 2              |
| user_quota_monthly  | month_yyyymm              | character                | NO          | null                                            | 1              |
| user_quota_monthly  | ai_requests_limit         | integer                  | YES         | 200                                             | 0              |
| user_quota_monthly  | ai_requests_used          | integer                  | YES         | 0                                               | 0              |
| user_quota_monthly  | ext_api_limit             | integer                  | YES         | 500                                             | 0              |
| user_quota_monthly  | ext_api_used              | integer                  | YES         | 0                                               | 0              |
| user_quota_monthly  | updated_at                | timestamp with time zone | YES         | now()                                           | 0              |
| user_request_dedupe | id                        | bigint                   | NO          | nextval('user_request_dedupe_id_seq'::regclass) | 1              |
| user_request_dedupe | user_id                   | uuid                     | NO          | null                                            | 2              |
| user_request_dedupe | request_type              | text                     | NO          | null                                            | 1              |
| user_request_dedupe | request_hash              | character varying        | NO          | null                                            | 1              |
| user_request_dedupe | result                    | jsonb                    | NO          | null                                            | 0              |
| user_request_dedupe | expires_at                | timestamp with time zone | NO          | null                                            | 0              |
| user_request_dedupe | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| youtube_cache       | id                        | bigint                   | NO          | nextval('youtube_cache_id_seq'::regclass)       | 1              |
| youtube_cache       | query_hash                | character varying        | NO          | null                                            | 1              |
| youtube_cache       | query                     | text                     | NO          | null                                            | 0              |
| youtube_cache       | rep_code                  | character varying        | YES         | null                                            | 0              |
| youtube_cache       | results                   | jsonb                    | NO          | null                                            | 0              |
| youtube_cache       | result_count              | integer                  | YES         | 0                                               | 0              |
| youtube_cache       | api_quota_used            | integer                  | YES         | 0                                               | 0              |
| youtube_cache       | expires_at                | timestamp with time zone | NO          | null                                            | 0              |
| youtube_cache       | created_at                | timestamp with time zone | YES         | now()                                           | 0              |
| youtube_cache       | updated_at                | timestamp with time zone | YES         | now()                                           | 0              |