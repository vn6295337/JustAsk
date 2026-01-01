# Operations Guide

**Last Updated:** 2025-12-30
**Purpose:** Table ownership, maintenance procedures, and troubleshooting

---

## Table Ownership

### Summary

| Table | Owner | Update Frequency |
|-------|-------|------------------|
| `public.working_version` | justask-registry pipeline | Daily |
| `ims.10_model_aa_mapping` | justask-registry pipeline | Daily (after working_version) |
| `ims.20_aa_performance_metrics` | selector-service scripts | Weekly |
| `ims.30_rate_limits` | selector-service scripts | As needed |

### public.working_version

**Owner:** justask-registry pipeline
**Access:** READ-ONLY (selector service never modifies)

The pipeline populates this table daily with discovered models from:
- Google AI (Gemini, Gemma)
- Groq Cloud
- OpenRouter

### ims.10_model_aa_mapping

**Owner:** justask-registry pipeline
**Authoritative Script:** `justask-registry/model_aa_mapping_utils.py`

Maps `working_version.provider_slug` → `ims.20_aa_performance_metrics.aa_slug`

**Normalization Rules:**
- Periods → hyphens (`gemini-2.5-flash` → `gemini-2-5-flash`)
- Suffixes stripped (`-instruct`, `-chat`, `-it`, `-turbo`)
- Lowercase

### ims.20_aa_performance_metrics

**Owner:** selector-service
**Script:** `selector-service/scripts/db/refresh_aa_performance_metrics.py`

Caches Intelligence Index data from Artificial Analysis API.

### ims.30_rate_limits

**Owner:** selector-service
**Script:** `selector-service/scripts/db/populate_rate_limits.js`

Normalized rate limits parsed from `working_version.rate_limits` text field.

---

## Maintenance Procedures

### When Pipeline Updates working_version

**Automatic flow:**
1. Pipeline inserts/updates working_version (daily)
2. Pipeline runs model_aa_mapping refresh
3. Selector service picks up changes on next cache refresh (24 hours)

**No manual action required.**

### Refreshing AA Performance Metrics

```bash
cd selector-service
npm run db:populate:scores
```

Run weekly or when Artificial Analysis adds new models.

### Refreshing Rate Limits

```bash
cd selector-service
npm run db:populate:rate-limits
```

Run when rate limit formats change or new providers added.

### Force Cache Refresh

```bash
curl -X POST http://localhost:3001/cache/refresh
```

Use when you need immediate pickup of database changes.

---

## Monitoring

### Health Check

```bash
curl http://localhost:3001/health
```

**Key indicators:**
- `status: "ok"` - Service healthy
- `cache.entries[].expired: false` - Cache valid
- `rateLimits.*.headroom.overall` - Capacity available

### Log Levels

| Level | Use Case |
|-------|----------|
| `error` | Production (errors only) |
| `warn` | Production (+ warnings) |
| `info` | Staging (+ info messages) |
| `debug` | Development (verbose) |

Set via `LOG_LEVEL` environment variable.

### Key Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Selection latency (cached) | < 100ms | > 500ms |
| Cache hit rate | > 95% | < 80% |
| Rate limit headroom | > 30% | < 10% |
| Models with AA mapping | > 40% | < 20% |

---

## Troubleshooting

### No Models Returned

**Symptom:** `/select-model` returns empty or error

**Check:**
1. Database connection: `curl http://localhost:3001/health`
2. Cache populated: Check `cache.entries` in health response
3. Modality filter: Try `modalities: ["text"]` only
4. RLS policies: Ensure public SELECT allowed

**Fix:**
```bash
curl -X POST http://localhost:3001/cache/refresh
```

### Models Missing Intelligence Index

**Symptom:** `/best-model` returns 404

**Cause:** Models not mapped to AA slugs

**Check:**
```bash
npm run debug:find-unmapped
```

**Fix:** Run pipeline refresh or add manual mappings

### Rate Limit Tracking Incorrect

**Symptom:** Headroom shows 100% but requests failing

**Cause:** In-memory counters reset on service restart

**Check:**
```bash
npm run debug:check-metrics
```

**Fix:** Rate limits are approximate; consider Redis for production persistence

### Slow Selection Times

**Symptom:** Selection > 100ms

**Check:**
1. Cache status (expired = DB query each time)
2. Network latency to Supabase
3. Log level (debug adds overhead)

**Fix:**
- Ensure cache TTL appropriate (24 hours default)
- Deploy closer to Supabase region
- Set `LOG_LEVEL=warn` in production

---

## Scripts Reference

### Database Population

| Script | Command | Purpose |
|--------|---------|---------|
| `populate_rate_limits.js` | `npm run db:populate:rate-limits` | Parse rate limits |
| `populate_model_selection_score.js` | `npm run db:populate:scores` | Build selection scores |
| `refresh_aa_performance_metrics.py` | `python scripts/db/refresh_aa_performance_metrics.py` | Fetch AA API data |

### Debugging

| Script | Command | Purpose |
|--------|---------|---------|
| `check_aa_metrics_table.js` | `npm run debug:check-metrics` | Inspect metrics table |
| `debug_aa_mapping.js` | `npm run debug:mapping` | Diagnose mapping issues |
| `find_models_with_aa_metrics.js` | `npm run debug:find-with-metrics` | List models by coverage |
| `find_unmapped_models.js` | `npm run debug:find-unmapped` | Find gaps |

### Validation

| Script | Command | Purpose |
|--------|---------|---------|
| `validate_scoring.js` | `npm run validate:scoring` | End-to-end validation |
| `test_aa_api.js` | `npm run validate:api` | Test AA API connectivity |

---

## Incident Response

### Service Down

1. Check Render dashboard for deployment status
2. Review logs for startup errors
3. Verify environment variables set
4. Check Supabase status page

### Database Connection Failed

1. Verify `SUPABASE_URL` and `SUPABASE_KEY`
2. Check Supabase project status
3. Test connection: `curl $SUPABASE_URL/rest/v1/`
4. Review RLS policies

### Rate Limits Exhausted

1. Check `/health` for headroom status
2. Wait for window reset (60s for RPM, 24h for RPD)
3. Consider load balancing across providers
4. Reset counters for testing: `POST /rate-limits/reset`

---

**Document Owner:** Development Team
