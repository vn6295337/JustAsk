# JustAsk Database Map

Supabase project `askme` (`atilxlecbaqcksnrgzav`), Mumbai region. Updated 2026-11-10.

- All JustAsk tables live in schema `justask`.
- Table names start with a digit and contain hyphens, so SQL must quote them: `justask."11_free-models-live"`.
- Name format: `<group number><order>_<group>-<what it holds>`.
- Change history: [database/README.md](../database/README.md).

## Data Flow

- Registry pipelines (CI) write `10_free-models-staging`; the registry deploy copies it to `11_free-models-live`.
- The dashboard reads `11_free-models-live`.
- The nightly benchmark refresh (CI) writes `20_router-benchmark-scores`.
- The registry deploy writes `21_router-model-benchmark-map`; the registry refresh writes `22_router-provider-rate-limits`.
- The ranking script (manual) reads tables 10, 20, 21 and 22 and writes `23_router-model-ranking`.
- The router serves that ranking to the API through `/best-models`.
- The nightly database job reads `11_free-models-live` and writes `30_analytics-daily-model-counts`, which the dashboard reads.

## 1. Free Models

| Table | Role | Written by | Read by |
|---|---|---|---|
| `10_free-models-staging` | Model list before publishing | Registry refresh step (CI) | Router, registry compare steps |
| `11_free-models-live` | Published model list | Registry deploy step (CI) | Dashboard, nightly analytics job |

## 2. Router

| Table | Role | Written by | Read by |
|---|---|---|---|
| `20_router-benchmark-scores` | Model quality scores from Artificial Analysis | Nightly benchmark refresh (CI) | Router, ranking script |
| `21_router-model-benchmark-map` | Links each model to its Artificial Analysis entry | Registry deploy step (CI) | Router, ranking script |
| `22_router-provider-rate-limits` | Provider rate limits | Registry refresh step (CI), `populate_rate_limits.js` (manual) | Router, ranking script |
| `23_router-model-ranking` | Final model ranking | `populate_model_selection_score.js` (manual) | Router `/best-models` |

## 3. Analytics

| Table | Role | Written by | Read by |
|---|---|---|---|
| `30_analytics-daily-model-counts` | Daily model-count snapshots | Nightly database job (`pg_cron`) | Dashboard |

## 4. API Key Management (Not in Use Since Sep 2025)

- Data store for the 8 Edge Functions deleted on 2026-11-10.

| Table | Purpose |
|---|---|
| `40_api-keys-status` | Provider key status, expiry and rotation settings |
| `41_api-keys-usage` | Usage counts per key and period |
| `42_api-keys-usage-limits` | Provider usage limits and warning thresholds |
| `43_api-keys-alerts` | Usage, expiry and abuse alerts |
| `44_api-keys-audit-log` | Record of key access and rotation |

## 5. Detailed Catalog (Never Filled In)

| Table | Purpose |
|---|---|
| `50_catalog-providers` | Provider details and API configuration |
| `51_catalog-model-availability` | Which providers serve each model |
| `52_catalog-model-pricing` | Per-provider model pricing |
| `53_catalog-model-quality` | Model quality scores from Artificial Analysis |

## 6. MVP Model Map (Not in Use)

| Table | Purpose |
|---|---|
| `60_mvp-model-benchmark-map` | Text models mapped to Artificial Analysis; `21_router-model-benchmark-map` now does this |

## 7. External App (Not JustAsk)

| Table | Purpose |
|---|---|
| `70_external-stock-analysis-cache` | Stock ticker and company analysis cache for another app, which logs in as `postgres` |

## Who Can Write

| Who | Login | Can write |
|---|---|---|
| Dashboard, router, API | Anon key | Nothing. Read-only on groups 1–3. |
| CI pipelines | `pipeline_writer` | Tables 10, 11, 20, 21, 22 |
| Ranking scripts (manual) | Service role key | Tables 22, 23 |
| Nightly analytics job | `postgres` (via `pg_cron`) | Table 30 |
| External app | `postgres` | Table 70 |

## Compatibility Views (Temporary)

- The old names still work as views: `public.working_version`, `public.ai_models_main`, `ims."10_model_aa_mapping"` and so on.
- Each view points to its new table and applies the caller's own permissions.
- They will be dropped once all code uses the new names. Do not use them in new code.

## Supabase-Managed Schemas

- `auth`, `storage`, `realtime`, `cron`, `supabase_migrations` and `vault` belong to Supabase. Do not edit them.
