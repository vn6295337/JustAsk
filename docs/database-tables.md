# JustAsk Database Tables

Plain-English reference for the main tables in schema `justask` (Supabase project `askme`). Updated 2026-11-12.

- Overview of all tables and how data flows between them: [database-map.md](database-map.md).
- Each table below has: what it does, what happens to it in order, who can access it, and its fields.
- "Login" is the database role that does the work. `anon` is the public key used by the dashboard and router.

---

## `10_free-models-staging`: Free models, draft list

### What it does
- Holds the newest list of free AI models from each provider (Google, Groq, OpenRouter), before it goes live.
- It is the inbox: data comes in here, is checked, and only then is published to `11_free-models-live`.
- Each row is one model at one provider.

### What happens to it, in order

```
┌─────┬────────────────────┬───────────┬──────────────────────────────────────┬──────────────────────────────────────┐
│ #   │ When               │ Action    │ What happens to the table            │ Done by                              │
├─────┼────────────────────┼───────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ 1   │ • Daily, 00:00 UTC │ Written   │ • The provider's rows are replaced   │ • Daily pipeline                     │
│     │ • Google first,    │           │   with the list fetched that day     │   registry-<provider>-pipeline.yml   │
│     │   then Groq, then  │           │ • All at once (all or nothing)       │ • Google step 6, Groq step 7,        │
│     │   OpenRouter       │           │                                      │   OpenRouter step 19 (refresh draft) │
│     │                    │           │                                      │ • Login pipeline_writer              │
├─────┼────────────────────┼───────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ 2   │ • Straight after 1 │ Read      │ • The draft is compared with the     │ • Same daily pipeline                │
│     │                    │           │   live list (table 11)               │ • Google step 7, Groq step 8,        │
│     │                    │           │ • A report lists the models          │   OpenRouter step 20 (compare draft  │
│     │                    │           │   publishing would add, remove or    │   with live)                         │
│     │                    │           │   change                             │ • Login pipeline_writer              │
├─────┼────────────────────┼───────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ 3   │ • When you choose  │ Read      │ • The draft is checked: same columns │ • Deploy workflow                    │
│     │   to publish       │           │   as 11, no big drop in model count, │   registry-<provider>-deploy.yml     │
│     │                    │           │   required fields filled, no         │ • Google step 8, Groq step 9,        │
│     │                    │           │   duplicates                         │   OpenRouter step 21 (publish)       │
│     │                    │           │ • If it passes, it is copied to      │ • Login pipeline_writer              │
│     │                    │           │   table 11                           │                                      │
│     │                    │           │ • If it fails, nothing is published  │                                      │
│     │                    │           │   and the reason is logged           │                                      │
└─────┴────────────────────┴───────────┴──────────────────────────────────────┴──────────────────────────────────────┘
```

- Never read by the dashboard, the API or the router. The public `anon` key has no access.

### Who can access it

| Who | Login | Access |
|---|---|---|
| CI pipelines | `pipeline_writer` | Read and write |
| Admin scripts | `service_role` | Read and write (none use it today) |
| Dashboard, API, router | `anon` (public key) | None |

### Fields

| Field | Plain meaning | Required | Example |
|---|---|---|---|
| `id` | Row number, assigned by the database | Yes | 4462 |
| `inference_provider` | Company that runs the model and serves the free API | Yes | Google |
| `model_provider` | Company that made the model | Yes | Google |
| `human_readable_name` | Display name | Yes | Gemini 2.5 Flash |
| `provider_slug` | Short ID the provider uses for the model | Yes (checked when publishing) | gemini-2.5-flash |
| `model_provider_country` | Home country of the company that made the model | No | United States |
| `official_url` | The model's official web page | No | https://deepmind.google/models/gemini/ |
| `input_modalities` | What the model accepts | No | Text, Image, Audio, Video |
| `output_modalities` | What the model produces | No | Text |
| `license_name` | Name of the licence | No | GEMINI |
| `license_url` | Link to the licence | No | https://ai.google.dev/gemini-api/terms |
| `license_info_text` | Who issues the licence or terms | No | Google |
| `license_info_url` | Link to the terms of use | No | https://developers.google.com/terms |
| `rate_limits` | Free-tier limits, as the provider writes them | Yes (checked when publishing) | 10 requests/min, 250K tokens/min, 250 requests/day |
| `provider_api_access` | Where to get an API key | No | https://aistudio.google.com/apikey |
| `created_at` | When the row was written | Automatic | 2026-11-10 16:01 UTC |
| `updated_at` | When the row was last changed | Automatic | 2026-11-10 16:01 UTC |

