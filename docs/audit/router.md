# Audit: justask-router/selector-service

Static review, 2026-11-02. Paths relative to `justask-router/selector-service/`.

## High
- `scripts/db/create_model_selection_score_table.sql:71-84`, `create_rate_limits_table.sql:36-52` — anon INSERT/UPDATE with `USING(true)`; anon key can alter rankings and enforced limits. `CREATE POLICY` not idempotent.
- `src/index.js:341,362` — `/cache/refresh`, `/rate-limits/reset` unauthenticated; `cors()` open; `/health` exposes per-model limits/usage.
- `src/services/modelSelector.js:138` + `intelligenceIndex.js:599-614` — `scoresMap[model.human_readable_name]` but map keyed by AA slug; `aa_performance_metrics` join never read. Most models get fallback 0.6; `/best-models` and `/select-model` disagree. Tests hand-craft slug-keyed map, hiding this.
- `src/index.js:270-292` — no type validation: array/number `queryText` → NaN tokens → tpm/tpd NaN for 24 h → model silently excluded; `complexityScore:"abc"` passes (=0 headroom needed); `modalities:"text"` → 500.
- `modelSelector.js:248,135` — `provider.toLowerCase()` with no null guard; one NULL `inference_provider` row 500s every `/select-model`.

## Medium
- `intelligenceIndex.js:459` + `cacheManager.js:297-305` — `get()` ignores expiry; 7-day TTL never enforced.
- `intelligenceIndex.js:485` — failed AA fetch returns `{}` uncached; refetch every request.
- `index.js:341-346` — `invalidate()` before awaited fetch; Supabase failure leaves no cache.
- `cacheManager.js:380-398` — no in-flight dedupe; thundering herd, 4 queries/request on failure.
- `modelSelector.js:217-229,73-77` — low complexity accepts `headroom >= 0`; relaxed fallback ignores headroom; exhausted models still chosen.
- `rateLimitTracker.js:35-37`, `modelSelector.js:40-47` — tracker keyed by `human_readable_name` only; limits fixed at init.
- `intelligenceIndex.js:630-634` — substring size matching (`qwen3-32b`→`2b`, `llama-3.2-11b`→`1b`, `deepseek-14b`→`4b`).
- `scripts/db/populate_model_selection_score.js` — `:95-99` license substring match ("Limited" scores open); default license 0.8 vs 0.9 runtime; `:105-107` missing intelligence 0 vs 0.6; `:138` headroom avg vs runtime min; `:271` provider not lowercased (stored `latency_score` may be 0.5 for all — case unverified).
- `populate_model_selection_score.js:366-381`, `populate_rate_limits.js:71-80` — upsert without deleting stale rows.
- `index.js:193-196` — `limit=abc` → NaN passes validation → DB 500.
- `index.js:80-130` — `/best-model` queries `public.*` tables/columns superseded by `ims."10_…"`/`"20_…"`; likely 500/404 (not confirmed); new client per request; no env check (`:83-86`).
- `scripts/db/refresh_aa_performance_metrics.py:252-257,160-168` — no record-count sanity; truncated/empty API replaces table; zero records exits 0; unreliable `rowcount`.
- `refresh_aa_performance_metrics.py:214-232` — restore-after-rollback is dead code; stale `_backup` could overwrite good data; `evaluations` null raises.
- `src/utils/rateLimitParser.js:81,90-100` — "20 requests/min, 50/day" → `rpd=null`, `parseable=true`; unknown providers all-null yet parseable.
- `index.js:18` vs `config/constants.js:503` — `dotenv.config()` runs after `CACHE_TTL` read.

## Low
- `modelSelector.js:250-251` — usage recorded at selection with `length*0.75` estimate; never reconciled.
- `rateLimitTracker.js:96-135` — O(models×events) per request; cleanup every 5 min; `setInterval` not `unref`'d.
- Tests: no end-to-end `selectModel()`, no route/validation tests (no supertest).

## Clean
- No hard-coded secrets in `src/` or `scripts/`; `.env.example` placeholders only.
