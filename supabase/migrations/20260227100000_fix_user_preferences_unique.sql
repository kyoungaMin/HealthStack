-- Fix: Add UNIQUE constraint on user_id for upsert operations
-- Without this, upsert(..., on_conflict="user_id") fails with 500 error
ALTER TABLE public.user_preferences
  ADD CONSTRAINT user_preferences_user_id_unique UNIQUE (user_id);
