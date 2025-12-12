# Hugging Face Spaces Deployment Guide

## AI Business Analyst - Deployment to Hugging Face Spaces

This guide will help you deploy the AI Business Analyst application to Hugging Face Spaces using Docker.

---

## Prerequisites

1. **Hugging Face Account** - Create one at [huggingface.co](https://huggingface.co/join)
2. **Git installed** on your machine
3. **Hugging Face CLI** (optional but recommended)

---

## Step 1: Create a New Hugging Face Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Enter a Space name: `ai-business-analyst`
3. Select **Docker** as the SDK
4. Select **Blank** Docker template
5. Choose visibility: **Public** (free) or **Private** (Pro plan)
6. Click **Create Space**

---

## Step 2: Clone Your New Space

```bash
# Install Hugging Face CLI if not installed
pip install huggingface_hub

# Login to Hugging Face
huggingface-cli login

# Clone your new space (replace YOUR_USERNAME)
git clone https://huggingface.co/spaces/YOUR_USERNAME/ai-business-analyst
cd ai-business-analyst
```

---

## Step 3: Copy Project Files

Copy all your project files to the cloned space directory:

```bash
# Copy backend
cp -r "c:\Users\navee\Cisco Packet Tracer 8.2.2\saves\ai_business_analyst\backend" ./backend

# Copy frontend
cp -r "c:\Users\navee\Cisco Packet Tracer 8.2.2\saves\ai_business_analyst\frontend" ./frontend

# Copy requirements
cp "c:\Users\navee\Cisco Packet Tracer 8.2.2\saves\ai_business_analyst\requirements.txt" ./requirements.txt

# Copy Dockerfile (created for you)
cp "c:\Users\navee\Cisco Packet Tracer 8.2.2\saves\ai_business_analyst\Dockerfile" ./Dockerfile
```

---

## Step 4: Set Environment Variables (Secrets)

Go to your Space settings → **Repository secrets** and add:

| Secret Name | Description |
|-------------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Your Supabase anon/public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase service role key |
| `SUPABASE_JWT_SECRET` | Your Supabase JWT secret |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `GEMINI_API_KEY` | Your Gemini API key (if using) |

---

## Step 5: Configure OAuth Redirect URLs

> **CRITICAL:** This is the most important step for fixing OAuth authentication in production!

### A. Supabase Configuration

1. Go to **Supabase Dashboard** → **Authentication** → **URL Configuration**

2. Set **Site URL** to your Hugging Face Space URL:
   ```
   https://YOUR_USERNAME-ai-business-analyst.hf.space
   ```

3. Add **Redirect URLs** (one per line):
   ```
   http://localhost:5173/auth/callback
   https://YOUR_USERNAME-ai-business-analyst.hf.space/auth/callback
   ```

4. Click **Save**

---

### B. Google OAuth Configuration

> **NOTE:** Skip this if you're not using Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Click on your **OAuth 2.0 Client ID**
4. Under **Authorized JavaScript origins**, add:
   ```
   https://YOUR_USERNAME-ai-business-analyst.hf.space
   ```
5. Under **Authorized redirect URIs**, add:
   ```
   https://YOUR_USERNAME-ai-business-analyst.hf.space/auth/callback
   https://YOUR_SUPABASE_PROJECT.supabase.co/auth/v1/callback
   ```
   Replace `YOUR_SUPABASE_PROJECT` with your actual Supabase project reference (found in Supabase Dashboard → Settings → API)

6. Click **Save**

---

### C. GitHub OAuth App Configuration

> **NOTE:** Skip this if you're not using GitHub OAuth

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **OAuth Apps** → Select your app
3. Set **Homepage URL**:
   ```
   https://YOUR_USERNAME-ai-business-analyst.hf.space
   ```
4. Set **Authorization callback URL**:
   ```
   https://YOUR_SUPABASE_PROJECT.supabase.co/auth/v1/callback
   ```
   Replace `YOUR_SUPABASE_PROJECT` with your actual Supabase project reference

5. Click **Update application**

---

### D. Verify Provider Configuration in Supabase

1. Go to **Supabase Dashboard** → **Authentication** → **Providers**
2. Ensure **Google** is enabled (if using Google OAuth):
   - Toggle ON
   - Enter your Google Client ID and Client Secret
3. Ensure **GitHub** is enabled (if using GitHub OAuth):
   - Toggle ON
   - Enter your GitHub Client ID and Client Secret
4. Click **Save**

---

## Step 6: Push to Hugging Face

```bash
# Add all files
git add .

# Commit
git commit -m "Initial deployment of AI Business Analyst"

# Push to Hugging Face
git push
```

---

## Step 7: Wait for Build

1. Go to your Space: `https://huggingface.co/spaces/YOUR_USERNAME/ai-business-analyst`
2. Click on the **Build** tab to monitor progress
3. Build takes ~5-10 minutes for first deployment

---

## Troubleshooting

### Build Fails
- Check the **Build logs** for errors
- Ensure all environment secrets are set correctly
- Verify Dockerfile syntax

### App Shows "Building"
- Hugging Face free tier may sleep after inactivity
- First request after sleep takes 30-60 seconds to wake up

### OAuth Not Working
- Check redirect URLs are correctly configured
- Ensure Space URL matches exactly in Supabase and Google Console

---

## Accessing Your Deployed App

Once deployed, your app will be available at:
```
https://YOUR_USERNAME-ai-business-analyst.hf.space
```

---

## Updating Your App

To push updates:
```bash
git add .
git commit -m "Update: description of changes"
git push
```

The Space will automatically rebuild and redeploy.
