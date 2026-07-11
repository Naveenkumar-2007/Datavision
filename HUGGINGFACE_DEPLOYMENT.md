# 🚀 HuggingFace Spaces Deployment Guide

## Production-Ready DataVision AI

This project is configured with a **fully automated CI/CD pipeline**. Any code you push to the `main` branch of this GitHub repository will automatically be deployed to your HuggingFace Space.

Your HuggingFace Space: [https://datavision-ai-datavision.hf.space](https://datavision-ai-datavision.hf.space)

### Pre-Deployment Checklist ✅

#### 1. Setup GitHub Actions CI/CD (One-time setup)
To allow GitHub to push to HuggingFace Spaces on your behalf, you need a HuggingFace Write Token:
1. Go to your HuggingFace Settings: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Create a new token with **Write** permissions and copy it.
3. Go to this GitHub repository's Settings > **Secrets and variables** > **Actions**
4. Click **New repository secret**
5. Name: `HF_TOKEN`
6. Secret: paste your copied HuggingFace token

#### 2. Environment Variables (CRITICAL)
Your actual secrets must be added to your HuggingFace Space (they are NOT in GitHub).
Go to HuggingFace Space Settings > **Variables and secrets**. 
Add the following as **Secrets**:

```bash
# REQUIRED - AI Provider
GROQ_API_KEY=gsk_your_actual_groq_key_here

# REQUIRED - Database (PostgreSQL hosted e.g. Neon, Supabase Postgres, Railway)
# Localhost will NOT work on HuggingFace.
DATABASE_URL=postgresql+asyncpg://user:password@hostname:5432/datavision

# REQUIRED - Authentication
JWT_SECRET=your_randomly_generated_jwt_secret

# Production Environment
ENVIRONMENT=production

# CORS (Auto-configured for HF Spaces)
CORS_ORIGINS=*
ALLOWED_HOSTS=*.hf.space,huggingface.co
```

---

## Deployment Workflow

### 1. The Automated Way (GitHub CI/CD) - Recommended
Because we've configured GitHub Actions, deployment is completely hands-off.

```bash
# 1. Make your changes locally
git add .
git commit -m "Your descriptive commit message"

# 2. Push to GitHub
git push origin main
```
**What happens next?**
1. GitHub Actions automatically starts the CI Pipeline (`ci.yml`). It lints the Python backend and builds the frontend.
2. If successful, it starts the Deployment Pipeline (`deploy.yml`).
3. GitHub pushes the code directly to HuggingFace.
4. HuggingFace rebuilds the Docker container automatically (takes ~5 minutes).

### 2. Manual Fallback Way (If CI fails)
If you ever need to bypass GitHub Actions and push directly to HuggingFace:

```bash
# 1. Add HuggingFace remote manually (first time only)
git remote add huggingface https://huggingface.co/spaces/datavision-ai/Datavision

# 2. Force push
git push --force huggingface main
```

---

## Database Configuration for HuggingFace

HuggingFace Spaces are ephemeral Docker containers. This means a local SQLite or Localhost PostgreSQL database will **lose all data when the space goes to sleep**. 

To maintain user accounts, chats, and configurations, you MUST use an external hosted PostgreSQL database.

**Recommended Free Providers:**
1. **Neon** (https://neon.tech): Excellent free tier, serverless Postgres.
2. **Railway** (https://railway.app): Easy Postgres provisioning.
3. **Supabase** (https://supabase.com): Create a project and grab the Postgres connection string from Settings > Database. (You do not need the Supabase JS SDK, just the pure Postgres string).

*Note: Your `DATABASE_URL` must start with `postgresql+asyncpg://` for our SQLAlchemy setup.*

### Alembic Migrations
When your HuggingFace space boots up, the `start.sh` script automatically runs `alembic upgrade head`. This ensures your database schema is perfectly in sync with your code!

---

## Post-Deployment Validation

### 1. Verify Deployment
- Access your Space: `https://datavision-ai-datavision.hf.space`
- Check HuggingFace logs for any runtime errors.
- Create an account and log in.

### 2. Check Persistent Storage
HuggingFace Spaces comes with 50GB of persistent storage mounted at `/app/storage` (where we configured it in the Dockerfile).
- Upload a file and verify it persists after the space reboots.
- Check that trained AutoML models and vector FAISS indexes are saved properly.

---

## Troubleshooting

### Issue: GitHub Action Fails on Deploy
**Fix:** Ensure you added the `HF_TOKEN` exactly as specified in the GitHub Secrets. Check the action logs for specific Git errors.

### Issue: "Application Startup Failed" in HF Logs
**Fix:** Likely a database connection issue or missing `GROQ_API_KEY`. Verify all secrets in HF Settings and ensure your `DATABASE_URL` is accessible from the internet.

### Issue: "Database schema out of date"
**Fix:** Restart the space. The `start.sh` script will run `alembic upgrade head` again.

---

See `MLOPS.md` for complete architecture and lifecycle details.
