# Audit: justask-registry + workflows

Static review, 2026-11-02. `reg` = `justask-registry/src`, `wf` = `.github/workflows`.

## High
- `reg/pipelines/groq/steps/step_08_refresh_working.py:285-292` (same: google step_07:284, openrouter step_20:316; deploy: google step_08:238, groq step_09, openrouter step_21:241) — post-insert rollback only re-INSERTs backup; new rows already committed → duplicate rows in `working_version`/`ai_models_main`.
- `reg/utils/db.py:196-209` + groq step_09:213-217, step_08:220 — DELETE commits before INSERT; interruption leaves provider with zero rows; backup only in memory.
- `reg/pipelines/google/steps/step_01_fetch.py:168-186,214-216` — non-200/JSON error on page N `break`s and returns partial list as success; deploy checks only `staging_count > 0`; 5% tolerance compares to new set. Missing models later deleted.
- `wf/registry-{groq,google,openrouter}-deploy.yml:~58-66` — `refresh_model_aa_mapping()` return value ignored; green on failure.
- `wf/registry-*-deploy.yml:~61` — direct `psycopg2.connect()` skips IPv4 `hostaddr` workaround; silent failure on IPv6-only runner.
- `reg/utils/key_client.py:15,164-167` — anon JWT + project URL hardcoded; `__main__` prints first 20 chars of API key. `reg/utils/env_manager.py:103`, openrouter `step_01_fetch.py:87` read provider keys from `secrets` table via anon key — exposed if RLS permits anon read (unverified).

## Medium
- `reg/utils/model_aa_mapping.py:~655-662` — continues and deletes mappings if backup returns None; rollback gated on truthy backup.
- `reg/utils/output.py:15-25`, `reg/main.py:96-107`, `reg/pipelines/base.py:36` — module-global current pipeline; `all --parallel` last constructor wins; can wipe another pipeline's `outputs/`.
- `wf/registry-*-pipeline.yml` "Commit outputs" — no concurrency group, `git push` without pull/rebase; overlapping runs fail and skip chained workflow.
- `reg/utils/db.py:296-311` — rate-limit upsert `ON CONFLICT (human_readable_name)` without provider (constraint unchecked).
- Refresh scripts (groq step_08:~255-282, google step_07, openrouter step_20) — rate limits written after `working_version` commit; `delete_rate_limits` commits separately; upsert failure only warns; `ims.30_rate_limits` can be left empty.
- `reg/utils/rate_limit_parser.py:116-130,163-169` — "20 requests/min, 50/day" → `rpd=None`, `parseable=True`; fallback overwrites parsed fields and invents limits (groq rpm 30, tpm 15000).
- `reg/pipelines/base.py:61-75` — `--steps` malformed raises, reversed range → empty list → "success".
- `reg/main.py:176-190` — `all` ignores `--no-clean`.
- `openrouter step_01_fetch.py:197-206` vs google/groq step_01 — three different fetch-failure contracts (root cause of partial-list bug).
- `wf/registry-openrouter-pipeline.yml` — on pipeline failure, commit skipped; committed `outputs/` stale; deploy steps read stale files.
- `google step_06_compare_supabase.py:~242-250` vs `:~66-90` (copied: groq step_07, openrouter step_19) — NULL handling inconsistent; `load_supabase_data` swallows exceptions → all models reported new.

## Low
- `google step_06:63-66`, `groq step_07:67-70` — print first 20 chars of `PIPELINE_SUPABASE_URL` (project ref/role) to CI logs and committed outputs.
- `wf/registry-*-pipeline.yml:~22-23` — actions pinned to tags, not SHAs; `contents: write` + secrets; deploy workflows lack `permissions`.
- `reg/utils/db.py:213-221,233-237` — table/column names f-string interpolated; missing key → `KeyError`.
- openrouter `step_05_fetch_hf_license_urls.py:43`, `step_06…:69` — per-model requests, no reuse; can exceed 15-min cap; HEAD treats 3xx/403 as inaccessible.
- `reg/pipelines/base.py:96-110` — output printed only after exit; hard 15-min timeout.
- Dead code: `groq_web_scraper.py`, `groq_data_processor.py`, `path_manager.py`, `config_manager.py`, `env_manager.py` (interactive `input()`); keeps selenium in requirements.
- Deploy/refresh scripts and 3 runners are near-identical copies that already drifted; docstrings reference `*_v3` tables; openrouter legacy letter map doesn't cover 21 steps.
