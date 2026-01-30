-- ============================================================================
-- AI Business Analyst - Supabase Database Schema
-- Complete schema with Row Level Security (RLS)
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. PROFILES TABLE (extends Supabase auth.users)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    company_name TEXT,
    role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin', 'super_admin')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Policies for profiles
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Admins can view all profiles" ON public.profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = auth.uid() AND role IN ('admin', 'super_admin')
        )
    );

-- Trigger to create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', ''),
        COALESCE(NEW.raw_user_meta_data->>'avatar_url', NEW.raw_user_meta_data->>'picture', '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================================
-- 2. ADMIN USERS TABLE (separate admin management)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.admin_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    admin_role TEXT NOT NULL DEFAULT 'moderator' CHECK (admin_role IN ('moderator', 'admin', 'super_admin')),
    permissions JSONB DEFAULT '{"can_view_users": true, "can_edit_users": false, "can_delete_users": false, "can_view_analytics": true}'::jsonb,
    granted_by UUID REFERENCES public.profiles(id),
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    UNIQUE(user_id)
);

-- Enable RLS
ALTER TABLE public.admin_users ENABLE ROW LEVEL SECURITY;

-- Only super_admins can manage admin_users
CREATE POLICY "Super admins can manage admin users" ON public.admin_users
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = auth.uid() AND role = 'super_admin'
        )
    );

CREATE POLICY "Admins can view admin users" ON public.admin_users
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = auth.uid() AND role IN ('admin', 'super_admin')
        )
    );

-- ============================================================================
-- 3. CONVERSATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT,
    mode TEXT DEFAULT 'auto',
    is_archived BOOLEAN DEFAULT false,
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON public.conversations(created_at DESC);

-- Enable RLS
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

-- Users can only access their own conversations
CREATE POLICY "Users can manage own conversations" ON public.conversations
    FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- 4. MESSAGES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    mode TEXT,
    sources JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON public.messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON public.messages(created_at);

-- Enable RLS
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Users can only access their own messages
CREATE POLICY "Users can manage own messages" ON public.messages
    FOR ALL USING (auth.uid() = user_id);

-- Trigger to update conversation message count and last_message_at
CREATE OR REPLACE FUNCTION public.update_conversation_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.conversations
    SET 
        message_count = message_count + 1,
        last_message_at = NEW.created_at,
        updated_at = NOW()
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_message_created
    AFTER INSERT ON public.messages
    FOR EACH ROW EXECUTE FUNCTION public.update_conversation_stats();

-- ============================================================================
-- 5. USER FILES TABLE (metadata only, files in Storage)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.user_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type TEXT,
    storage_path TEXT NOT NULL,  -- Path in Supabase Storage
    bucket_name TEXT DEFAULT 'user-files',
    is_processed BOOLEAN DEFAULT false,
    is_indexed BOOLEAN DEFAULT false,
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    processing_error TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_files_user_id ON public.user_files(user_id);
CREATE INDEX IF NOT EXISTS idx_user_files_filename ON public.user_files(filename);
CREATE INDEX IF NOT EXISTS idx_user_files_uploaded_at ON public.user_files(uploaded_at DESC);

-- Enable RLS
ALTER TABLE public.user_files ENABLE ROW LEVEL SECURITY;

-- Users can only access their own files
CREATE POLICY "Users can manage own files" ON public.user_files
    FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- 6. USER QUERIES TABLE (for analytics)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.user_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    query_type TEXT,  -- 'rag', 'graph', 'hybrid', 'vision'
    response_time_ms INTEGER,
    tokens_used INTEGER,
    cache_hit BOOLEAN DEFAULT false,
    sources_used JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_queries_user_id ON public.user_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_user_queries_created_at ON public.user_queries(created_at DESC);

-- Enable RLS
ALTER TABLE public.user_queries ENABLE ROW LEVEL SECURITY;

