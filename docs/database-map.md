# JustAsk Database Map

Supabase project `askme` (`atilxlecbaqcksnrgzav`), Mumbai region. Updated 2026-11-11.

- All JustAsk tables live in schema `justask`.
- Table names start with a digit and contain hyphens, so SQL must quote them: `justask."11_free-models-live"`.
- Name format: `<group number><order>_<group>-<what it holds>`.
- Change history: [database/README.md](../database/README.md).
- Plain-English reference for tables 10, 11 and 20 (timeline, access, fields): [database-tables.md](database-tables.md).

## Data Flow

- Registry pipelines (CI) write `10_free-models-staging`; the registry deploy copies it to `11_free-models-live`.
- Rule: `10` is incoming only (read only by the CI compare and deploy steps); `11` is outgoing only (written only by the deploy step, from `10`). Both have the same columns.
- The deploy step publishes only if the publish gate passes: same columns in `10` and `11`; no drop of more than 20% in a provider's model count (override: workflow input `allow_large_drop`); no empty `inference_provider`, `provider_slug`, `human_readable_name` or `rate_limits`; no duplicate `provider_slug`. Each result is written to the GitHub Actions run summary.
- The dashboard reads `11_free-models-live`.
- The nightly benchmark refresh (CI) writes `20_router-benchmark-scores`.
- The registry deploy writes `22_router-provider-rate-limits` in the same transaction as `11`, then builds `21_router-model-benchmark-map` from `11`.
- The ranking script (manual) reads tables 10, 20, 21 and 22 and writes `23_router-model-ranking`.
- The router serves that ranking to the API through `/best-models`.
- The nightly database job reads `11_free-models-live` and writes `30_analytics-daily-model-counts`, which the dashboard reads.

## 1. Free Models

| Table | Role | Written by | Read by |
|---|---|---|---|
| `10_free-models-staging` | Model list before publishing (incoming only) | Registry refresh step (CI) | Registry compare and deploy steps only |
| `11_free-models-live` | Published model list (outgoing only) | Registry deploy step (CI), copied from `10` | Dashboard, router, ranking script, mapping refresh, nightly analytics job |

## 2. Router

| Table | Role | Written by | Read by |
|---|---|---|---|
| `20_router-benchmark-scores` | Model scores, prices and speed from the Artificial Analysis Free API, one column per Free-tier field | Nightly benchmark refresh (CI) | Router, ranking script, registry mapping |
| `21_router-model-benchmark-map` | Links each model to its Artificial Analysis entry | Registry deploy step (CI) | Router, ranking script |
| `22_router-provider-rate-limits` | Provider rate limits | Registry deploy step (CI), `populate_rate_limits.js` (manual) | Router, ranking script |
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
| `70_external-stock-analysis-cache` | Stock analysis cache for Instant SWOT Agent (`src/utils/analysis_cache.py`). Caching is off since 2026-11-10: the app has no database access and runs without a cache. |

## Who Can Write

| Who | Login | Can write |
|---|---|---|
| Dashboard, router, API | Anon key | Nothing. Read-only on tables 11, 20–23 and 30; no access to 10 (staging). |
| CI pipelines | `pipeline_writer` | Tables 10, 11, 20, 21, 22 |
| Ranking scripts (manual) | Service role key | Tables 22, 23 |
| Nightly analytics job | `postgres` (via `pg_cron`) | Table 30 |

## Old Names

- The pre-2026-11 names (`public.working_version`, `public.ai_models_main`, `ims."10_model_aa_mapping"` and so on) no longer exist. Mapping: [database/applied/2026-11-10_04_justask-schema.sql](../database/applied/2026-11-10_04_justask-schema.sql).

## Supabase-Managed Schemas

- `auth`, `storage`, `realtime`, `cron`, `supabase_migrations` and `vault` belong to Supabase. Do not edit them.
