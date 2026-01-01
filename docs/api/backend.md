# Backend Deployment Guide - Render

This guide walks through deploying the JustAsk backend to Render (free tier).

## Prerequisites

1. **GitHub Account** - Push code to GitHub
2. **Render Account** - https://render.com (free tier)
3. **Supabase Account** - For API key vault
4. **API Keys** - Stored in Supabase Vault:
   - Google Gemini API key
   - Groq API key
   - OpenRouter API key

## Step-by-Step Deployment

### 1. Prepare Supabase (One-time Setup)

Ensure your API keys are stored in Supabase Vault:

```
Supabase Dashboard → Settings → Vault → Secrets

Add these secrets:
- GEMINI_API_KEY = your_gemini_key
- GROQ_API_KEY = your_groq_key
- OPENROUTER_API_KEY = your_openrouter_key
```

Your backend code reads these at runtime:
```javascript
// src/utils/supabase.js
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
const geminiKey = await supabase.vault.secrets.retrieve('GEMINI_API_KEY');
```

### 2. Push Code to GitHub

```bash
# From api directory
cd justask/api

# Commit all code
git add .
git commit -m "Prepare backend for Render deployment

- Add render.yaml for auto-deploy configuration
- Ensure package.json has correct start script
- Verify all environment variables are properly configured"

# Push to GitHub
git push origin main
```

### 3. Create Render Web Service

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. **Connect GitHub Repository:**
   - Click "Connect account" if needed
   - Select the **justask** repository
   - Click "Connect"

4. **Configure Web Service:**
   - **Name:** `justask-api`
   - **Root Directory:** `justask/api`
   - **Environment:** `Node`
   - **Region:** `Oregon` (free tier)
   - **Branch:** `main`
   - **Build Command:** `npm install` (auto-filled from render.yaml)
   - **Start Command:** `npm start` (auto-filled from render.yaml)
   - **Plan:** `Free`

5. **Set Environment Variables:**

   Click **"Environment"** and add:

   | Key | Value | Notes |
   |-----|-------|-------|
   | `SUPABASE_URL` | `https://your-project.supabase.co` | From Supabase dashboard |
   | `SUPABASE_KEY` | `your-public-anon-key` | Supabase Settings → API |
   | `SELECTOR_SERVICE_URL` | `https://justask-router.onrender.com` | Model selector service |
   | `NODE_ENV` | `production` | Set in render.yaml |
   | `PORT` | `3000` | Set in render.yaml |

6. **Create Web Service**
   - Click "Create Web Service"
   - Wait for deployment (2-3 minutes)

### 4. Verify Deployment

Once deployed, Render shows your live URL (e.g., `https://justask-api.onrender.com`).

**Test the health endpoint:**

```bash
curl https://justask-api.onrender.com/api/health
# Expected response: { "status": "ok" }
```

**Test the query endpoint:**

```bash
curl -X POST https://justask-api.onrender.com/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is artificial intelligence?"}'

# Expected response:
# {
#   "response": "AI is...",
#   "llm_used": "Groq",
#   "category": "general_knowledge",
#   ...
# }
```

### 5. Record Backend URL

Save the Render URL for app configuration:

```
Backend URL: https://justask-api.onrender.com
```

This URL will be used in the React Native app (`.env` file in Phase 2).

## Auto-Deployment

The `render.yaml` file enables auto-deployment:
- Every push to `main` branch triggers a new deployment
- Render automatically builds and restarts the service
- Health check monitors service status

## Monitoring

### View Logs

1. Go to Render Dashboard
2. Click on **justask-api** service
3. **Logs** tab shows:
   - Build logs (npm install, errors)
   - Runtime logs (HTTP requests, errors)

### Common Issues

#### Deployment Fails (Build Error)

```
Error: Cannot find module 'express'
```

**Solution:**
- Check `package.json` has all dependencies
- Run `npm install` locally and commit `package-lock.json`
- Push to GitHub and retry

#### 502 Bad Gateway

```
502 Bad Gateway
```

**Causes:**
1. Service crashed or didn't start
2. Check Logs tab for errors
3. Verify environment variables are set correctly
4. Ensure `SUPABASE_URL` and `SUPABASE_KEY` are valid

**Solution:**
- Fix error in code or env vars
- Commit and push to trigger auto-redeploy
- Check logs after deployment

#### Slow First Request (10+ seconds)

Expected on Render free tier - the service goes idle after 15 minutes and needs to restart.

**Solution:**
- First request is slow (30-60 seconds)
- Subsequent requests are fast (2-5 seconds)
- Users will see: "Server warming up... (first request may be slow)"

#### Rate Limiting (429 errors)

If you exceed provider rate limits:
- Gemini: 60 req/min
- Groq: 30 req/min

**Solution:**
- Check app is using failover chain correctly
- Verify rate limiter is working (check code: `src/rate-limiting/limiter.js`)
- Scale to standard Render plan if needed (Phase 3)

## Troubleshooting

### Environment Variables Not Showing

1. Render Dashboard → **justask-api** → **Settings**
2. Click "Environment" tab
3. Verify all 5 variables are listed (SUPABASE_URL, SUPABASE_KEY, SELECTOR_SERVICE_URL, NODE_ENV, PORT)
4. If missing, add them manually

### Port Already in Use

Render automatically assigns port 3000. If conflict:

```javascript
// src/index.js
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

This is already implemented.

### API Keys Not Loading

If `callGemini()` returns "API key not found":

1. Check Supabase credentials:
   ```bash
   # Local test
   SUPABASE_URL=your-url SUPABASE_KEY=your-key npm run dev
   curl http://localhost:3000/api/health
   ```

2. If works locally, issue is Render env vars
3. Check Render Dashboard for correct SUPABASE_URL and SUPABASE_KEY

## Next Steps

Once backend is deployed and verified:

1. **Save Backend URL** (e.g., `https://justask-api.onrender.com`)
2. **Start Phase 2:** Android app development (use backend URL in `.env`)

---

**Render Free Tier Limits:**
- 0.5 CPU, 512MB RAM
- Idles after 15 minutes (first request slower)
- Sufficient for MVP (~10 users, 10 queries/min)

**Scaling (Phase 3):**
- Upgrade to Starter plan for persistent running ($7/month)
- Add Redis for distributed rate limiting
- Add PostgreSQL for request history
