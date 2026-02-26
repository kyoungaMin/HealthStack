-- 가족 처방전 공유 기능: family_groups + family_members 테이블

-- 1) 가족 그룹
CREATE TABLE IF NOT EXISTS public.family_groups (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL DEFAULT '우리 가족',
  invite_code TEXT UNIQUE NOT NULL,
  created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_family_groups_invite_code
  ON public.family_groups(invite_code);

-- 2) 가족 멤버
CREATE TABLE IF NOT EXISTS public.family_members (
  id BIGSERIAL PRIMARY KEY,
  group_id UUID NOT NULL REFERENCES public.family_groups(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  nickname TEXT,
  role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'member')),
  joined_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(group_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_family_members_user_id
  ON public.family_members(user_id);

CREATE INDEX IF NOT EXISTS idx_family_members_group_id
  ON public.family_members(group_id);

-- RLS 활성화
ALTER TABLE public.family_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.family_members ENABLE ROW LEVEL SECURITY;

-- family_groups RLS: 멤버인 사용자만 조회/수정 가능
CREATE POLICY "family_groups_select_member"
  ON public.family_groups FOR SELECT
  TO authenticated
  USING (
    id IN (SELECT group_id FROM public.family_members WHERE user_id = auth.uid())
  );

CREATE POLICY "family_groups_insert_auth"
  ON public.family_groups FOR INSERT
  TO authenticated
  WITH CHECK (created_by = auth.uid());

CREATE POLICY "family_groups_update_owner"
  ON public.family_groups FOR UPDATE
  TO authenticated
  USING (created_by = auth.uid());

CREATE POLICY "family_groups_delete_owner"
  ON public.family_groups FOR DELETE
  TO authenticated
  USING (created_by = auth.uid());

-- family_members RLS: 같은 그룹 멤버만 조회 가능
CREATE POLICY "family_members_select_same_group"
  ON public.family_members FOR SELECT
  TO authenticated
  USING (
    group_id IN (SELECT group_id FROM public.family_members WHERE user_id = auth.uid())
  );

CREATE POLICY "family_members_insert_self"
  ON public.family_members FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "family_members_update_self"
  ON public.family_members FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "family_members_delete_self"
  ON public.family_members FOR DELETE
  TO authenticated
  USING (user_id = auth.uid());

-- prescription_records RLS: 같은 가족 그룹 멤버가 읽기 가능
-- (prescription_records 테이블에 이미 RLS가 있다면 정책만 추가)
DO $$
BEGIN
  -- prescription_records에 RLS가 비활성화되어 있으면 활성화
  IF NOT EXISTS (
    SELECT 1 FROM pg_tables
    WHERE tablename = 'prescription_records' AND rowsecurity = true
  ) THEN
    ALTER TABLE public.prescription_records ENABLE ROW LEVEL SECURITY;

    -- 본인 데이터 전체 접근
    CREATE POLICY "prescription_records_own"
      ON public.prescription_records FOR ALL
      TO authenticated
      USING (user_id = auth.uid())
      WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

-- 가족 멤버가 읽기 가능 (SELECT만)
CREATE POLICY "prescription_records_family_read"
  ON public.prescription_records FOR SELECT
  TO authenticated
  USING (
    user_id IN (
      SELECT fm2.user_id
      FROM public.family_members fm1
      JOIN public.family_members fm2 ON fm1.group_id = fm2.group_id
      WHERE fm1.user_id = auth.uid()
    )
  );