### Rules
- Has exactly the same columns as `11_free-models-live`. The publish check blocks any mismatch.
- Rows are replaced one provider at a time, never edited one row at a time.

---

## `11_free-models-live`: Free models, published list

### What it does
- Holds the published list of free AI models: the list everything else uses.
- It is the outbox: it changes only when you publish a provider's draft from `10_free-models-staging`.
- Each row is one model at one provider.

### What happens to it, in order

```
┌─────┬────────────────────┬───────────┬──────────────────────────────────────┬──────────────────────────────────────┐
│ #   │ When               │ Action    │ What happens to the table            │ Done by                              │
├─────┼────────────────────┼───────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ 1   │ • When you choose  │ Written   │ • The provider's rows are replaced   │ • Deploy workflow                    │
│     │   to publish       │           │   with the checked draft from table  │   registry-<provider>-deploy.yml     │
│     │                    │           │   10                                 │ • Google step 8, Groq step 9,        │
│     │                    │           │ • Rate limits (table 22) are         │   OpenRouter step 21 (publish)       │
│     │                    │           │   replaced in the same transaction   │ • Login pipeline_writer              │
│     │                    │           │ • All or nothing                     │                                      │
├─────┼────────────────────┼───────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ 2   │ • Straight after 1 │ Read      │ • The provider's models are linked   │ • Same deploy workflow, AA mapping   │
│     │                    │           │   to their Artificial Analysis       │   refresh                            │
│     │                    │           │   entries                            │ • Script model_aa_mapping.py         │
│     │                    │           │ • The links are written to table 21  │ • Login pipeline_writer              │
├─────┼────────────────────┼───────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ 3   │ • Daily, after the │ Read      │ • Compared with the draft (table 10) │ • Daily pipeline                     │
│     │   draft refresh    │           │ • A report lists what publishing     │   registry-<provider>-pipeline.yml   │
│     │                    │           │   would change                       │ • Google step 7, Groq step 8,        │
│     │                    │           │                                      │   OpenRouter step 20 (compare draft  │
│     │                    │           │                                      │   with live)                         │
│     │                    │           │                                      │ • Login pipeline_writer              │
├─────┼────────────────────┼───────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ 4   │ • Daily, 23:59 UTC │ Read      │ • Models are counted, in total and   │ • Database job                       │
│     │                    │           │   per provider                       │   daily-analytics-collection         │
│     │                    │           │ • The counts are saved as one row in │   (pg_cron)                          │
│     │                    │           │   table 30                           │ • Function                           │
│     │                    │           │                                      │   public.collect_daily_analytics()   │
│     │                    │           │                                      │ • Login postgres                     │
├─────┼────────────────────┼───────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ 5   │ • Each time a      │ Read      │ • The model list is shown in the     │ • Dashboard pages                    │
│     │   dashboard page   │           │   dashboard                          │   AiModelsVisualization.tsx and      │
│     │   loads            │           │                                      │   Analytics.tsx                      │
│     │                    │           │                                      │ • Public key (anon)                  │
├─────┼────────────────────┼───────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ 6   │ • When the         │ Read      │ • Used to pick a model for each      │ • Router on Render (justask-router)  │
│     │   router's cache   │           │   question, together with tables 20, │ • Script supabase.js                 │
│     │   expires (every   │           │   21 and 22                          │ • Public key (anon)                  │
│     │   30 minutes)      │           │                                      │                                      │
├─────┼────────────────────┼───────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ 7   │ • When you run the │ Read      │ • Used to compute the model ranking, │ • Script                             │
│     │   ranking script   │           │   saved to table 23                  │   populate_model_selection_score.js  │
│     │   by hand          │           │                                      │ • Login service_role                 │
└─────┴────────────────────┴───────────┴──────────────────────────────────────┴──────────────────────────────────────┘
```

### Who can access it

| Who | Login | Access |
|---|---|---|
| CI pipelines | `pipeline_writer` | Read and write (write only by the publish step) |
| Ranking script, admin scripts | `service_role` | Read and write (reads only) |
| Nightly analytics job | `postgres` | Read |
| Dashboard, API, router | `anon` (public key) | Read |

### Fields

Same fields as `10_free-models-staging`; a published row is a copy of its draft row.

