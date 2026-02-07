# Health Stack ERD - Section Index

> Auto-generated from `schema.integrated.dbml`


## Core User & Master Tables

- **File**: [01_core_user.md](./01_core_user.md)

- **Tables**: `auth_users`, `user_profiles`, `user_preferences`, `foods_master`, `disease_master`, `catalog_drugs`, `catalog_supplements`


## Intake & Schedule Management

- **File**: [02_intake_schedule.md](./02_intake_schedule.md)

- **Tables**: `user_intake_items`, `intake_schedules`, `intake_logs`, `user_push_tokens`, `reports`


## Symptom & Ingredient Mapping

- **File**: [03_symptom_mapping.md](./03_symptom_mapping.md)

- **Tables**: `symptom_ingredient_map`, `recipes`, `symptom_recipe_map`, `content_videos`, `symptom_video_map`, `ingredient_product_links`


## User Input Sessions & Prescriptions

- **File**: [04_input_session.md](./04_input_session.md)

- **Tables**: `user_input_sessions`, `user_symptoms`, `user_prescriptions`, `user_prescription_drugs`, `session_recommendation_results`


## Restaurant Recommendations

- **File**: [05_restaurant.md](./05_restaurant.md)

- **Tables**: `restaurants`, `restaurant_menus`, `restaurant_search_templates`, `restaurant_search_requests`, `restaurant_search_results`, `user_restaurant_favorites`, `user_restaurant_visit_logs`


## Catalog Codes & Cache

- **File**: [06_catalog_cache.md](./06_catalog_cache.md)

- **Tables**: `catalog_major_codes`, `catalog_minor_codes`, `youtube_cache`, `commerce_cache`


## TKM (동의보감) Symptom Mapping

- **File**: [07_tkm_mapping.md](./07_tkm_mapping.md)

- **Tables**: `tkm_symptom_master`, `tkm_to_modern_map`


## PubMed & MeSH Integration

- **File**: [08_pubmed.md](./08_pubmed.md)

- **Tables**: `pubmed_papers`, `pubmed_embeddings`, `modern_to_mesh_map`, `symptom_pubmed_map`, `ingredient_pubmed_map`, `interaction_facts`


## Plans & Billing

- **File**: [09_billing.md](./09_billing.md)

- **Tables**: `plans`, `subscriptions`, `payments`

