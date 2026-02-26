-- Add health profile columns to user_profiles
ALTER TABLE public.user_profiles
  ADD COLUMN IF NOT EXISTS birth_year INTEGER,
  ADD COLUMN IF NOT EXISTS gender TEXT CHECK (gender IN ('male', 'female', 'other')),
  ADD COLUMN IF NOT EXISTS height_cm NUMERIC(5,1),
  ADD COLUMN IF NOT EXISTS weight_kg NUMERIC(5,1),
  ADD COLUMN IF NOT EXISTS drug_allergies TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS food_allergies TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS health_conditions TEXT[] DEFAULT '{}';

-- Add display settings columns to user_preferences
ALTER TABLE public.user_preferences
  ADD COLUMN IF NOT EXISTS theme_mode TEXT DEFAULT 'light' CHECK (theme_mode IN ('light', 'dark', 'system')),
  ADD COLUMN IF NOT EXISTS font_size TEXT DEFAULT 'medium' CHECK (font_size IN ('small', 'medium', 'large')),
  ADD COLUMN IF NOT EXISTS tts_speed NUMERIC(3,1) DEFAULT 0.9 CHECK (tts_speed >= 0.5 AND tts_speed <= 2.0);
