# Architecture Overview

## System Design

```
┌─────────────┐         ┌──────────────┐         ┌────────────┐
│   Mobile    │──HTTPS──│   Express    │──REST───│   LLMs     │
│   App       │         │   Backend    │         │ (G,Gr,OR)  │
│  (React     │         │  (Render)    │         │            │
│  Native)    │         │              │         └────────────┘
└─────────────┘         └──────────────┘
     SQLite                Stateless
   (Local)           (No persistence)
```

## Layer Stack

### Client Layer
- **Framework:** React Native (Expo 51)
- **State:** Redux Toolkit
- **Network:** Axios with 10s timeout
- **Storage:** SQLite (offline queue, cache)

### Backend Layer
- **Runtime:** Node.js 18 LTS
- **Framework:** Express.js
- **Deployment:** Render (free tier)
- **Architecture:** Stateless (no DB)

### Data Layer
- **Query Queue:** SQLite on device
- **Response Cache:** SQLite with 7-day TTL
- **Rate State:** In-memory (per backend instance)

## Data Flow

**Online Query:**
1. User input → Validation
2. Cache lookup (MD5 hash)
3. Cache hit → Immediate response
4. Cache miss → Classification → Provider selection
5. Failover chain: Primary → Groq → OpenRouter
6. Response → Save cache → Display

**Offline Query:**
1. User input → Validation
2. SQLite save (offline_queue)
3. Display "saved" badge
4. On network restore → Auto-detect
5. Batch POST to /api/queue/sync
6. Exponential backoff retry (1s, 5s, 30s)
7. Save responses → Update DB → Display

## Provider Routing

| Query Type | Keywords | Primary | Secondary | Tertiary |
|-----------|----------|---------|-----------|----------|
| News | news, latest, today | Gemini | Groq | OR |
| Creative | write, poem, story | Groq | Gemini | OR |
| General | Other | Groq | Gemini | OR |

## Rate Limits

- Gemini: 60 req/min
- Groq: 30 req/min
- Hit limit → Failover to next provider

## Offline Support

- Max queue: 10 queries (config)
- Sync trigger: Network restoration
- Retry: 1s → 5s → 30s → Fail
- Data persistence: Device-local only

## Caching Strategy

- Key: MD5(query.toLowerCase())
- TTL: 7 days (config: EXPO_PUBLIC_CACHE_TTL_DAYS)
- Size limit: 50 MB (config: EXPO_PUBLIC_CACHE_SIZE_LIMIT_MB)
- Eviction: Oldest entries deleted when limit exceeded

## Privacy Model

- ✅ Queries stored locally (SQLite)
- ✅ Cache stored locally (7 days, auto-expires)
- ✅ No cloud sync
- ✅ No analytics
- ✅ No user tracking
- ✅ Backend stateless (no persistence)

## Security

- HTTPS: Render-managed SSL
- API Keys: Supabase Vault (server-side)
- Input validation: Length (1-2000), special chars
- No hardcoded secrets in APK
