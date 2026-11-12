# Database Changes

Record of changes applied to the Supabase project `askme` (`atilxlecbaqcksnrgzav`).

- **Table map:** [docs/database-map.md](../docs/database-map.md)
- **Applied SQL:** `applied/`, in the order applied
- **Pending SQL:** `pending/`, written but not yet applied; move to `applied/` when applied
- **How applied:** Supabase Management API, as the `postgres` role

## 2026-11-10

| File | Change |
|---|---|
| `applied/2026-11-10_01_remove-public-write-access.sql` | Public roles (`anon`, `authenticated`) lose all write access; read-only on the 7 active tables |
| `applied/2026-11-10_02_pipeline-writer-grants.sql` | `pipeline_writer` can write the two router tables it lacked, so CI no longer needs `postgres` |
| `applied/2026-11-10_03_lock-analytics-functions.sql` | Only the nightly job can run the analytics functions; their `search_path` is pinned |
| `applied/2026-11-10_04_justask-schema.sql` | All 18 tables move to schema `justask` with numbered names; old names stay as compatibility views |
| `applied/2026-11-10_05_analytics-functions-new-names.sql` | Analytics functions use the new table names |
| `applied/2026-11-10_06_drop-asa-view.sql` | Instant SWOT Agent cache left off; `asa.analysis_cache` view and `asa` schema dropped |

## 2026-11-11

| File | Change |
|---|---|
| `applied/2026-11-11_07_drop-compatibility-views.sql` | Remaining 17 compatibility views and the empty `ims` schema dropped; API exposes `public, justask` |
| `applied/2026-11-11_08_live-provider-slug.sql` | `11_free-models-live` gets `provider_slug`, backfilled from `10`; the two tables now have the same columns |
| `applied/2026-11-11_10_benchmark-scores-add-aa-fields.sql` | `20_router-benchmark-scores` gets the 16 Artificial Analysis Free API fields it lacked (capability indexes, index version, creator id, index cost, cache prices, `performance_v3` speed, agentic index) |

## 2026-11-12

| File | Change |
|---|---|
| `applied/2026-11-11_11_benchmark-scores-drop-old-fields.sql` | `20_router-benchmark-scores` drops the 18 columns the Artificial Analysis Free API cannot fill (Pro-only or retired benchmarks, creator slug, blended price, old median speed). All were empty |
| `applied/2026-11-11_09_staging-private.sql` | Public roles (`anon`, `authenticated`) lose read access to `10_free-models-staging`; only CI (`pipeline_writer`) and `service_role` can read it |
| `applied/2026-11-12_12_staging-table-tidy.sql` | `10_free-models-staging`: current table description; index, primary key and sequence names changed from `working_version_duplicate_duplicate_*` to `free_models_staging_*`; no-op `pipeline_writer` policy dropped (that role bypasses RLS; grants control access) |
| `applied/2026-11-12_13_live-table-tidy.sql` | `11_free-models-live`: current description; names changed from `ai_models_main_working_version_*` to `free_models_live_*`; no-op `pipeline_writer` policy dropped; `authenticated` read permission removed; `provider_slug` and `rate_limits` required and `(inference_provider, provider_slug)` unique |
| `applied/2026-11-12_14_benchmark-table-tidy.sql` | `20_router-benchmark-scores`: current description; names changed from `aa_performance_metrics_*` / `idx_aa_metrics_*` to `router_benchmark_scores_*` (keys, index, trigger); no-op `service_role` policy dropped; `authenticated` read permission removed; duplicate index on `aa_slug` dropped |
| `applied/2026-11-12_15_benchmark-map-tidy.sql` | `21_router-model-benchmark-map`: current description; names changed from `model_aa_mapping_*` / `unique_provider_model` / `idx_*` to `router_model_benchmark_map_*` (keys, indexes, sequence); `authenticated` read permission removed |
| `applied/2026-11-12_16_benchmark-map-timestamptz.sql` | `21_router-model-benchmark-map`: `created_at` and `updated_at` become `timestamptz` (existing values read as UTC); the mapping refresh now writes time-zone-aware times |
| `applied/2026-11-12_17_timestamptz-22-23-pin-analytics-utc.sql` | Tables 22 and 23: `created_at`/`updated_at` become `timestamptz` (read as UTC); analytics functions pinned to UTC so the nightly snapshot keeps counting by UTC day |
| `applied/2026-11-12_18_database-timezone-ist.sql` | Database default time zone set to `Asia/Kolkata`: times are shown in IST (`+05:30`). Stored values unchanged; schedules (GitHub Actions, `pg_cron`) stay in UTC |

## Not SQL

- Deleted all 8 Edge Functions (`get-api-key` gave provider keys to anyone with the public anon key). Backup: `~/backups/supabase-askme-edge-functions-20261110/` on the owner's machine.
- Deleted the `GEMINI_API_KEY`, `GROQ_API_KEY` and `OPENROUTER_API_KEY` Edge Function secrets. The provider keys were rotated.
- New random password for `pipeline_writer`, stored only in the GitHub secret `PIPELINE_SUPABASE_URL`.
- API setting: exposed schemas are `public, justask` (since 2026-11-11).
