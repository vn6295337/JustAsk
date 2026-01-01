# JustAsk Deployment Guide

All deployments are from the main `justask` repository.

---

## Vercel (Dashboard)

**URL:** https://justask-dashboard.vercel.app/

**Deployment:** Automatic via Vercel

**Configuration:** `vercel.json` in repo root

**Triggers:**
- Push to `main` branch

---

## Render.com (API & Router)

### JustAsk API

**URL:** https://justask-api.onrender.com

**Settings:**
- **Repository:** `vn6295337/justask`
- **Branch:** `main`
- **Root Directory:** `justask/api`
- **Build Command:** `npm install`
- **Start Command:** `npm start`

### JustAsk Router

**URL:** https://justask-router.onrender.com

**Settings:**
- **Repository:** `vn6295337/justask`
- **Branch:** `main`
- **Root Directory:** `justask-router/selector-service`
- **Build Command:** `npm install`
- **Start Command:** `npm start`

---

## GitHub Actions (Registry Pipelines)

**Workflows in `.github/workflows/`:**
- `refresh-aa-performance-metrics.yml` - Daily AA metrics refresh

**Registry-specific workflows** are in `justask-registry/.github/workflows/`:
- OpenRouter pipeline
- Google pipeline
- Groq pipeline

---

## Environment Variables

### Render Services
```
NODE_ENV=production
PORT=3000 (API) or 3001 (Router)
SUPABASE_URL=<from Supabase>
SUPABASE_KEY=<from Supabase>
```

### GitHub Actions
Set in repository Settings → Secrets:
- `PIPELINE_SUPABASE_URL`
- `ARTIFICIALANALYSIS_API_KEY`
- `GROQ_API_KEY`
