# Database Changes

Record of changes applied to the Supabase project `askme` (`atilxlecbaqcksnrgzav`).

- **Table map:** [docs/database-map.md](../docs/database-map.md)
- **Applied SQL:** `applied/`, in the order applied
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

## Not SQL

- Deleted all 8 Edge Functions (`get-api-key` gave provider keys to anyone with the public anon key). Backup: `~/backups/supabase-askme-edge-functions-20261110/` on the owner's machine.
- Deleted the `GEMINI_API_KEY`, `GROQ_API_KEY` and `OPENROUTER_API_KEY` Edge Function secrets. The provider keys were rotated.
- New random password for `pipeline_writer`, stored only in the GitHub secret `PIPELINE_SUPABASE_URL`.
- API setting: exposed schemas are `public, justask` (since 2026-11-11).
