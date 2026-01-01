# JustAsk Registry

**Version:** 1.0.0

Automated multi-pipeline system for discovering, enriching, and managing AI model metadata from OpenRouter, Google AI, and Groq. Deploys curated datasets to Supabase database for production use by JustAsk platform.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  JUSTASK PLATFORM                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [1] Registry Pipeline  →  [2] Dashboard  →  [3] Client        │
│                                                                 │
│      justask-registry      justask-         justask/           │
│                            dashboard        (api + app)         │
│                                                                 │
│  • 37-stage automation    • Daily updates     • Smart routing  │
│  • Daily updates          • 50+ models        • Multi-provider │
│  • Zero manual work       • Decision support  • Secure access  │
└─────────────────────────────────────────────────────────────────┘
```

**Data Flow:**
Registry Pipeline → Supabase (`ai_models_main` table) → Dashboard + API

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Provider Aggregation** | Fetches model metadata from OpenRouter, Google AI, Groq |
| **License Standardization** | Normalizes 48 license variations to 6 canonical forms |
| **Capability Processing** | Extracts modalities, context windows, pricing |
| **Data Validation** | Ensures quality and consistency before deployment |
| **Daily Automation** | Runs automatically via GitHub Actions at 00:00 UTC |

**Current Dataset:** 50+ models across OpenRouter, Google, and Groq

---

## Pipelines

| Pipeline | Stages | Method |
|----------|--------|--------|
| **OpenRouter** | 19 (A-U) | API with HuggingFace license extraction |
| **Google** | 8 (A-H) | API + web scraping for modalities |
| **Groq** | 10 (A-J) | Web scraping + rate limit detection |

---

## Quick Start

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.local.example .env.local
# Edit .env.local with your credentials
```

---

## Configuration

**Required:**
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_key
OPENROUTER_API_KEY=your_key
```

**Optional:**
```env
GOOGLE_API_KEY=your_key
GROQ_API_KEY=your_key
```

---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Runtime | Python 3.11+ | Type hints, async support |
| Database | Supabase (PostgreSQL) | `ai_models_main` table |
| Automation | GitHub Actions | Daily scheduled runs |
| Web Scraping | Selenium | For providers without APIs |

---

## Usage

```bash
# Run individual pipelines
python -m src.main --pipeline openrouter
python -m src.main --pipeline google
python -m src.main --pipeline groq

# Run all pipelines
python -m src.main --pipeline all
```

---

## License

MIT License - See LICENSE file for details.
