# ==============================================================================
# AI AGENT NOTIFICATION SYSTEM - DEPLOYMENT GUIDE
# ==============================================================================

## Overview
Complete system for AI agents to autonomously detect insights and notify users via email and push notifications with proper rate limiting, retries, and security.

---

## Prerequisites

### 1. Environment Variables

Add to `.env` (backend):
```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Email (Resend)
RESEND_API_KEY=your_resend_api_key
FROM_EMAIL=insights@your-domain.com

# Push Notifications (VAPID)
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_PRIVATE_KEY=your_vapid_private_key

# App URL
APP_URL=https://your-app.com
```

Add to `.env` (frontend):
```env
VITE_VAPID_PUBLIC_KEY=your_vapid_public_key
```

### 2. Generate VAPID Keys

```bash
cd backend
python -c "from services.push_service import generate_vapid_keys; generate_vapid_keys()"
```

This will output:
```
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...
```

Add these to your `.env` files.

---

## Phase 1: Database Setup

### 1. Run Migration

In Supabase SQL Editor, run:
```sql
-- Execute the migration file
\i supabase/migrations/004_notification_system.sql
```

Or copy-paste the contents of `004_notification_system.sql` into the SQL Editor.

### 2. Verify Tables

Run verification queries:
```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('notification_settings', 'push_tokens', 'ai_insights', 'agent_logs', 'notifications_history');

-- Check RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('notification_settings', 'push_tokens', 'ai_insights', 'agent_logs', 'notifications_history');
```

### 3. Test RLS Policies

```sql
-- As authenticated user, try to select from notification_settings
-- Should only return your own settings
SELECT * FROM notification_settings;
```

---

## Phase 2: Backend Deployment

### 1. Install Dependencies

```bash
cd backend
pip install supabase pywebpush httpx
```

### 2. Register API Routes

In `backend/main.py`:
```python
from api.v1.endpoints.notifications import router as notification_router

app.include_router(notification_router)
```

### 3. Test API Endpoints

```bash
# Start backend
uvicorn main:app --reload

# Test endpoint (with valid JWT token)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/settings/WORKSPACE_ID/USER_ID
```

---

## Phase 3: Agent Deployment

### Option A: Supabase Edge Functions

1. Create edge functions:
```bash
supabase functions new agent-monitoring
supabase functions new agent-forecast
supabase functions new agent-report
supabase functions new agent-memory
```

2. Deploy:
```bash
supabase functions deploy agent-monitoring --no-verify-jwt
supabase functions deploy agent-forecast --no-verify-jwt
supabase functions deploy agent-report --no-verify-jwt
supabase functions deploy agent-memory --no-verify-jwt
```

3. Set up cron triggers in Supabase dashboard:
- `agent-monitoring`: Every 6 hours
- `agent-forecast`: Daily at 2 AM
- `agent-report`: Weekly on Monday 8 AM
- `agent-memory`: Daily at 3 AM

### Option B: Cron Job (Server)

1. Add to crontab:
```bash
# MonitoringAgent - every 6 hours
0 */6 * * * cd /path/to/backend && python scheduler/agent_scheduler.py monitoring

# ForecastAgent - daily at 2 AM
0 2 * * * cd /path/to/backend && python scheduler/agent_scheduler.py forecast

# ReportAgent - weekly on Monday at 8 AM
0 8 * * 1 cd /path/to/backend && python scheduler/agent_scheduler.py report

# MemoryAgent - daily at 3 AM
0 3 * * * cd /path/to/backend && python scheduler/agent_scheduler.py memory
```

### Option C: AWS Lambda (Serverless)

1. Package dependencies:
```bash
pip install -t package/ supabase pywebpush httpx
cd package && zip -r ../lambda.zip . && cd ..
zip -g lambda.zip backend/agents/* backend/services/* backend/utils/*
```

2. Upload to AWS Lambda

3. Set up CloudWatch Events triggers with cron expressions

---

## Phase 4: Frontend Deployment

### 1. Add Route

In `frontend/src/App.tsx` or router configuration:
```typescript
import NotificationSettings from './pages/NotificationSettings';

<Route path="/settings/notifications" element={<NotificationSettings />} />
```

