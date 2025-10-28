# 🚨 Railway Deployment Fix

## Problem
Your deployment failed because **required environment variables are missing**.

## Solution (2 Steps)

### Step 1: Set Environment Variables in Railway

In your Railway dashboard, go to **Variables** and add these **3 required** variables:

```bash
YOUTUBE_RAPIDAPI_KEY=your_rapidapi_key_here
OPENAI_API_KEY=sk-your_openai_key_here
SERVICE_API_KEY=your_secure_api_key_min_16_chars
```

**How to get them:**
- **YOUTUBE_RAPIDAPI_KEY**: Subscribe to https://rapidapi.com/ytjar/api/youtube138/ and copy your key
- **OPENAI_API_KEY**: Get from https://platform.openai.com/api-keys
- **SERVICE_API_KEY**: Create your own secure random string (min 16 chars). Example:
  ```bash
  # Generate a secure key:
  openssl rand -hex 32
  ```

### Step 2: Push Updated Dockerfile

I've fixed the port binding issue. Now push to trigger a new deployment:

```bash
git add Dockerfile
git commit -m "Fix Railway port binding for dynamic $PORT"
git push origin main
```

Railway will automatically redeploy when you push.

---

## What Was Wrong?

1. ❌ **Missing ENV vars**: `YOUTUBE_RAPIDAPI_KEY`, `OPENAI_API_KEY`, `SERVICE_API_KEY` were not set
   - App crashed on startup due to Pydantic validation failure
   
2. ❌ **Hardcoded port**: Dockerfile used port `8000` but Railway uses dynamic `$PORT`
   - ✅ Fixed: Now uses `${PORT:-8000}` (Railway's port or fallback to 8000)

---

## After Setting Variables

Your deployment will succeed and you'll see:
- ✅ Build: Success
- ✅ Deploy: Success  
- ✅ Healthcheck: Passed
- ✅ Service: Running

You can test with:
```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "youtube-sl-api"
}
```

---

## Quick Railway Commands

```bash
# Set variables (alternative to dashboard)
railway variables set YOUTUBE_RAPIDAPI_KEY="your_key"
railway variables set OPENAI_API_KEY="sk-your_key"
railway variables set SERVICE_API_KEY="your_secure_key"

# View all variables
railway variables

# Trigger redeploy
railway up

# View logs
railway logs
```

---

**That's it!** Set the 3 environment variables in Railway, push the fixed Dockerfile, and your deployment will succeed. 🚀