-- Users can view their own queries, admins can view all
CREATE POLICY "Users can view own queries" ON public.user_queries
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert queries" ON public.user_queries
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Admins can view all queries" ON public.user_queries
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = auth.uid() AND role IN ('admin', 'super_admin')
        )
    );

-- ============================================================================
-- 7. USER MEMORY TABLE (mid-term and long-term memory)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.user_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    memory_layer TEXT NOT NULL CHECK (memory_layer IN ('mid_term', 'long_term')),
    memory_type TEXT NOT NULL,  -- 'insight', 'prediction', 'entity', 'relationship', 'kpi', 'pattern'
    content JSONB NOT NULL,
    embedding vector(384),  -- For semantic search with pgvector
    metadata JSONB DEFAULT '{}'::jsonb,
    confidence FLOAT,
    expires_at TIMESTAMPTZ,  -- For mid-term memories
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_memory_user_id ON public.user_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_user_memory_layer ON public.user_memory(memory_layer);
CREATE INDEX IF NOT EXISTS idx_user_memory_type ON public.user_memory(memory_type);
CREATE INDEX IF NOT EXISTS idx_user_memory_expires_at ON public.user_memory(expires_at);

-- Enable RLS
ALTER TABLE public.user_memory ENABLE ROW LEVEL SECURITY;

-- Users can only access their own memories
CREATE POLICY "Users can manage own memories" ON public.user_memory
    FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- 8. USER PREFERENCES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    theme TEXT DEFAULT 'dark' CHECK (theme IN ('light', 'dark', 'system')),
    currency_code TEXT DEFAULT 'INR',
    currency_symbol TEXT DEFAULT '₹',
    language TEXT DEFAULT 'en',
    notifications_enabled BOOLEAN DEFAULT true,
    email_notifications BOOLEAN DEFAULT true,
    auto_save_conversations BOOLEAN DEFAULT true,
    default_chat_mode TEXT DEFAULT 'auto',
    custom_settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;

-- Users can only access their own preferences
CREATE POLICY "Users can manage own preferences" ON public.user_preferences
    FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get user's total storage used
CREATE OR REPLACE FUNCTION public.get_user_storage_used(p_user_id UUID)
RETURNS BIGINT AS $$
    SELECT COALESCE(SUM(file_size), 0)
    FROM public.user_files
    WHERE user_id = p_user_id;
$$ LANGUAGE sql SECURITY DEFINER;

-- Function to check if user is admin
CREATE OR REPLACE FUNCTION public.is_admin(p_user_id UUID)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.profiles 
        WHERE id = p_user_id AND role IN ('admin', 'super_admin')
    );
$$ LANGUAGE sql SECURITY DEFINER;

-- Function to update timestamps
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update_updated_at trigger to relevant tables
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON public.conversations
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE TRIGGER update_user_memory_updated_at
    BEFORE UPDATE ON public.user_memory
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON public.user_preferences
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- ============================================================================
-- STORAGE BUCKET SETUP (run in Supabase Dashboard or via API)
-- ============================================================================
-- Note: Storage buckets are created via Supabase Dashboard or Storage API
-- Bucket name: user-files
-- Public: false
-- File size limit: 100MB
-- Allowed MIME types: application/pdf, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,
--                     application/vnd.ms-excel, text/csv, application/json, text/plain,
--                     image/png, image/jpeg, image/jpg,
--                     application/vnd.openxmlformats-officedocument.wordprocessingml.document,
--                     application/vnd.openxmlformats-officedocument.presentationml.presentation

-- Storage RLS policies (set in Supabase Dashboard):
-- SELECT: (bucket_id = 'user-files') AND (auth.uid()::text = (storage.foldername(name))[1])
-- INSERT: (bucket_id = 'user-files') AND (auth.uid()::text = (storage.foldername(name))[1])
-- UPDATE: (bucket_id = 'user-files') AND (auth.uid()::text = (storage.foldername(name))[1])
-- DELETE: (bucket_id = 'user-files') AND (auth.uid()::text = (storage.foldername(name))[1])
