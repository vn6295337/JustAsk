# API Reference

Base URL: `https://justask-api.onrender.com`

---

## Health Check

```
GET /api/health
```

Response: `{"status": "ok"}` (200) or error (500)

---

## Query

```
POST /api/query
{"query": "What is AI?"}
```

**Classification & Routing:**

| Category | Keywords | Primary |
|----------|----------|---------|
| business_news | news, latest, today, current | Gemini |
| creative | write, poem, story, creative, compose | Groq |
| general_knowledge | other | Groq |

**Response:**
```json
{
  "response": "...",
  "llm_used": "gemini-1.5-flash|mixtral-8x7b-32768|openrouter",
  "category": "business_news|creative|general_knowledge",
  "response_time": 4250
}
```

**Status Codes:**
- 200: Success
- 400: Invalid input (empty/too long/special chars)
- 429: Rate limited (retry after 1-2 min)
- 500: All providers unavailable

**Rate Limits (per provider, global):**
- Gemini: 60 req/min
- Groq: 30 req/min
- Failover: Primary → Groq → OpenRouter

**Timeout:** 10 seconds

---

## Queue Sync (Batch)

```
POST /api/queue/sync
{
  "queries": [
    {"query": "Question 1"},
    {"query": "Question 2"}
  ]
}
```

**Response:**
```json
{
  "responses": [
    {
      "response": "...",
      "llm_used": "...",
      "category": "...",
      "response_time": 4250
    }
  ]
}
```

**Status Codes:** 200 (success), 400 (invalid), 429 (rate limit), 500 (error)

---

## Examples

**cURL:**
```bash
curl -X POST https://justask-api.onrender.com/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AI?"}'
```

**JavaScript:**
```javascript
const response = await fetch('https://justask-api.onrender.com/api/query', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({query: 'What is AI?'})
});
const data = await response.json();
console.log(data);
```

**Python:**
```python
import requests
response = requests.post('https://justask-api.onrender.com/api/query',
  json={'query': 'What is AI?'})
print(response.json())
```

---

## Providers

| Provider | Model | Strengths |
|----------|-------|-----------|
| Gemini | gemini-1.5-flash | Fast, web search for news |
| Groq | mixtral-8x7b-32768 | Very fast, creative, reliable |
| OpenRouter | Various | Fallback option |

---

## Response Times

| Scenario | Time | Notes |
|----------|------|-------|
| Cold start (Render wake) | ~15s | First request |
| Gemini | 4-6s | With search |
| Groq | 2-4s | Fast |
| OpenRouter | 5-10s | Varies |

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| Rate limited (429) | Too many requests | Wait 1-2 min, retry with backoff |
| All unavailable (500) | All providers down | Retry after 5-10 min |
| Timeout | Network/backend slow | Increase timeout, retry |
| Invalid query (400) | Empty or >2000 chars | Validate input before sending |

---

## Retry Strategy

- 1st attempt: Immediate
- 2nd attempt: Wait 1s
- 3rd attempt: Wait 5s
- 4th attempt: Wait 30s
- Final: Fail, show error
