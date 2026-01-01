# JustAsk Platform Overview

**Just ask. No signup. Forever free.**

A free AI assistant platform that routes user queries to the best available AI model automatically.

---

## Architecture

| Service | Purpose | Tech | Hosting |
|---------|---------|------|---------|
| **justask-api** | Backend API, failover logic | Node.js/Express | Render |
| **justask-app** | Mobile app | React Native/Expo | Expo Go |
| **justask-dashboard** | Analytics visualization | React/Vite | Vercel |
| **justask-router** | 5-factor model selection | Node.js | Render |
| **justask-registry** | Data pipelines (Google, Groq, OpenRouter) | Python | GitHub Actions |

---

## How It Works

1. User sends query via mobile app
2. API classifies query and calls router
3. Router scores available models using 5 factors:
   - Intelligence
   - Latency
   - Rate Limits
   - Geography
   - License
4. API calls selected provider (Groq → Gemini → OpenRouter fallback chain)
5. Response returned to user

---

## Database

- **Supabase** PostgreSQL (shared by all services)
- Tables: `ai_models_main`, `ai_models_working`, performance metrics, rate limits

---

## Production URLs

| Service | URL |
|---------|-----|
| Dashboard | https://justask-dashboard.vercel.app/ |
| API | https://justask-api.onrender.com |
| Router | https://justask-router.onrender.com |

---

## Running the Mobile App

Start the Expo development server with tunnel mode:

```bash
cd justask/app
npx expo start --tunnel
```

Scan the QR code with **Expo Go** app ([Android](https://play.google.com/store/apps/details?id=host.exp.exponent) | [iOS](https://apps.apple.com/app/expo-go/id982107779)).
