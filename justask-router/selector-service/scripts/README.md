# Selector Service Scripts

Helper scripts for database population, debugging, and validation.

## Database Population

Run after schema changes or to refresh data.

| Script | Command | Description |
|--------|---------|-------------|
| `populate_rate_limits.js` | `npm run db:populate:rate-limits` | Parse rate limits from `working_version` → `ims.30_rate_limits` |
| `populate_model_selection_score.js` | `npm run db:populate:scores` | Build consolidated scores in `ims.40_model_selection_score` |

## Debug/Diagnostic

Safe to run anytime. Read-only inspection scripts.

| Script | Command | Description |
|--------|---------|-------------|
| `check_aa_metrics_table.js` | `npm run debug:check-metrics` | Inspect AA performance metrics table structure and completeness |
| `debug_aa_mapping.js` | `npm run debug:mapping` | Diagnose model→AA slug mapping mismatches |
| `find_models_with_aa_metrics.js` | `npm run debug:find-with-metrics` | List models grouped by metrics availability |
| `find_unmapped_models.js` | `npm run debug:find-unmapped` | Find `working_version` models missing AA mappings |

## Validation

Run before deployments to verify data integrity.

| Script | Command | Description |
|--------|---------|-------------|
| `test_aa_api.js` | `npm run validate:api` | Verify Artificial Analysis API connectivity and response format |
| `test_intelligence_parsing.js` | `npm run validate:parsing` | Test intelligence index score parsing |
| `validate_scoring.js` | `npm run validate:scoring` | End-to-end scoring validation with live data |

## SQL Schema Files

Located in `scripts/db/`. Run manually via Supabase SQL Editor or psql:

- `create_rate_limits_table.sql` - Schema for `ims.30_rate_limits`
- `create_model_selection_score_table.sql` - Schema for `ims.40_model_selection_score`

## Prerequisites

All scripts require environment variables set in `.env`:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
ARTIFICIALANALYSIS_API_KEY=your-api-key  # For validation scripts
```

## Running Scripts

From the `selector-service/` directory:

```bash
# Using npm scripts (recommended)
npm run debug:check-metrics

# Direct execution
node scripts/debug/check_aa_metrics_table.js
```
