-- Store user health stacks (prescription & symptom analysis results)
CREATE TABLE IF NOT EXISTS public.user_health_stacks (
    id TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('prescription', 'symptom')),
    date TEXT NOT NULL,
    stack_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, id)
);

CREATE INDEX IF NOT EXISTS idx_health_stacks_user_id ON public.user_health_stacks(user_id);

-- RLS
ALTER TABLE public.user_health_stacks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own stacks"
    ON public.user_health_stacks
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);
