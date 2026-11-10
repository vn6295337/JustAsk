# Codebase Audit — 2026-11-02

- Scope: all packages (`justask-registry`, `justask-dashboard`, `justask-router`, `justask/api`, `justask/app`, `.github/workflows`).
- Method: static read-only review by one agent per package. Nothing was executed. Generated outputs and `components/ui` skipped.
- Status column below is updated as items are fixed.

## Reports

| File | Package |
|---|---|
| [registry.md](registry.md) | `justask-registry` + workflows |
| [dashboard.md](dashboard.md) | `justask-dashboard` |
| [router.md](router.md) | `justask-router/selector-service` |
| [api-app.md](api-app.md) | `justask/api`, `justask/app` |

## Cross-package priorities

| # | Topic | Status |
|---|---|---|
| 1 | Anon-key writes: `model_validations`, `analytics_history` (+ `SECURITY DEFINER` RPC), `ims."40_model_selection_score"`, `rate_limits`; possible anon read of registry `secrets` table (unverified) | Fixed in working tree (uncommitted); migrations not applied |
| 2 | Unauthenticated, unmetered endpoints: API `/query`, `/queue/sync` (up to 100 LLM calls/request); router `/rate-limits/reset`, `/cache/refresh` | Fixed in working tree (uncommitted); migrations not applied |
| 3 | Registry deploy path: rollback duplicates rows; delete/insert not atomic; partial Google list accepted; mapping refresh failure silent | Fixed in working tree (uncommitted); migrations not applied |
| 4 | Router scoring: wrong score key, NaN input poisons tracker, NULL provider crashes selection | Fixed in working tree (uncommitted); migrations not applied |
| 5 | App sync: race, retry spend multiplication, failing queries re-billed forever | Fixed in working tree (uncommitted); migrations not applied |

## Decisions recorded

- Router populate scripts (`scripts/db/populate_*.js`) are intentionally manual (human-in-the-loop). They are not to be moved to CI. Plan: read `SUPABASE_SERVICE_KEY` locally.
- Analytics RPC handling: undecided (revoke / harden / revoke + scheduled job).

## Caveats

- Live Supabase RLS and applied migrations were not inspected; findings reflect repo files only.
- Severity is the reviewing agent's judgment.

## Fix status (2026-11-04)

Fixes applied to the working tree by one agent per package. Not committed. No migration applied, no live service called.

Pending manual steps:
- Apply `justask-dashboard/supabase/migrations/20261104000000_harden_analytics_and_validations.sql`.
- Apply `justask-router/selector-service/scripts/db/drop_anon_write_policies.sql`.
- Grant the `pipeline_writer` role INSERT/UPDATE on `analytics_history` and SELECT on `ai_models_main` (analytics snapshot job).
- Set env: `ADMIN_TOKEN`, `CORS_ORIGINS` (router); `API_AUTH_TOKEN` optional (api); `SUPABASE_FUNCTIONS_URL`, `SUPABASE_ANON_KEY` (registry key logging); Supabase env vars on Vercel (dashboard now throws if missing).
- Verify live RLS on `ai_models_main`, `ai_models_discovery`, `secrets`; the unique constraint on `ims."30_rate_limits"`.

Known remaining:
- `tsc` has 5 pre-existing errors in the dashboard; strict mode left off.
- Router `npm test` fails coverage threshold (about 77.7% vs 80%).
- API `router.test.js`: 6 failures that predate the fixes.
- Skipped: encrypted local SQLite, usage reconciliation, action SHA pinning, OpenRouter HF step redesign, registry dedupe/dead-code removal, minimum-count deploy guard.
