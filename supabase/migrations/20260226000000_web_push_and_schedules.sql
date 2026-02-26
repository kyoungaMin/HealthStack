-- Web Push 지원을 위한 user_push_tokens 컬럼 추가 + 복약 스케줄 테이블 생성

-- 1) user_push_tokens에 Web Push 필드 추가
ALTER TABLE public.user_push_tokens
  ADD COLUMN IF NOT EXISTS endpoint TEXT,
  ADD COLUMN IF NOT EXISTS p256dh TEXT,
  ADD COLUMN IF NOT EXISTS auth_key TEXT;

-- Web Push endpoint 기반 고유 인덱스
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_push_tokens_web_endpoint
  ON public.user_push_tokens(user_id, endpoint)
  WHERE platform = 'web' AND endpoint IS NOT NULL;

-- 2) 복약 스케줄 테이블 (백엔드 스케줄러가 조회하여 Push 발송)
CREATE TABLE IF NOT EXISTS public.user_medication_schedules (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  schedule_key TEXT NOT NULL,
  drug_name TEXT NOT NULL,
  times TEXT[] NOT NULL DEFAULT '{}',
  days_of_week INT[] NOT NULL DEFAULT '{}',
  enabled BOOLEAN DEFAULT TRUE,
  timezone TEXT DEFAULT 'Asia/Seoul',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, schedule_key)
);

CREATE INDEX IF NOT EXISTS idx_user_med_schedules_user
  ON public.user_medication_schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_user_med_schedules_enabled
  ON public.user_medication_schedules(enabled) WHERE enabled = TRUE;

-- RLS
ALTER TABLE public.user_medication_schedules ENABLE ROW LEVEL SECURITY;

CREATE POLICY "med_schedules_select_own"
  ON public.user_medication_schedules FOR SELECT
  TO authenticated USING (user_id = auth.uid());

CREATE POLICY "med_schedules_insert_own"
  ON public.user_medication_schedules FOR INSERT
  TO authenticated WITH CHECK (user_id = auth.uid());

CREATE POLICY "med_schedules_update_own"
  ON public.user_medication_schedules FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "med_schedules_delete_own"
  ON public.user_medication_schedules FOR DELETE
  TO authenticated USING (user_id = auth.uid());
