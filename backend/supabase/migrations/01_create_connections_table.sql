-- Create table for storing user connection credentials securely
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE public.data_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL, -- Ties back to auth.users if using Supabase auth
    source_type TEXT NOT NULL CHECK (source_type IN ('postgres', 'snowflake', 'kafka')),
    connection_name TEXT NOT NULL,
    host TEXT NOT NULL,
    database_name TEXT,
    encrypted_credentials TEXT NOT NULL, -- Stored as encrypted string
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add RLS policies (Optional but recommended)
ALTER TABLE public.data_connections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own connections"
    ON public.data_connections FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own connections"
    ON public.data_connections FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own connections"
    ON public.data_connections FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own connections"
    ON public.data_connections FOR DELETE
    USING (auth.uid() = user_id);
