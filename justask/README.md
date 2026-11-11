# JustAsk Client Package

**Version:** 1.0.0

Mobile app and API backend for intelligent LLM query routing. Automatically routes user queries to the best free LLM provider (Gemini, Groq, OpenRouter) with built-in failover and offline queueing.

---

## Components

```
justask/
├── api/     # Node.js + Express backend
└── app/     # React Native + Expo mobile app
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              JUSTASK MOBILE APP                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Android App (React Native + Expo)                          │
│  ├── Search UI + Response Display                           │
│  ├── Offline Queue (SQLite)                                 │
│  └── 7-day Response Cache                                   │
│           ↓ [HTTP / Offline Detection]                      │
│  Backend API (Node.js + Express on Render)                  │
│  ├── Query Classification (Keyword-based)                   │
│  ├── Provider Routing via justask-router                    │
│  ├── Failover Chain (Primary → Secondary → Tertiary)        │
│  └── Global Rate Limiting                                   │
│           ↓ [Supabase Vault]                                │
│  LLM Providers                                              │
│  ├── Google Gemini (60 req/min, web search)                 │
│  ├── Groq (30 req/min, ultra-fast)                          │
│  └── OpenRouter (Fallback aggregator)                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Intelligent Classification** | Keyword-based query routing (instant, no LLM call overhead) |
| **Multi-Provider Failover** | Automatic fallback chain ensures reliability |
| **Offline-First** | Queue queries locally, sync when online |
| **On-Device Data** | Chat history and 7-day cache on the device; server stores no questions or IP addresses |
| **Zero Configuration** | No API keys needed in app or local config |
| **Free to Use** | All free-tier LLM providers, free backend hosting (Render) |

---

## Quick Start

### Backend Setup

```bash
cd api
npm install
npm run dev
# Server running on http://localhost:3000
```

### Mobile App Setup

```bash
cd app
npm install
npx expo start
```

---

## Configuration

Backend requires `.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-public-key
SELECTOR_SERVICE_URL=https://justask-router.onrender.com
PORT=3000
NODE_ENV=development
```

**Note:** API keys for Gemini, Groq, OpenRouter are stored in Supabase Vault (server-side only).

---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| **Frontend** | React Native (Expo) | Android app, clean UI |
| **Backend** | Node.js 18+ LTS (Express) | Stateless, Render-hosted |
| **Database** | SQLite (mobile) | Offline queue + cache only |
| **LLM APIs** | Gemini, Groq, OpenRouter | Free tiers, rate-limited |
| **Secrets** | Supabase Vault | Server-side key management |
| **Hosting** | Render (free tier) | Auto-deploy from GitHub |

---

## Data Privacy

This section matches the in-app Privacy and Terms screen (`app/src/legal/privacyText.js`). Keep them in sync.

**Who can use JustAsk**
- You must be 18 or older (in-app age check).
- JustAsk is not available in the EU, EEA, UK or Switzerland. The API returns HTTP 451 for those regions.

**Where questions go**
- The server sends each question to an AI provider: Google (Gemini), Groq, or OpenRouter. OpenRouter passes it on to one of several AI providers.
- Google may use questions to improve its products, and Google staff may read them (Gemini API free tier).
- The other providers may keep questions for a limited time, and some may use them to train AI. OpenRouter requests set `data_collection: "deny"`.
- Users are told not to type personal or private information.

**What we keep**
- The server does not save questions, answers or IP addresses. Request logs omit the client IP. The hosting provider (Render) may keep basic technical logs.
- Chat history is stored only on the device, until the user deletes it in Settings.
- Cached answers are stored on the device for 7 days, then deleted.
- API keys are managed server-side; none ship in the app.

**Credits**
- IP Geolocation by [DB-IP](https://db-ip.com), licensed under CC BY 4.0.

---

## License

MIT License - See LICENSE file for terms