| Field | Plain meaning | Required | Example |
|---|---|---|---|
| `id` | Row number, assigned by the database | Yes | 2842 |
| `inference_provider` | Company that runs the model and serves the free API | Yes | Google |
| `model_provider` | Company that made the model | Yes | Google |
| `human_readable_name` | Display name | Yes | Gemini 2.5 Flash |
| `provider_slug` | Short ID the provider uses for the model | Yes (checked when publishing) | gemini-2.5-flash |
| `model_provider_country` | Home country of the company that made the model | No | United States |
| `official_url` | The model's official web page | No | https://deepmind.google/models/gemini/ |
| `input_modalities` | What the model accepts | No | Text, Image, Audio, Video |
| `output_modalities` | What the model produces | No | Text |
| `license_name` | Name of the licence | No | GEMINI |
| `license_url` | Link to the licence | No | https://ai.google.dev/gemini-api/terms |
| `license_info_text` | Who issues the licence or terms | No | Google |
| `license_info_url` | Link to the terms of use | No | https://developers.google.com/terms |
| `rate_limits` | Free-tier limits, as the provider writes them | Yes (checked when publishing) | 10 requests/min, 250K tokens/min, 250 requests/day |
| `provider_api_access` | Where to get an API key | No | https://aistudio.google.com/apikey |
| `created_at` | When the row was written | Automatic | 2026-11-10 16:01 UTC |
| `updated_at` | When the row was last changed | Automatic | 2026-11-10 16:01 UTC |

### Rules
- Written only by the publish step, and only after the publish check passes.
- Has exactly the same columns as `10_free-models-staging`.

---

## `20_router-benchmark-scores`: Model quality scores from Artificial Analysis

### What it does
- Holds quality scores, prices and speed for AI models, from Artificial Analysis (AA), an independent benchmarking site.
- One column per field of AA's free API (`/api/v2/language/models/free`).
- Gives the router and the ranking its measure of how good a model is.

### What happens to it, in order

```
┌─────┬────────────────────┬───────────┬──────────────────────────────────────┬──────────────────────────────────────┐
│ #   │ When               │ Action    │ What happens to the table            │ Done by                              │
├─────┼────────────────────┼───────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ 1   │ • Daily, 00:00 UTC │ Written   │ • Artificial Analysis's free model   │ • Workflow                           │
│     │   (GitHub often    │           │   list is fetched (about 735 models) │   refresh-aa-performance-metrics.yml │
│     │   starts it hours  │           │ • Models without an intelligence     │ • Script                             │
│     │   late)            │           │   score are skipped (about 120 kept) │   refresh_aa_performance_metrics.py  │
│     │                    │           │ • All rows are replaced at once (all │ • Login pipeline_writer              │
│     │                    │           │   or nothing)                        │                                      │
│     │                    │           │ • Refused if fewer than 50 models,   │                                      │
│     │                    │           │   or less than half of the current   │                                      │
│     │                    │           │   count                              │                                      │
├─────┼────────────────────┼───────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ 2   │ • When you choose  │ Read      │ • The list of AA model slugs is used │ • Deploy workflow                    │
│     │   to publish a     │           │   to link our models to AA entries   │   registry-<provider>-deploy.yml, AA │
│     │   provider         │           │   (table 21)                         │   mapping refresh                    │
│     │                    │           │                                      │ • Script model_aa_mapping.py         │
│     │                    │           │                                      │ • Login pipeline_writer              │
├─────┼────────────────────┼───────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ 3   │ • When the         │ Read      │ • Intelligence scores are used to    │ • Router on Render (justask-router)  │
│     │   router's cache   │           │   pick a model for each question     │ • Script supabase.js                 │
│     │   expires (every   │           │                                      │ • Public key (anon)                  │
│     │   30 minutes)      │           │                                      │                                      │
├─────┼────────────────────┼───────────┼──────────────────────────────────────┼──────────────────────────────────────┤
│ 4   │ • When you run the │ Read      │ • Intelligence scores are used to    │ • Script                             │
│     │   ranking script   │           │   compute the model ranking (table   │   populate_model_selection_score.js  │
│     │   by hand          │           │   23)                                │ • Login service_role                 │
└─────┴────────────────────┴───────────┴──────────────────────────────────────┴──────────────────────────────────────┘
```

### Who can access it

| Who | Login | Access |
|---|---|---|
| Benchmark refresh, registry mapping | `pipeline_writer` | Read, insert, delete |
| Ranking script, admin scripts | `service_role` | Read and write (reads only) |
| Dashboard, API, router | `anon` (public key) | Read |

### Fields

