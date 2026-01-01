# JustAsk API - Intelligent LLM Query Router

Node.js + Express backend for routing user queries to the most suitable free LLM provider (Gemini, Groq, OpenRouter) with automatic failover and rate limiting.

## Features

- **Keyword-based Query Classification:** Instant categorization (news/general/creative) with no API calls
- **Intelligent Provider Routing:** Selects best LLM based on query type
- **Global Failover:** Primary → Groq → OpenRouter chain when provider unavailable
- **Rate Limiting:** Enforces per-provider limits (60/min Gemini, 30/min Groq)
- **Stateless Architecture:** No backend queueing; app handles offline retry
- **Secure API Key Management:** Keys stored in Supabase Vault (server-side only)

## Tech Stack

- **Runtime:** Node.js 18 LTS
- **Framework:** Express 4.18+
- **LLM Clients:** @google/generative-ai, groq-sdk, openrouter-js
- **Security:** helmet, cors
- **Logging:** morgan
- **Key Management:** @supabase/supabase-js

## Prerequisites

- Node.js 18.17.0+ (⚠️ required for LLM SDKs)
- npm 9.6.0+
- Supabase account with API keys vault configured
- API keys from Gemini, Groq, and OpenRouter

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Update with your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-public-key
PORT=3000
NODE_ENV=development
```

⚠️ **Important:** API keys are stored in Supabase Vault, NOT in `.env`. This keeps them server-side only and out of the APK.

### 3. Verify Setup

Test that the server starts:

```bash
npm run dev
```

Should output: `Server running on http://localhost:3000`

Test health endpoint:

```bash
curl http://localhost:3000/api/health
# Expected: { "status": "ok" }
```

## API Endpoints

### Health Check

```
GET /api/health
Response: { status: "ok" }
```

### Query Endpoint

```
POST /api/query
Request: { query: string }
Response: {
  response: string,
  llm_used: string,
  category: string,
  response_time: number
}
```

### Offline Sync

```
POST /api/queue/sync
Request: { queries: [{ query: string, timestamp: number }] }
Response: { responses: [{ response: string, llm_used: string, ... }] }
```

## Deployment

### Deploy to Render

1. Push code to GitHub
2. Create new Web Service on Render
3. Connect repository
4. Set environment variables in Render dashboard (Supabase credentials)
5. Deploy

See `DEPLOYMENT.md` for detailed instructions.

## Development

### Run with Watch Mode

```bash
npm run dev
```

### Run Tests

```bash
npm test
npm run test:watch
```

### Linting

```bash
npm run lint
npm run lint:fix
```

## Error Handling

All endpoints return consistent error format:

```json
{
  "error": "Error message",
  "status": 400
}
```

Common errors:
- **400:** Invalid query (empty, too long, missing)
- **429:** Rate limit exceeded (wait before retry)
- **500:** Backend error (all LLM providers failed)

## Architecture

```
Request
  ↓
Validation (1.6)
  ↓
Classification (1.9) → news/creative/general
  ↓
Routing (1.10) → select primary provider
  ↓
Failover Chain (1.11) → Primary → Groq → OpenRouter
  ↓
Response Normalization (1.8)
  ↓
Rate Limiting (1.12)
  ↓
Response
```

## Security

- ✅ No API keys in APK (server-side only)
- ✅ CORS enabled for mobile app only
- ✅ Security headers via helmet
- ✅ Input validation on all endpoints
- ✅ Rate limiting per provider

## Troubleshooting

**Issue:** Server won't start
- Check Node.js version: `node --version` (must be 18+)
- Clear node_modules: `rm -rf node_modules && npm install`

**Issue:** API keys not working
- Verify Supabase credentials in `.env`
- Check Supabase Vault has keys stored

**Issue:** Slow responses
- Render free tier has 15min idle timeout (first request slow)
- Normal response time: 2-8 seconds depending on LLM

## License

MIT
