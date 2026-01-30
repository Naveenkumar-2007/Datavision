-- Migration: Company Profiles for ChatGPT Business Analyst
-- Enables company-aware, context-aware responses

-- ============================================================================
-- COMPANY PROFILES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS company_profiles (
    -- Primary key is workspace_id (one profile per workspace)
    workspace_id TEXT PRIMARY KEY,
    
    -- Company identification
    company_name TEXT NOT NULL DEFAULT 'Your Company',
    
    -- Industry for benchmarking
    industry TEXT NOT NULL DEFAULT 'other',
    
    -- Fiscal calendar
    fiscal_year_end_month INTEGER NOT NULL DEFAULT 12,
    
    -- Currency and locale
    currency TEXT NOT NULL DEFAULT 'USD',
    currency_symbol TEXT NOT NULL DEFAULT '$',
    timezone TEXT NOT NULL DEFAULT 'UTC',
    
    -- JSON fields for flexible storage
    kpi_definitions JSONB NOT NULL DEFAULT '{
        "revenue": "Total sales revenue",
        "mrr": "Monthly Recurring Revenue",
        "arr": "Annual Recurring Revenue",
        "aov": "Average Order Value"
    }'::jsonb,
    
    terminology JSONB NOT NULL DEFAULT '{
        "customer": "customer",
        "revenue": "revenue",
        "product": "product",
        "order": "order"
    }'::jsonb,
    
    benchmarks JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    branding JSONB NOT NULL DEFAULT '{
        "primary_color": "#3B82F6",
        "secondary_color": "#1E40AF",
        "font_family": "Inter"
    }'::jsonb,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_company_profiles_workspace 
ON company_profiles(workspace_id);

-- Index for industry-based analytics
CREATE INDEX IF NOT EXISTS idx_company_profiles_industry 
ON company_profiles(industry);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

-- Enable RLS
ALTER TABLE company_profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own workspace profiles
CREATE POLICY "Users can view own workspace profile"
ON company_profiles FOR SELECT
USING (auth.uid()::text = workspace_id OR workspace_id LIKE auth.uid()::text || '%');

CREATE POLICY "Users can insert own workspace profile"
ON company_profiles FOR INSERT
WITH CHECK (auth.uid()::text = workspace_id OR workspace_id LIKE auth.uid()::text || '%');

CREATE POLICY "Users can update own workspace profile"
ON company_profiles FOR UPDATE
USING (auth.uid()::text = workspace_id OR workspace_id LIKE auth.uid()::text || '%');

CREATE POLICY "Users can delete own workspace profile"
ON company_profiles FOR DELETE
USING (auth.uid()::text = workspace_id OR workspace_id LIKE auth.uid()::text || '%');

-- Service role bypass for admin operations
CREATE POLICY "Service role has full access"
ON company_profiles FOR ALL
USING (auth.role() = 'service_role');

-- ============================================================================
-- UPDATED_AT TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION update_company_profile_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER company_profiles_updated_at
    BEFORE UPDATE ON company_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_company_profile_timestamp();

-- ============================================================================
-- SAMPLE DATA (for development)
-- ============================================================================

-- Insert a sample profile for testing
INSERT INTO company_profiles (
    workspace_id,
    company_name,
    industry,
    fiscal_year_end_month,
    currency,
    currency_symbol,
    timezone,
    terminology,
    benchmarks
) VALUES (
    'demo_workspace',
    'Demo Analytics Inc',
    'saas',
    12,
    'USD',
    '$',
    'America/New_York',
    '{"customer": "client", "revenue": "ARR", "product": "subscription", "order": "deal"}'::jsonb,
    '{"growth_target": 0.25, "churn_target": 0.03}'::jsonb
) ON CONFLICT (workspace_id) DO NOTHING;
