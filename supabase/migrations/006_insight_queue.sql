-- Migration: Insight Queue for Proactive Intelligence
-- Stores detected anomalies and insights for dashboard surfacing

-- ============================================================================
-- INSIGHT QUEUE TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS insight_queue (
    -- Primary key
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    
    -- Insight content
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'anomaly',
    
    -- Priority and severity
    priority INTEGER NOT NULL DEFAULT 5,
    severity TEXT NOT NULL DEFAULT 'medium',
    
    -- Additional data
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    chart_payload JSONB,
    
    -- Status tracking
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    seen_at TIMESTAMPTZ,
    dismissed BOOLEAN NOT NULL DEFAULT false,
    actioned BOOLEAN NOT NULL DEFAULT false
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_insight_queue_workspace 
ON insight_queue(workspace_id);

CREATE INDEX IF NOT EXISTS idx_insight_queue_unseen 
ON insight_queue(workspace_id, seen_at) WHERE seen_at IS NULL AND dismissed = false;

CREATE INDEX IF NOT EXISTS idx_insight_queue_priority 
ON insight_queue(priority DESC);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE insight_queue ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own workspace insights"
ON insight_queue FOR SELECT
USING (auth.uid()::text = workspace_id OR workspace_id LIKE auth.uid()::text || '%');

CREATE POLICY "Users can update own workspace insights"
ON insight_queue FOR UPDATE
USING (auth.uid()::text = workspace_id OR workspace_id LIKE auth.uid()::text || '%');

CREATE POLICY "Service role has full access to insights"
ON insight_queue FOR ALL
USING (auth.role() = 'service_role');

-- ============================================================================
-- CLEANUP FUNCTION (for old insights)
-- ============================================================================

CREATE OR REPLACE FUNCTION cleanup_old_insights()
RETURNS void AS $$
BEGIN
    DELETE FROM insight_queue 
    WHERE created_at < now() - interval '30 days'
    AND (dismissed = true OR seen_at IS NOT NULL);
END;
$$ LANGUAGE plpgsql;
