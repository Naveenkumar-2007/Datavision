# 🚀 HuggingFace Spaces Deployment Guide

## Production-Ready DataVision AI

### Pre-Deployment Checklist ✅

#### 1. Environment Variables (CRITICAL)
Set these in HuggingFace Spaces Settings > Variables:

```bash
# REQUIRED - AI Provider
GROQ_API_KEY=gsk_your_actual_groq_key_here

# REQUIRED - Database & Auth  
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here

# Production Environment
ENVIRONMENT=production

# CORS (Auto-configured for HF Spaces)
CORS_ORIGINS=*
ALLOWED_HOSTS=*.hf.space,huggingface.co

# Optional - Additional AI Providers (Fallback)
OPENAI_API_KEY=sk-your_openai_key_here
GOOGLE_API_KEY=your_google_api_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

#### 2. Supabase Setup (Required for Persistence)
1. Create free account at https://supabase.com
2. Create new project
3. Go to Settings > API and copy:
   - Project URL → `VITE_SUPABASE_URL`
   - anon public key → `VITE_SUPABASE_ANON_KEY`
   - service_role key → `SUPABASE_SERVICE_KEY`

#### 3. GROQ API Key (Primary AI Provider)
1. Get FREE key at https://console.groq.com/keys
2. Copy key starting with `gsk_`
3. Set as `GROQ_API_KEY` in HF Spaces

---

## Deployment Steps

### Option 1: Using HuggingFace Web Interface (Recommended)

1. **Create New Space**
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Choose "Docker" as Space SDK
   - Set visibility (Public/Private)

2. **Upload Code**
   - Drag & drop your project folder OR
   - Use Git push (see Option 2)

3. **Set Environment Variables**
   - Go to Space Settings > Variables
   - Add all variables from checklist above
   - Mark sensitive ones as "Secret"

4. **Build & Deploy**
   - HuggingFace auto-builds from Dockerfile
   - First build: ~5-10 minutes
   - Subsequent builds: ~2-3 minutes

### Option 2: Using Git Push

```bash
# 1. Create Space on HuggingFace first (get the URL)

# 2. Run deployment script
.\deploy_hf.ps1

# Or manually:
git remote add huggingface https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
git push huggingface main
```

---

## Post-Deployment Configuration

### 1. Verify Deployment
- Access your Space: `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`
- Check logs for errors
- Test file upload functionality
- Test AI chat responses

### 2. Data Persistence Check
✅ User sessions persist across refreshes
✅ Uploaded files remain after restart
✅ ML models saved to storage
✅ Chat history maintained

### 3. API Rate Limiting (Production Best Practice)

**How enterprises handle this:**
- Never show users "API limit exceeded" errors
- Use multiple API keys (load balancing)
- Implement graceful degradation
- Show generic "High traffic, please wait" message

**Already implemented in DataVision:**
```python
# backend/utils/groq_client.py
# Automatic load balancing across multiple keys
# Automatic fallback to alternative models
# User never sees API limit messages
```

**To add more API keys:**
```bash
# In HuggingFace Spaces Settings > Variables
GROQ_API_KEY=gsk_primary_key
GROQ_KEY_1=gsk_backup_key_1
GROQ_KEY_2=gsk_backup_key_2
GROQ_KEY_3=gsk_backup_key_3
# System auto-rotates between them
```

---

## Security Features (Production-Grade)

### ✅ Already Implemented

1. **No Exposed API Keys**
   - All keys from environment variables
   - Sensitive data filtered from logs
   - No keys in frontend code

2. **Data Isolation**
   - Each user has separate storage directory
   - No cross-user data leakage
   - Secure file upload validation

3. **Input Validation**
   - File type whitelist
   - File size limits (100MB)
   - Filename sanitization
   - Path traversal prevention

4. **Secure Headers**
   - X-Content-Type-Options: nosniff
   - X-XSS-Protection enabled
   - CORS properly configured
   - Server header removed

5. **Database Security**
   - Row Level Security (RLS) in Supabase
   - JWT token authentication
   - Service role key server-side only

---

## Monitoring & Maintenance

### Check Space Logs
```
HuggingFace Space > Logs tab
Monitor for:
- ❌ API errors
- ⚠️ Rate limit warnings (add more keys if frequent)
- 🔒 Security issues
- 💾 Storage capacity
```

### Storage Management
- Default HF Spaces: 50GB persistent storage
- Monitor: Space Settings > Storage
- Clean old files: Admin dashboard coming soon

### Performance Optimization
```bash
# Already configured in Dockerfile:
- Non-root user for security
- Health checks enabled
- Optimized Python dependencies
- Pre-built frontend (no build in container)
```

---

## Troubleshooting

### Issue: "No API key found"
**Fix:** Add `GROQ_API_KEY` in Space Settings > Variables

### Issue: "Database connection failed"
**Fix:** Add Supabase variables (VITE_SUPABASE_URL, etc.)

### Issue: "Files not persisting"
**Fix:** Ensure `/app/storage` directory has write permissions (already configured in Dockerfile)

### Issue: "CORS error"
**Fix:** Set `CORS_ORIGINS=*` in environment variables

### Issue: "API rate limit"
**Fix:** Add multiple GROQ keys (GROQ_KEY_1, GROQ_KEY_2, etc.)

---

## Scaling Up

### Free Tier Limits
- ✅ 2 CPU cores
- ✅ 16GB RAM
- ✅ 50GB storage
- ✅ Unlimited requests

### Upgrade to Pro ($10/month)
- 🚀 4 CPU cores
- 🚀 32GB RAM
- 🚀 100GB storage
- 🚀 GPU access

### Enterprise Features
- Multiple API key rotation ✅ (already implemented)
- Graceful error handling ✅ (already implemented)
- User data isolation ✅ (already implemented)
- Audit logging ✅ (already implemented)
- Auto-scaling → Available in HF Pro

---

## Success Checklist

Before going live:
- [ ] All environment variables set in HF Spaces
- [ ] Supabase project created and configured
- [ ] GROQ API key active and tested
- [ ] Test file upload (CSV, Excel, JSON)
- [ ] Test AI chat responses
- [ ] Test AutoML model training
- [ ] Verify data persists after refresh
- [ ] Check logs for errors
- [ ] Test from multiple devices
- [ ] Verify HTTPS working

---

## Support & Documentation

- HuggingFace Spaces Docs: https://huggingface.co/docs/hub/spaces
- Supabase Docs: https://supabase.com/docs
- GROQ API Docs: https://console.groq.com/docs
- DataVision Issues: Check backend/DEPLOYMENT.md for detailed architecture

---

## Production URL Structure

```
Production Space: https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
API Endpoint: https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/api
Frontend: https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/
Docs (dev only): https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/docs
```

---

**Your DataVision AI is now production-ready! 🎉**

Users can:
- Upload any data (CSV, Excel, JSON, PDF, images)
- Get instant AI analysis
- Train ML models without code
- Generate reports and forecasts
- Everything persists across sessions
- No API limits shown to users
- Enterprise-grade security

Questions? Check logs in HuggingFace Space dashboard.
