-- ============================================================================
-- AI Agent Notification System - Database Schema
-- Run this in Supabase SQL Editor
-- ============================================================================

-- Enable UUID extension if not already enabled
create extension if not exists "uuid-ossp";

-- ============================================================================
-- 1. NOTIFICATION SETTINGS TABLE
-- ============================================================================
create table if not exists notification_settings (
  workspace_id uuid not null,
  user_id uuid not null,
  email_notifications boolean default true,
  push_notifications boolean default false,
  weekly_reports boolean default true,
  ai_insights boolean default true,
  severity_threshold text default 'medium' check (severity_threshold in ('low', 'medium', 'high')),
  dnd_start time null,
  dnd_end time null,
  updated_at timestamptz default now(),
  primary key(workspace_id, user_id)
);

-- Indexes for performance
create index if not exists idx_notification_settings_workspace on notification_settings(workspace_id);
create index if not exists idx_notification_settings_user on notification_settings(user_id);

-- Enable RLS
alter table notification_settings enable row level security;

-- RLS Policies
drop policy if exists "Users can view their own settings" on notification_settings;
create policy "Users can view their own settings"
  on notification_settings for select
  using (auth.uid() = user_id);

drop policy if exists "Users can update their own settings" on notification_settings;
create policy "Users can update their own settings"
  on notification_settings for update
  using (auth.uid() = user_id);

drop policy if exists "Users can insert their own settings" on notification_settings;
create policy "Users can insert their own settings"
  on notification_settings for insert
  with check (auth.uid() = user_id);

-- ============================================================================
-- 2. PUSH TOKENS TABLE
-- ============================================================================
create table if not exists push_tokens (
  id uuid primary key default uuid_generate_v4(),
  workspace_id uuid not null,
  user_id uuid not null,
  token text not null,
  platform text,
  created_at timestamptz default now(),
  constraint push_tokens_token_unique unique(token)
);

-- Indexes
create index if not exists idx_push_tokens_user_workspace on push_tokens(user_id, workspace_id);
create index if not exists idx_push_tokens_workspace on push_tokens(workspace_id);

-- Enable RLS
alter table push_tokens enable row level security;

-- RLS Policies
drop policy if exists "Users can manage their own tokens" on push_tokens;
create policy "Users can manage their own tokens"
  on push_tokens for all
  using (auth.uid() = user_id);

-- ============================================================================
-- 3. AI INSIGHTS TABLE
-- ============================================================================
create table if not exists ai_insights (
  id uuid primary key default uuid_generate_v4(),
  workspace_id uuid not null,
  title text not null,
  body text not null,
  severity text not null check (severity in ('low', 'medium', 'high')),
  score numeric null,
  metadata jsonb default '{}'::jsonb,
  chart_payload jsonb null,
  created_by_agent text not null,
  created_at timestamptz default now()
);

-- Indexes
create index if not exists idx_ai_insights_workspace on ai_insights(workspace_id);
create index if not exists idx_ai_insights_created_at on ai_insights(created_at desc);
create index if not exists idx_ai_insights_severity on ai_insights(severity);
create index if not exists idx_ai_insights_agent on ai_insights(created_by_agent);

-- Enable RLS
alter table ai_insights enable row level security;

-- RLS Policies
-- Simplified: Allow authenticated users to view all insights
-- TODO: Add workspace_members table check when available
drop policy if exists "Users can view all insights" on ai_insights;
create policy "Users can view all insights"
  on ai_insights for select
  using (auth.role() = 'authenticated');

-- ============================================================================
-- 4. AGENT LOGS TABLE
-- ============================================================================
create table if not exists agent_logs (
  id uuid primary key default uuid_generate_v4(),
  agent_name text not null,
  workspace_id uuid,
  status text not null,
  message text,
  metadata jsonb default '{}'::jsonb,
  executed_at timestamptz default now()
);

-- Indexes
create index if not exists idx_agent_logs_workspace on agent_logs(workspace_id);
create index if not exists idx_agent_logs_executed_at on agent_logs(executed_at desc);
create index if not exists idx_agent_logs_agent_name on agent_logs(agent_name);
create index if not exists idx_agent_logs_status on agent_logs(status);

-- Enable RLS
alter table agent_logs enable row level security;

-- RLS Policies
-- Simplified: Allow authenticated users to view logs
-- TODO: Restrict to admins only when workspace_members table is available
drop policy if exists "Authenticated users can view logs" on agent_logs;
create policy "Authenticated users can view logs"
  on agent_logs for select
  using (auth.role() = 'authenticated');

-- ============================================================================
-- 5. NOTIFICATIONS HISTORY TABLE
-- ============================================================================
create table if not exists notifications_history (
  id uuid primary key default uuid_generate_v4(),
  insight_id uuid references ai_insights(id) on delete cascade,
  workspace_id uuid not null,
  user_id uuid not null,
  channel text not null check (channel in ('email', 'push')),
  payload jsonb not null,
  success boolean default false,
  attempt int default 1,
  error_message text,
  sent_at timestamptz default now()
);

-- Indexes
create index if not exists idx_notifications_history_workspace on notifications_history(workspace_id);
create index if not exists idx_notifications_history_user on notifications_history(user_id);
create index if not exists idx_notifications_history_insight on notifications_history(insight_id);
create index if not exists idx_notifications_history_sent_at on notifications_history(sent_at desc);
create index if not exists idx_notifications_history_channel on notifications_history(channel);

-- Enable RLS
alter table notifications_history enable row level security;

-- RLS Policies (users can view their own notification history)
drop policy if exists "Users can view their notification history" on notifications_history;
create policy "Users can view their notification history"
  on notifications_history for select
  using (auth.uid() = user_id);

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================
-- Grant authenticated users access to tables
grant select, insert, update on notification_settings to authenticated;
grant select, insert, delete on push_tokens to authenticated;
grant select on ai_insights to authenticated;
grant select on agent_logs to authenticated;
grant select on notifications_history to authenticated;

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to automatically create default notification settings for new users
-- DISABLED: Requires workspace_members table
-- Uncomment when workspace_members table is available
/*
create or replace function create_default_notification_settings()
returns trigger as $$
begin
  insert into notification_settings (workspace_id, user_id)
  values (NEW.workspace_id, NEW.user_id)
  on conflict (workspace_id, user_id) do nothing;
  return NEW;
end;
$$ language plpgsql security definer;

drop trigger if exists auto_create_notification_settings on workspace_members;
create trigger auto_create_notification_settings
  after insert on workspace_members
  for each row
  execute function create_default_notification_settings();
*/

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these to verify setup:

-- Check tables exist
-- select table_name from information_schema.tables 
-- where table_schema = 'public' 
-- and table_name in ('notification_settings', 'push_tokens', 'ai_insights', 'agent_logs', 'notifications_history');

-- Check RLS is enabled
-- select tablename, rowsecurity from pg_tables 
-- where schemaname = 'public' 
-- and tablename in ('notification_settings', 'push_tokens', 'ai_insights', 'agent_logs', 'notifications_history');

-- Check indexes
-- select indexname from pg_indexes 
-- where schemaname = 'public' 
-- and tablename in ('notification_settings', 'push_tokens', 'ai_insights', 'agent_logs', 'notifications_history');
