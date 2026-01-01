# JustAsk Registry Architecture

## Overview

Multi-pipeline system for discovering, enriching, and managing AI model metadata from Google, Groq, and OpenRouter.

## Directory Structure

```
justask-registry/
├── src/
│   ├── main.py                   # Unified CLI entry point
│   ├── pipelines/
│   │   ├── base.py               # Base pipeline runner
│   │   ├── google/steps/         # Google pipeline (8 steps)
│   │   ├── groq/steps/           # Groq pipeline (9 steps)
│   │   └── openrouter/steps/     # OpenRouter pipeline (21 steps)
│   ├── utils/                    # Shared utilities
│   └── models/                   # Data models
├── config/
│   ├── google/                   # Google pipeline configs
│   ├── groq/                     # Groq pipeline configs
│   └── openrouter/               # OpenRouter pipeline configs
├── outputs/                      # Pipeline outputs (gitignored)
│   ├── google/
│   ├── groq/
│   └── openrouter/
├── docs/                         # Documentation
├── scripts/                      # Standalone scripts
└── tests/                        # Test suite
```

## Usage

```bash
# Run from project root
python3 -m src.main google --steps 1-6
python3 -m src.main groq --steps 1-7
python3 -m src.main openrouter --steps 1-19

# Dry run
python3 -m src.main google --dry-run

# Specific steps
python3 -m src.main openrouter --steps 1,3,5
```

## Pipelines

### Google Pipeline (8 steps)
Fetches models from Google AI API, enriches with modality information.

### Groq Pipeline (9 steps)
Scrapes Groq's model catalog, extracts license/modality data.
Requires Selenium/Chrome for web scraping.

### OpenRouter Pipeline (21 steps)
Most comprehensive - aggregates models from multiple providers with full license and modality enrichment.

## Data Flow

```
Source → Fetch → Filter → Enrich → Normalize → Compare → Deploy
```

1. **Fetch**: Get raw model data from API/web
2. **Filter**: Apply inclusion/exclusion rules
3. **Enrich**: Add licenses, modalities, provider info
4. **Normalize**: Standardize field names and values
5. **Compare**: Diff against existing database
6. **Deploy**: Update Supabase tables

## Configuration

Each pipeline has its own config directory:
- `config/google/` - filtering_rules.json, licenses.json, etc.
- `config/groq/` - api_endpoints.json, hf_mappings.json, etc.
- `config/openrouter/` - filtering_rules.json, provider_enrichment.json, etc.

## Database

Two main tables in Supabase:
- `working_version` - Staging table for pipeline updates
- `ai_models_main` - Production table for frontend consumption

See `docs/security.md` for RLS configuration.
