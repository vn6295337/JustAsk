 Comprehensive mapping of integrations between the four modules:

       ---
       MODULE 1: justask-registry (Discovery Pipeline)

       Purpose: Automated data pipeline that discovers, enriches, and deploys AI model metadata to Supabase

       Database Connection:
       - Connection Type: PostgreSQL direct connection via psycopg2
       - Environment Variable: PIPELINE_SUPABASE_URL (PostgreSQL connection string)
       - Role: pipeline_writer (write access to database)
       - Connection Logic: Located in /src/utils/db.py with IPv4 resolution for GitHub Actions compatibility

       Tables Written To:
       1. public.working_version - Staging table for pipeline-managed model data
         - Method: DELETE by provider + INSERT new records
         - Scripts: T_refresh (OpenRouter), G_refresh (Google), H_refresh (Groq)
         - Holds raw model metadata before deployment
       2. public.ai_models_main - Production table consumed by all services
         - Method: BACKUP + DELETE + INSERT from working_version
         - Scripts: U_deploy (OpenRouter), H_deploy (Google), I_deploy (Groq)
         - Contains 50+ models with full metadata
       3. ims.10_model_aa_mapping - Provider slug to Artificial Analysis mapping
         - Method: UPSERT (INSERT ON CONFLICT DO UPDATE)
         - Maps: inference_provider, provider_slug → aa_slug
         - Script: refresh_model_aa_mapping
       4. ims.30_rate_limits - Normalized rate limits parsed from working_version
         - Method: DELETE + UPSERT
         - Fields: human_readable_name, inference_provider, rpm, rpd, tpm, tpd
         - Source: Text parsing of working_version.rate_limits column

       Environment Variables:
       PIPELINE_SUPABASE_URL=postgresql://pipeline_writer:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
       SUPABASE_URL=https://PROJECT_REF.supabase.co
       SUPABASE_ANON_KEY=your-anon-key
       GROQ_API_KEY=your-groq-key (from Supabase secrets or env)

       External API Dependencies:
       - OpenRouter API (19-stage pipeline)
       - Google Gemini API (8-stage pipeline)
       - Groq API (10-stage pipeline)
       - Artificial Analysis API (weekly ETL - external source)

       ---
       MODULE 2: justask-router (Model Selection Microservice)

       Purpose: Intelligent model selection service that routes queries to optimal AI providers

       Server Configuration:
       - Port: 3001
       - Framework: Node.js Express
       - Entry Point: /selector-service/src/index.js

       Database Connection:
       - Connection Type: Supabase REST API + JavaScript client
       - Environment Variables:
       SUPABASE_URL=https://your-project.supabase.co
       SUPABASE_KEY=your-anon-key-here
       ARTIFICIALANALYSIS_API_KEY=optional-for-metrics
       - Auth: Public anon key (read-only access via RLS)

       Tables Read From:

       1. public.working_version - Base model data
         - Query: SELECT * ORDER BY updated_at DESC
         - Used for: Core model information
       2. ims.10_model_aa_mapping (schema: 'ims')
         - Query: SELECT provider_slug, aa_slug, inference_provider
         - Used for: Mapping models to Artificial Analysis slugs
       3. ims.20_aa_performance_metrics (schema: 'ims')
         - Query: SELECT aa_slug, intelligence_index, coding_index, math_index, name
         - Used for: Intelligence Index scoring (35% of selection algorithm)
       4. ims.30_rate_limits (schema: 'ims')
         - Query: SELECT human_readable_name, rpm, rpd, tpm, tpd, parseable
         - Used for: Rate limit headroom calculation (25% of selection algorithm)
       5. ims.40_model_selection_score (schema: 'ims')
         - Query: Pre-computed rankings with selection_score ordered descending
         - Used for: /best-models endpoint

       API Endpoints:

       | Endpoint           | Method | Purpose                   | Returns                                |
       |--------------------|--------|---------------------------|----------------------------------------|
       | /health            | GET    | Health check              | Uptime, cache stats, rate limit stats  |
       | /models            | GET    | List all models           | Array of models with metrics           |
       | /best-model        | GET    | Top model by intelligence | Single model with highest index        |
       | /best-models       | GET    | Top N ranked models       | Array of top models by selection score |
       | /select-model      | POST   | Intelligent selection     | Optimal model based on query type      |
       | /cache/refresh     | POST   | Force cache update        | Refreshed model count                  |
       | /rate-limits/reset | POST   | Reset counters (testing)  | Confirmation message                   |

       Request/Response for /select-model:
       // Request
       {
         queryType: 'business_news' | 'financial_analysis' | 'creative' | 'general_knowledge',
         queryText: string,
         modalities: ['text' | 'image' | 'audio' | 'video'],
         complexityScore: 0.0-1.0
       }

       // Response
       {
         provider: 'groq' | 'google' | 'openrouter',
         modelName: string,
         humanReadableName: string,
         score: number,
         rateLimitHeadroom: number,
         estimatedLatency: 'low' | 'medium' | 'high',
         intelligenceIndex: number,
         selectionReason: string,
         selectionDuration: number (ms)
       }

       Scoring Algorithm (5-Factor):
       - Intelligence Index: 35%
       - Latency Score: 25% (Groq 1.0, Google 0.8, OpenRouter 0.6)
       - Rate Limit Headroom: 25%
       - Geography (US preferred): 10%
       - License (open source bonus): 5%

       Caching:
       - Cache TTL: 30 minutes (configurable via CACHE_TTLS)
       - Cache key: ai_models_main
       - Pre-warming on startup

       Configuration Files:
       - /src/config/constants.js - Selection weights, latency scores, complexity thresholds

       ---
       MODULE 3: justask (Mobile App + Backend API)

       Purpose: User-facing application with backend API for query processing

       Backend API Configuration:
       - Port: 3000 (default) via environment variable
       - Framework: Node.js Express
       - Entry Point: /api/src/index.js

       Database Connection:
       - Connection Type: Supabase REST API
       - Environment Variables:
       PORT=3000
       NODE_ENV=development
       SUPABASE_URL=https://your-project.supabase.co
       SUPABASE_KEY=your-supabase-public-key
       LOG_LEVEL=debug
       - Auth: Public anon key (or API key depending on RLS)

       Supabase Integration Points:
       - API Keys Location: Stored in Supabase Vault, retrieved at runtime
         - GEMINI_API_KEY
         - GROQ_API_KEY
         - OPENROUTER_API_KEY

       API Endpoints:

       | Endpoint        | Method | Purpose              | Consumes                |
       |-----------------|--------|----------------------|-------------------------|
       | /api/health     | GET    | Service health       | -                       |
       | /api/query      | POST   | Process single query | Query text              |
       | /api/queue/sync | POST   | Sync offline queries | Batch of queued queries |

       Request/Response for /api/query:
       // Request
       {
         query: string
       }

       // Response
       {
         response: string,
         llm_used: string,
         model_name: string,
         model_rank: number,
         selection_score: number,
         category: string,
         response_time: number (ms),
         confidence: number,
         failover_count: number
       }

       Router Integration:
       - File: /api/src/routing/rankedModelSelector.js
       - Service URL: SELECTOR_SERVICE_URL (default: http://localhost:3001)
       - Function: getModelFallbackChain() - Fetches top 10 ranked models from justask-router
       - HTTP Call: GET /best-models?limit=10
       - Fallback: Hardcoded chain if selector service unavailable:
         a. groq:llama-3.1-70b-versatile
         b. gemini:gemini-2.5-flash
         c. openrouter:google/gemini-2.0-flash-exp:free

       Query Processing Flow:
       1. Validate query via /api/query
       2. Classify query type (keyword-based) in classifier.js
       3. Get ranked fallback chain from rankedModelSelector.js (calls justask-router)
       4. Execute with ranked model fallback (tries models in order)
       5. Return response with model metadata

       Provider Integrations:
       - Gemini: /api/src/providers/gemini.js
       - Groq: /api/src/providers/groq.js (supports compound models for news/financial queries)
       - OpenRouter: /api/src/providers/openrouter.js (supports web search for news queries)

       Mobile App Configuration:
       - Framework: React Native + Expo
       - Offline Support: SQLite local database for query queueing
       - API Client: /app/src/services/APIClient.js
       - Sync Service: /app/src/services/SyncManager.js

       CORS Configuration:
       origin: [
         'http://localhost:8081',    // Expo dev server
         'http://localhost:3000',    // Local testing
         'http://localhost:19000',   // Expo tunnel
         'http://localhost:19006',   // Expo web
         '*'                         // MVP mode (restrict in production)
       ]

       ---
       MODULE 4: justask-dashboard (Visualization Dashboard)

       Purpose: Real-time visualization dashboard for 50+ AI models

       Frontend Framework:
       - Technology: React 18 + TypeScript + Vite
       - Charts: Chart.js
       - Deployment: GitHub Pages (static hosting)
       - Live URL: Auto-deploys on push to main branch

       Database Connection:
       - Connection Type: Supabase JavaScript client
       - Environment Variables (Vite):
       VITE_SUPABASE_URL=https://your-project-ref.supabase.co
       VITE_SUPABASE_ANON_KEY=your-anon-key-here
       - Auth: Public anon key (read-only access)
       - Configuration File: /src/integrations/supabase/client.ts

       Tables Read From:

       1. public.ai_models_main - Primary data source
         - Query: SELECT * with 5-minute refresh interval
         - Used in: AiModelsVisualization.tsx, Analytics.tsx
         - Fields displayed: model_name, provider, license, pricing, task_type, etc.
       2. ai_models_discovery - Alternative discovery table
         - Used in: ModelsSSoT.tsx (Models "Source of Truth" component)
         - Fallback data if Supabase unavailable

       Auto-refresh Mechanism:
       - Interval: 5 minutes
       - Type: Client-side polling via Supabase queries
       - Cache control headers: No-cache directives to prevent stale data

       Key Components:

       | Component                 | Queries             | Purpose                          |
       |---------------------------|---------------------|----------------------------------|
       | AiModelsVisualization.tsx | ai_models_main      | Interactive model visualizations |
       | Analytics.tsx             | ai_models_main      | Analytics and statistics         |
       | ModelsSSoT.tsx            | ai_models_discovery | Filterable model catalog         |
       | Executive.tsx             | ai_models_main      | Executive summary view           |

       Features:
       - Dark mode toggle (localStorage persistence)
       - Search, filter, sort functionality
       - Provider, license, and task type filtering
       - CSV export capability
       - Mobile-responsive UI
       - Real-time model count display

       Shared Database Schema:
       - Location: /supabase/ directory
       - Types: Auto-generated in /src/integrations/supabase/types.ts

       ---
       SHARED CONFIGURATION & ENVIRONMENT VARIABLES

       Supabase Project Configuration:
       Standard setup: https://PROJECT_REF.supabase.co

       Environment Variables by Module:

       | Variable              | Registry       | Router | API                         | Dashboard        |
       |-----------------------|----------------|--------|-----------------------------|------------------|
       | SUPABASE_URL          | ✓              | ✓      | ✓                           | ✓ (VITE_)        |
       | SUPABASE_ANON_KEY     | ✓              | ✓      | ✓                           | ✓ (VITE_)        |
       | PIPELINE_SUPABASE_URL | ✓ (PostgreSQL) | -      | -                           | -                |
       | PORT                  | -              | 3001   | 3000                        | - (GitHub Pages) |
       | SELECTOR_SERVICE_URL  | -              | -      | ✓ (default: localhost:3001) | -                |
       | NODE_ENV              | -              | ✓      | ✓                           | -                |
       | CACHE_TTL             | -              | ✓      | -                           | -                |

       ---
       DATA FLOW SUMMARY

       justask-registry (Discovery)
         ↓ (Writes 50+ models daily)
       public.working_version (staging)
         ↓ (BACKUP + DELETE + INSERT)
       public.ai_models_main (production)
         ├→ justask-dashboard (reads, 5-min refresh)
         ├→ justask-router (reads + 4-table join)
         │   ├→ ims.10_model_aa_mapping
         │   ├→ ims.20_aa_performance_metrics
         │   └→ ims.30_rate_limits
         │   ↓ (HTTP)
         └→ justask API (HTTP calls to router)
             ├→ /select-model endpoint
             └→ Model providers (Gemini, Groq, OpenRouter)
             ↓ (Response)
             justask mobile app

       ---
       KEY INTEGRATION POINTS

       1. justask-registry → Supabase
         - Direct PostgreSQL writes via PIPELINE_SUPABASE_URL
         - Tables: working_version, ai_models_main, model_aa_mapping, rate_limits
         - Runs: Daily via GitHub Actions
       2. justask-router → Supabase
         - HTTP REST API via anon key
         - 4-table client-side join
         - Cache: 30-minute TTL with pre-warming
       3. justask API → justask-router
         - HTTP POST to http://localhost:3001/select-model
         - Query classification + complexity scoring
         - Ranked fallback chain (10 models)
       4. justask API → LLM Providers
         - API keys from Supabase Vault
         - Failover: Gemini → Groq → OpenRouter
       5. justask-dashboard → Supabase
         - HTTP REST API via anon key
         - 5-minute refresh polling
         - Read-only: ai_models_main table
       6. Shared Supabase Instance
         - Single project for all modules
         - RLS policies enforce access control
         - Public key for client-side reads
         - Pipeline role for server-side writes





  Integration Test Results

  1. justask-registry → Supabase ✅

  ✅ public.working_version: 50+ records
  ✅ public.ai_models_main: 50+ records
  ✅ ims.10_model_aa_mapping: 29 records
  ✅ ims.30_rate_limits: 56 records

  2. justask-router ✅

  ✅ Supabase connection successful
  ✅ Intelligence Index: 367 model scores from API
  ✅ Cached 50+ models
  ✅ /health - 200 OK
  ✅ /best-models - Returns ranked models with scores
  ✅ /select-model - Returns optimal model selection

  3. justask API → justask-router ✅

  ✅ API started on port 3000
  ✅ /api/health - 200 OK
  ✅ /api/query - Successfully calls router, gets model selection, queries LLM

  Sample response:
  {
    "response": "2 + 2 = 4",
    "llm_used": "openrouter",
    "model_name": "kat-coder-pro-v1",
    "model_rank": 1,
    "selection_score": 0.7376,
    "response_time": 2115ms
  }

  4. justask-dashboard → Supabase ✅

  ✅ ai_models_main: 50+ records accessible
  ✅ Sample data: Google (7), OpenRouter (49), Groq (7)

  ---
  Data Flow Verified

  justask-registry
      ↓ (writes 50+ models)
  ┌─────────────────────────────────────────┐
  │  Supabase                               │
  │  ├── public.working_version (50+)       │
  │  ├── public.ai_models_main (50+)        │
  │  ├── ims.10_model_aa_mapping (29)       │
  │  └── ims.30_rate_limits (56)            │
  └─────────────────────────────────────────┘
      ↓ reads                    ↓ reads
  justask-router ←───────── justask-dashboard
      ↓ HTTP /select-model
  justask API
      ↓ LLM request
  Provider (OpenRouter/Groq/Google)
All integrations are functioning correctly.