### 2. Add Navigation Link

In your settings menu/sidebar:
```typescript
<Link to="/settings/notifications">
  <Bell className="h-5 w-5" />
  Notifications
</Link>
```

### 3. Build and Deploy

```bash
cd frontend
npm run build
# Deploy build/ folder to your hosting (Vercel, Netlify, etc.)
```

---

## Phase 5: Testing

### 1. Test Manual Agent Trigger

```bash
curl -X POST http://localhost:8000/api/agents/run/MonitoringAgent \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "YOUR_WORKSPACE_ID"}'
```

### 2. Verify Insight Creation

```sql
SELECT * FROM ai_insights WHERE workspace_id = 'YOUR_WORKSPACE_ID' ORDER BY created_at DESC LIMIT 5;
```

### 3. Check Notification Logs

```sql
SELECT * FROM notifications_history WHERE workspace_id = 'YOUR_WORKSPACE_ID' ORDER BY sent_at DESC LIMIT 10;
```

### 4. Test Push Notifications

1. Open app in browser
2. Go to Settings → Notifications
3. Enable "Push Notifications"
4. Allow browser permission
5. Manually trigger agent via API
6. You should receive a browser notification

---

## Monitoring & Maintenance

### 1. View Agent Logs

```sql
SELECT * FROM agent_logs 
WHERE workspace_id = 'YOUR_WORKSPACE_ID' 
ORDER BY executed_at DESC 
LIMIT 50;
```

### 2. Monitor Notification Success Rate

```sql
SELECT 
  channel,
  COUNT(*) as total,
  SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
  ROUND(100.0 * SUM(CASE WHEN success THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM notifications_history
WHERE sent_at >= NOW() - INTERVAL '7 days'
GROUP BY channel;
```

### 3. Check Rate Limits

```sql
SELECT user_id, COUNT(*) as notifications_last_hour
FROM notifications_history
WHERE sent_at >= NOW() - INTERVAL '1 hour'
GROUP BY user_id
HAVING COUNT(*) >= 5
ORDER BY COUNT(*) DESC;
```

---

## Troubleshooting

### Push Notifications Not Working

1. Check VAPID keys are correct
2. Verify service worker is registered: `navigator.serviceWorker.getRegistrations()`
3. Check browser console for errors
4. Ensure HTTPS (push requires secure context)

### Emails Not Sending

1. Verify RESEND_API_KEY is set
2. Check `notifications_history` for error messages
3. Test Resend API directly:
```bash
curl -X POST https://api.resend.com/emails \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"from":"test@yourdomain.com","to":"you@email.com","subject":"Test","html":"Test"}'
```

### Agents Not Running

1. Check cron/scheduler logs
2. Verify agent_logs table for errors
3. Test manual trigger endpoint
4. Check service role key permissions

---

## Security Checklist

- ✅ RLS enabled on all tables
- ✅ Service role key never exposed to client
- ✅ JWT validation on all API endpoints
- ✅ Workspace membership verification
- ✅ Rate limiting implemented
- ✅ Push token validation
- ✅ HTTPS enforced

---

## Performance Optimization

### 1. Add Indexes (if needed)

```sql
CREATE INDEX idx_insights_workspace_created ON ai_insights(workspace_id, created_at DESC);
CREATE INDEX idx_notifications_user_sent ON notifications_history(user_id, sent_at DESC);
```

### 2. Batch Notifications

Instead of sending one-by-one, batch notifications per user.

### 3. Rate Limit by Workspace

Implement per-workspace quotas to prevent spam.

---

## Next Steps

1. **Analytics Dashboard**: View insight trends, notification delivery rates
2. **A/B Testing**: Test different notification timings and content
3. **Notification Templates**: Allow customization of email templates
4. **Slack Integration**: Add Slack as another notification channel
5. **Mobile Apps**: Native Android/iOS push notifications

---

## Support

For issues or questions:
1. Check agent_logs table for errors
2. Review notifications_history for delivery failures
3. Test endpoints manually with Postman/curl
4. Enable debug logging: `logging.basicConfig(level=logging.DEBUG)`
