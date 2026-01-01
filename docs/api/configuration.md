# Configuration

## Environment Variables

**File:** `.env` (root of justask/app, not committed)

| Variable | Default | Description |
|----------|---------|-------------|
| `EXPO_PUBLIC_BACKEND_URL` | https://justask-api.onrender.com | Backend API endpoint |
| `EXPO_PUBLIC_API_TIMEOUT` | 10000 | Request timeout (ms) |
| `EXPO_PUBLIC_CACHE_TTL_DAYS` | 7 | Cache expiration (days) |
| `EXPO_PUBLIC_CACHE_SIZE_LIMIT_MB` | 50 | Max cache size (MB) |
| `EXPO_PUBLIC_OFFLINE_QUEUE_MAX_SIZE` | 10 | Max pending queries |
| `EXPO_PUBLIC_APP_VERSION` | 0.1.0 | App version |
| `EXPO_PUBLIC_DEBUG` | false | Enable debug logging |

## App Configuration

**File:** `justask/app/app.json`

| Key | Value |
|-----|-------|
| Name | JustAsk |
| Version | 1.0.0 |
| Package | com.justask.app |
| Permissions | INTERNET, ACCESS_NETWORK_STATE |

## Backend Configuration

**Rates (per provider, global):**
- Gemini: 60 req/min
- Groq: 30 req/min
- OpenRouter: Provider-dependent

**Keywords (classification):**
```
news: ["news", "latest", "today", "current"]
creative: ["write", "poem", "story", "creative", "compose"]
default: general_knowledge
```

**Failover:** Primary → Groq → OpenRouter

## Database Schema

See DATABASE_SCHEMA.md
