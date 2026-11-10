# Audit: justask-dashboard

Static review, 2026-11-02. Paths relative to `justask-dashboard/`.

## High
- `supabase/migrations/20250719…sql:19-23` — `model_validations` has `FOR ALL USING (true)`; anon key can insert/update/delete. Table is unused by any code.
- `supabase/migrations/20250902000000_create_analytics_history.sql:21-65` — public insert policy + `SECURITY DEFINER` RPC `insert_analytics_snapshot` with no `search_path`, auth, or validation.
- `src/components/ModelCountLineGraph.tsx:117-190` — every visitor's browser computes and writes the snapshot; writes scale with traffic; filtered/stale views overwrite the canonical row.
- `supabase/migrations/20250902…:41-50` (and `20251104…`) — one-row-per-day is select-then-insert, no unique constraint; `DATE()`/`CURRENT_DATE` are session-TZ, not UTC. Concurrent first visitors duplicate rows.

## Medium
- `AiModelsVisualization.tsx:695,710` — `license_info_url`/`license_url` rendered to `href` without scheme check (`javascript:` risk if data poisoned).
- `ModelsSSoT.tsx:212-216,303` — `sortBy` cast from URL unvalidated; `?sort=x` throws, white-screen, no error boundary.
- `ModelsSSoT.tsx:300-305` — sorts memoized array in place; `quickViews` dep changes every render so memo never caches.
- `AiModelsVisualization.tsx:268-274,394`, `pages/Analytics.tsx:57-59,154` — one failed 5-min refresh sets `error` forever and replaces the UI.
- `ModelsSSoT.tsx:321-327` — CSV export: no quote escaping, no formula-injection neutralization.
- `ModelsSSoT.tsx:107-166` — CSV parser splits on `,`; quoted commas shift columns; unchecked cast then `.toLowerCase()` throws.
- `ModelCountLineGraph.tsx:66-112` — JSONB provider counts cast to `any`; null/malformed throws in `useMemo`.
- `ModelCountLineGraph.tsx:62-112,136-190` — no cancellation/ordering; stale responses overwrite newer; set state after unmount.
- `ModelsSSoT.tsx:276-277,316-317` — "Recently Updated" matches `'2024'`/`'2025'`; 2026 excluded.
- `ModelsSSoT.tsx:68-97` — empty table sets permanent error, no refresh.
- `pages/Analytics.tsx:293` vs `AiModelsVisualization.tsx:521` — Analytics passes unfiltered models to snapshot writer; dashboard excludes Dolphin models. Counts disagree.

## Low
- `integrations/supabase/client.ts:6-14` — hardcoded URL/anon-key fallbacks hide missing env; `:20-23` pointless `no-cache` header (forces preflight) and `persistSession`.
- `key={index}` on filtered/sorted lists: `AiModelsVisualization.tsx:661`, `ModelsSSoT.tsx:615,677`.
- `AiModelsVisualization.tsx:178-220` — filters recomputed every render; case-sensitive string sort.
- `console.log` of full Supabase responses every 5 min: `AiModelsVisualization.tsx:48-70`, `Analytics.tsx:25-45`.
- `ModelCountLineGraph.tsx:59,70-90` — history load error only logged; looks like "no data".
- `tsconfig.json:12-17`, `tsconfig.app.json:18-21` — `strict`, `strictNullChecks`, `noImplicitAny` off; root cause of several crashes.
- `fonts.ready` workaround duplicated in 3 files; can set state after unmount.
- `/banner-text.txt` polled every 30 s by three components, no abort.
- `test.txt` (repo root) contains "PAT configured" / "secret test"; no secret value found; audit any related CI token (unverified).

## Not verified
- Live RLS on `ai_models_main`, `ai_models_discovery`.
