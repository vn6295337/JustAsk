# Audit: justask/api and justask/app

Static review, 2026-11-02. Paths relative to `justask/`.

## High
- `api/src/index.js:49`, `routes/query.js:14,68` — no auth, no inbound rate limiting; `checkRateLimit` (limiter.js) never called; `config.rateLimits` unused. Quota/billing drain.
- `routes/query.js:77-118`, `middleware/validate.js:113` — `/queue/sync` allows 100 sequential LLM calls × up to 3 providers per request; single Render instance. `express.json()` 100kb default (`index.js:37`) rejects legitimate 200kb batches (413).
- `failover/failover.js:14-27`, `routing/rankedModelSelector.js:49` — `model.modelName` never passed to provider; rank 1/2 on same provider call same model; response reports unused model/rank.
- `providers/gemini.js:39-41`, `groq.js:51`, `openrouter.js:66-68` — empty/blocked completions become "successful" placeholders; failover doesn't advance; app caches placeholder 7 days (`HomeScreen.js:205`).
- `app/src/services/SyncManager.js:16-29` — `isSyncing` check-then-set race across `await NetInfo.fetch()`; reconnect handler and manual Sync (`SettingsScreen.js:91`) duplicate LLM calls/messages.
- `SyncManager.js:158-161`, `routes/query.js:98-105` — `success:false` items stay `pending` forever; no attempt counter; re-billed each sync.
- `SyncManager.js:66-85`, `APIClient.js:5` — 30 s timeout, whole-batch retry ×3 while server continues abandoned requests; spend multiplies at ~10+ queued queries.

## Medium
- `validate.js:62-75` vs `120-139` — XSS regex only on `/query`, not `/queue/sync`; `on\w+\s*=` false-positives ("region=EU"); rejected queries get queued then accepted unvalidated.
- `SyncManager.js:119-141` — synced answer appended as detached message; "queued" placeholder never updated.
- `app/src/services/Database.js:20-28,103-105` — `db` returned before `createTables()` completes; errors swallowed.
- `Database.js:294-299` — `close()` doesn't reset `initPromise`; stale closed handle.
- `HomeScreen.js:171-196` — 7-day cache for all query types incl. news/prices.
- `HomeScreen.js:236-239`, `Database.js:111-128` — any API failure queues query; queue size cap ignored.
- `app/src/services/CacheManager.js:7-14,41-44` — 32-bit FNV key, UNIQUE on hash, `query_text` never compared; collisions return wrong answer; case/whitespace-sensitive.
- `Database.js:152-165` — response insert + status update not transactional; duplicates on partial failure.
- `Database.js:249-255`, `HomeScreen.js:140-166` — history ordered by 1 s `created_at`, no `id` tiebreak; "Thinking..." persists if app killed.
- `failover/failover.js:68-91` + providers — thrown plain objects without `.message`; logs `undefined`; route always 500 (`query.js:30`), 429 indistinguishable from outage.
- `rankedModelSelector.js:16` — selector `fetch` has no timeout/cache; blocks during router cold start.
- `providers/gemini.js:36`, `groq.js:38` — no timeouts; `config.responseTimeouts` only used for OpenRouter.
- `api/.env.example:9-12` vs `utils/supabase.js:36` — example documents `OPENROUTER_API_KEY`, code reads `OPENROUTER_API_KEY_2`; `config.nodeEnv` defaults to development (placeholder `dev-*-key`); `createClient(undefined)` throws at import.

## Low
- `index.js:64-73`, `routes/query.js:54-58,113` — raw `error.message` returned to clients.
- `index.js:20-27` — literal `'*'` in CORS array with `credentials:true`; does not allow-all (comment is wrong).
- `Database.js:227-236` — `updateMessage` interpolates object keys into SQL (safe today).
- `Database.js:46-100`, `app.config.js` — plaintext SQLite; `android.allowBackup` not disabled (generated manifest not checked).
- `CacheManager.js:84-88,131-154` — size via `LENGTH()` (chars); rough eviction; return ignored; expired rows only deleted on same-query lookup; unbounded growth.
