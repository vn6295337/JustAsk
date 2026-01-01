# API Reference

**Last Updated:** 2025-12-30
**Base URL:** `http://localhost:3001` (development) | `https://selector-service-xxxx.onrender.com` (production)

---

## Endpoints

### POST /select-model

Select optimal model based on query characteristics.

**Request:**
```json
{
  "queryType": "general_knowledge",
  "queryText": "What is the capital of France?",
  "modalities": ["text"],
  "complexityScore": 0.3
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| queryType | string | Yes | Category: `business_news`, `financial_analysis`, `creative`, `general_knowledge` |
| queryText | string | Yes | The actual query text (used for token estimation) |
| modalities | string[] | Yes | Required capabilities: `text`, `image`, `audio`, `video` |
| complexityScore | float | Yes | Complexity rating 0.0-1.0 (calculated by client) |

**Response (200):**
```json
{
  "provider": "groq",
  "modelName": "llama-3.1-70b-versatile",
  "humanReadableName": "Llama 3.1 70B Versatile",
  "score": 0.87,
  "rateLimitHeadroom": 0.95,
  "intelligenceIndex": 52.4,
  "estimatedLatency": "low",
  "selectionReason": "High intelligence score, Excellent rate limit headroom",
  "selectionDuration": 5,
  "modalities": {
    "input": "Text",
    "output": "Text"
  },
  "license": "Llama-3.1"
}
```

**Error Response (400):**
```json
{
  "error": "Missing required field: queryText",
  "code": "INVALID_REQUEST"
}
```

**Error Response (500):**
```json
{
  "error": "No models available matching criteria",
  "code": "NO_MODELS_AVAILABLE"
}
```

---

### GET /best-model

Get best model by Intelligence Index, optionally filtered by provider.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| provider | string | No | Filter by: `groq`, `google`, `openrouter` |

**Request:**
```bash
curl "http://localhost:3001/best-model?provider=groq"
```

**Response (200):**
```json
{
  "model": {
    "provider": "groq",
    "modelSlug": "gpt-oss-20b",
    "humanReadableName": "GPT OSS 20B",
    "intelligenceIndex": 52.4,
    "codingIndex": 48.2,
    "mathIndex": 45.1
  },
  "selectionCriteria": {
    "method": "intelligence_index",
    "filterProvider": "groq"
  },
  "timestamp": "2025-12-30T12:00:00.000Z"
}
```

**Error Response (404):**
```json
{
  "error": "No models with Intelligence Index available",
  "code": "NO_MODELS_WITH_INDEX"
}
```

---

### GET /models

List all available models from cache.

**Response (200):**
```json
{
  "models": [
    {
      "inference_provider": "groq",
      "human_readable_name": "Llama 3.3 70B Versatile",
      "aa_performance_metrics": {
        "intelligence_index": 64.1
      },
      "rate_limits_normalized": {
        "rpm": 30,
        "tpm": 15000
      }
    }
  ],
  "count": 50,
  "cached": true,
  "lastUpdate": "2025-12-30T12:00:00.000Z"
}
```

---

### GET /health

Health check with cache and rate limit statistics.

**Response (200):**
```json
{
  "status": "ok",
  "timestamp": "2025-12-30T12:00:00.000Z",
  "uptime": 3600,
  "cache": {
    "size": 2,
    "entries": [
      {"key": "ai_models_main", "age": "1800s", "expired": false}
    ]
  },
  "rateLimits": {
    "Llama 3.1 70B Versatile": {
      "limits": {"rpm": 30, "rpd": 14400, "tpm": 15000, "tpd": 500000},
      "headroom": {"rpm": "95%", "rpd": "98%", "tpm": "99%", "tpd": "100%", "overall": "95%"},
      "recentUsage": {"requestsLastMinute": 2, "tokensLastMinute": 150}
    }
  }
}
```

---

### POST /cache/refresh

Force cache refresh (bypasses TTL).

**Response (200):**
```json
{
  "message": "Cache refreshed",
  "modelsCount": 50,
  "timestamp": "2025-12-30T12:00:00.000Z"
}
```

---

### POST /rate-limits/reset

Reset rate limit counters (for testing only).

**Response (200):**
```json
{
  "message": "Rate limit counters reset",
  "timestamp": "2025-12-30T12:00:00.000Z"
}
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Missing or invalid request fields |
| `NO_MODELS_AVAILABLE` | 500 | No models match the selection criteria |
| `NO_MODELS_WITH_INDEX` | 404 | No models have Intelligence Index data |
| `DATABASE_ERROR` | 500 | Supabase query failed |
| `CACHE_ERROR` | 500 | Cache operation failed |

---

## Client Integration

### JavaScript/Node.js

```javascript
async function selectModel(criteria) {
  const response = await fetch('http://localhost:3001/select-model', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(criteria),
    timeout: 5000
  });

  if (!response.ok) {
    throw new Error(`Selection failed: ${response.status}`);
  }

  return response.json();
}

// Usage
const selection = await selectModel({
  queryType: 'general_knowledge',
  queryText: 'What is quantum computing?',
  modalities: ['text'],
  complexityScore: 0.5
});

console.log(`Selected: ${selection.humanReadableName} (${selection.provider})`);
```

### cURL

```bash
# Select model
curl -X POST http://localhost:3001/select-model \
  -H "Content-Type: application/json" \
  -d '{
    "queryType": "general_knowledge",
    "queryText": "What is the capital of France?",
    "modalities": ["text"],
    "complexityScore": 0.3
  }'

# Get best model
curl "http://localhost:3001/best-model?provider=groq"

# Health check
curl http://localhost:3001/health
```

---

**Document Owner:** Development Team