| Field | Plain meaning | AA API field | Example |
|---|---|---|---|
| `id` | Row ID, assigned by the database | (ours) | 52871534-… |
| `aa_model_id` | AA's permanent ID for the model | `id` | d366dfa1-d940-4788-aa73-d298c45699b3 |
| `aa_slug` | AA's short text ID for the model | `slug` | gemini-4-argon |
| `name` | Model name, as AA shows it | `name` | Gemini 4 Argon (High) |
| `release_date` | Release date | `release_date` | 2026-09-30 |
| `creator_id` | AA's ID for the company that made the model | `model_creator.id` | faddc6d9-2c14-445f-9b28-56726f59c793 |
| `creator_name` | Company that made the model | `model_creator.name` | Google |
| `intelligence_index_version` | Version of AA's intelligence score; compare scores only within one version | `intelligence_index_version` | 5 |
| `intelligence_index` | Overall intelligence score | `evaluations.artificial_analysis_intelligence_index` | 50.4 |
| `coding_index` | Coding score; AA no longer publishes it, always empty | `evaluations.artificial_analysis_coding_index` | (empty) |
| `agentic_index` | Agentic score; AA no longer publishes it, always empty | `evaluations.artificial_analysis_agentic_index` | (empty) |
| `finance_and_accounting_index` | Finance and accounting score | `evaluations.artificial_analysis_finance_and_accounting_index` | 55.9 |
| `strategy_and_ops_index` | Strategy and operations score | `evaluations.artificial_analysis_strategy_and_ops_index` | 57.2 |
| `legal_index` | Legal score | `evaluations.artificial_analysis_legal_index` | 54.6 |
| `healthcare_and_medical_index` | Healthcare and medical score | `evaluations.artificial_analysis_healthcare_and_medical_index` | 51.3 |
| `engineering_index` | Engineering score | `evaluations.artificial_analysis_engineering_index` | 57.3 |
| `economics_index` | Economics score | `evaluations.artificial_analysis_economics_index` | 52.6 |
| `intelligence_index_cost_total` | What AA spent running its tests on the model (USD) | `artificial_analysis_intelligence_index_cost.total_cost` | 7620.22 |
| `intelligence_index_cost_per_task` | Same, per test task (USD) | `artificial_analysis_intelligence_index_cost.cost_per_task.total_cost` | 9.9466 |
| `price_1m_input_tokens` | Paid price per 1M input tokens (USD) | `pricing.price_1m_input_tokens` | 4.00 |
| `price_1m_output_tokens` | Paid price per 1M output tokens (USD) | `pricing.price_1m_output_tokens` | 20.00 |
| `price_1m_cache_hit_tokens` | Paid price per 1M cached input tokens (USD) | `pricing.price_1m_cache_hit_tokens` | 0.20 |
| `price_1m_cache_write_tokens` | Paid price per 1M cache-write tokens (USD) | `pricing.price_1m_cache_write_tokens` | (empty) |
| `mean_output_tokens_per_second` | Output speed, averaged over the last 5 days | `performance_v3.mean_output_tokens_per_second` | 65.33 |
| `mean_time_to_first_token_seconds` | Wait until the first token (seconds) | `performance_v3.mean_time_to_first_token_seconds` | 37.44 |
| `mean_time_to_first_answer_token_seconds` | Wait until the first answer token, after any thinking (seconds) | `performance_v3.mean_time_to_first_answer_token_seconds` | 37.44 |
| `created_at` | When the row was written | (ours) | 2026-11-12 02:15 UTC |
| `updated_at` | When the row was last changed | (ours) | 2026-11-12 02:15 UTC |

### Rules
- Only models that have an intelligence score are kept.
- The whole table is replaced on each refresh; rows are never edited one at a time.
- Empty means AA has no value for that model; it never means zero.
- `aa_slug` and `aa_model_id` are unique.

---

## Where the scripts are

| Name used above | Full path |
|---|---|
| `registry-<provider>-pipeline.yml`, `registry-<provider>-deploy.yml`, `refresh-aa-performance-metrics.yml` | `.github/workflows/` |
| Refresh draft, compare, publish steps | `justask-registry/src/pipelines/<provider>/steps/` (step number in the file name, e.g. `step_06_refresh_working.py`) |
| `model_aa_mapping.py` | `justask-registry/src/utils/model_aa_mapping.py` |
| `refresh_aa_performance_metrics.py` | `justask-router/selector-service/scripts/db/refresh_aa_performance_metrics.py` |
| `populate_model_selection_score.js` | `justask-router/selector-service/scripts/db/populate_model_selection_score.js` |
| `supabase.js` (router) | `justask-router/selector-service/src/utils/supabase.js` |
| `AiModelsVisualization.tsx`, `Analytics.tsx` | `justask-dashboard/src/components/`, `justask-dashboard/src/pages/` |
| `public.collect_daily_analytics()` | Database function; scheduled by `pg_cron` job `daily-analytics-collection` |
