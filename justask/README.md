# JustAsk Client Package

**Version:** 1.0.0

Mobile app and API backend for intelligent LLM query routing. Automatically routes user queries to the best free LLM provider (Gemini, Groq, OpenRouter) with built-in failover, offline queueing, and privacy-first design.

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
│  └── 7-day Response Cache (Privacy-focused)                 │
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
| **Privacy-Focused** | No history, temporary cache only (7-day TTL), local storage only |
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

**What we do:**
- Store queries + responses locally on device only
- Cache responses for 7 days (performance + privacy balance)
- Manage API keys server-side (Supabase Vault)
- No user authentication required
- No cloud sync

**What we don't do:**
- Store query history
- Track user behavior
- Collect personal data
- Expose API keys in APK
- Require user accounts

---

## License

MIT License - See LICENSE file for terms
