# Getting Started

**Last Updated:** 2025-11-25
**Purpose:** Installation, configuration, and verification guide

---

## Prerequisites

**Required:**
- Node.js 18+ LTS
- npm 9.6+
- Supabase account with access to:
  - `working_version` table (read-only)
  - `model_aa_mapping` table (read-only)
  - `aa_performance_metrics` table (read-only)

**Optional:**
- Artificial Analysis API key (for Intelligence Index data)
- Redis (for production rate limit persistence)

---

## Installation

### 1. Navigate to Service Directory

```bash
cd justask-router/selector-service
```

### 2. Install Dependencies

```bash
npm install
```

**Expected packages:**
- express, cors, helmet, morgan - HTTP server
- dotenv - Environment configuration
- @supabase/supabase-js - Database client
- jest, supertest, eslint - Testing & development

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Optional
ARTIFICIAL_ANALYSIS_API_KEY=your-api-key
PORT=3001
NODE_ENV=development
LOG_LEVEL=debug
```

**Obtaining Supabase Credentials:**
1. Go to Supabase project dashboard
2. Navigate to Project Settings → API
3. Copy Project URL → `SUPABASE_URL`
4. Copy anon/public key → `SUPABASE_KEY`

### 4. Verify Database Access

Test `working_version` table access:

```bash
curl "https://your-project.supabase.co/rest/v1/working_version?limit=1" \
  -H "apikey: your-anon-key"
```

Expected: JSON array with model data

---

## Running the Service

### Development Mode

```bash
npm run dev
```

Uses Node.js `--watch` flag for automatic reloading on file changes.

### Production Mode

```bash
npm start
```

### Running Tests

```bash
npm test              # Run all tests with coverage
npm run test:watch    # Watch mode for TDD
```

---

## Verification

### 1. Health Check

```bash
curl http://localhost:3001/health
```

**Expected response:**
```json
{
  "status": "ok",
  "timestamp": "2025-11-24T...",
  "cache": {
    "modelsCount": 50,
    "lastRefresh": "2025-11-24T..."
  },
  "rateLimits": {
    "groq": {"headroom": 1.0},
    "google": {"headroom": 1.0},
    "openrouter": {"headroom": 1.0}
  }
}
```

### 2. List Available Models

```bash
curl http://localhost:3001/models
```

**Expected response:**
```json
{
  "models": [
    {
      "inference_provider": "groq",
      "human_readable_name": "Llama 3.3 70B Versatile",
      "aa_performance_metrics": {
        "intelligence_index": 64.1
      }
    }
  ],
  "count": 50,
  "cached": true,
  "lastUpdate": "2025-11-24T..."
}
```

### 3. Get Best Model

```bash
curl "http://localhost:3001/best-model?provider=groq"
```

**Expected response:**
```json
{
  "model": {
    "provider": "groq",
    "modelSlug": "gpt-oss-20b",
    "humanReadableName": "GPT OSS 20B",
    "intelligenceIndex": 52.4
  },
  "selectionCriteria": {
    "method": "intelligence_index",
    "filterProvider": "groq"
  }
}
```

### 4. Test Model Selection (Full)

```bash
curl -X POST http://localhost:3001/select-model \
  -H "Content-Type: application/json" \
  -d '{
    "queryType": "general_knowledge",
    "queryText": "What is the capital of France?",
    "modalities": ["text"],
    "complexityScore": 0.3
  }'
```

**Expected response:**
```json
{
  "provider": "groq",
  "modelName": "gpt-oss-20b",
  "humanReadableName": "GPT OSS 20B",
  "score": 0.87,
  "rateLimitHeadroom": 1.0,
  "estimatedLatency": "low",
  "intelligenceIndex": 52.4,
  "selectionReason": "High Intelligence Index with excellent rate limit headroom"
}
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 3001
lsof -i :3001

# Kill process
kill -9 <PID>

# Or change port in .env
PORT=3002
```

### Supabase Connection Failed

**Check credentials:**
```bash
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

**Test connection:**
```bash
curl "https://your-project.supabase.co/rest/v1/" \
  -H "apikey: your-anon-key"
```

**Common issues:**
- Wrong API key (use anon key, not service_role key)
- RLS policies blocking read access (check policies allow public SELECT)
- Network firewall blocking Supabase domains

### No Models Returned

**Check table access:**
```bash
# Verify working_version has data
curl "https://your-project.supabase.co/rest/v1/working_version?select=count" \
  -H "apikey: your-anon-key"

# Verify model_aa_mapping has mappings
curl "https://your-project.supabase.co/rest/v1/model_aa_mapping?select=count" \
  -H "apikey: your-anon-key"
```

**Solution:**
- Ensure RLS policies allow public read access
- Run `populate_model_aa_mapping.js` if mappings are missing (see migration docs)

### Intelligence Index Unavailable

Service operates with fallback scoring if Artificial Analysis API is unavailable. Check logs for:

```
[WARN] Intelligence Index unavailable, using fallback scoring
```

This is expected behavior if `ARTIFICIAL_ANALYSIS_API_KEY` is not provided.

---

## Deployment

For deployment configuration (Render, Docker), see [06_configuration.md](06_configuration.md#deployment-configuration).

---

## Next Steps

- **Architecture:** Review [03_architecture.md](03_architecture.md) for system design
- **Configuration:** See [06_configuration.md](06_configuration.md) for deployment and settings
- **API Reference:** Check [07_api_reference.md](07_api_reference.md) for endpoints
- **Testing:** Check [05_testing_strategy.md](05_testing_strategy.md) for test approach

---

**Document Owner:** Development Team
