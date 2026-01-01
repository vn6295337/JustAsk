# JustAsk: Abstracting AI Complexity Through Intelligent Routing

## Why We Built This

**Hypothesis**: As AI models proliferate, a unified routing layer that abstracts provider complexity could reduce adoption friction and eliminate vendor lock-in.

**Investment**: Minimal. Free-tier infrastructure, open-source tooling, single developer.

**Goal**: Validate the pattern before committing resources to production build.

---

## The Problem

The AI model landscape is fragmented and constantly shifting. There are now **50+ models** across **3 free-tier providers** (OpenRouter, Google, Groq), each with:

- Different APIs and authentication methods
- Different pricing structures (per token, per request, tiered)
- Different rate limits and availability windows
- Different strengths (coding, reasoning, creativity, speed)
- Weekly changes as new models launch and old ones deprecate

**For users**, this fragmentation creates friction. Want to ask a simple question? First, decide which provider. Sign up. Get an API key. Learn their interface. Hit a rate limit? Start over with another provider.

**For businesses**, this fragmentation creates risk. Commit to one provider, and you're locked in when pricing changes or a better model emerges elsewhere. Try to use multiple providers, and you're maintaining parallel integrations while manually tracking which model is best for which task.

**For developers**, this fragmentation is a moving target. The "best" model today may be outdated next week. Keeping up requires constant research—time that could be spent building.

---

## The Solution

JustAsk eliminates this complexity through **intelligent multi-provider routing**:

**One interface. Any model. Automatic optimization.**

### The Product: JustAsk App

A mobile app where users simply ask questions and get answers. No signup. No API keys. No provider selection. The complexity is invisible.

- Open the app, type a question
- System automatically selects the best available model
- Response returned with automatic failover if needed
- Works offline—queries queue and sync when connected

**Users never see the underlying infrastructure.** They just get answers.

### The Backbone

Three components power the app behind the scenes:

| Component | Function |
|-----------|----------|
| **justask-registry** | Daily ETL pipeline that aggregates model data from 3 providers. 37 stages required because each provider returns incompatible formats. |
| **justask-router** | Real-time scoring engine that ranks models by performance, availability, and fit. Returns optimal model with fallback chain. |
| **justask-dashboard** | Dashboard that tracks model changes—additions, deprecations, rate limit updates. Provides visibility into the shifting landscape. |

---

## What We Validated

| Question | Result |
|----------|--------|
| Can we create a unified view from heterogeneous AI provider APIs? | Yes — but requires 37 pipeline stages and manual verification |
| Can we rank models by real benchmark data in near real-time? | Yes — Artificial Analysis Intelligence Index integration |
| Can we route intelligently? | Yes — multi-factor scoring with automatic failover |
| Can users access AI without API keys or signup? | Yes — zero-config mobile app |
| Does offline-first work for mobile AI? | Yes — local queue with auto-sync |

---

## How It Works

```
justask-registry (daily)
    ↓
    37-stage ETL pipeline
    ↓
    Manual verification
    ↓
Supabase (Single Source of Truth)
    ↓
    ├── justask-router (query-time)
    │       ↓
    │       Multi-factor scoring + AA benchmarks
    │       ↓
    │       JustAsk App (user interface)
    │
    └── justask-dashboard (visualization)
            ↓
            Dashboard + Analytics
```

---

## Why This Matters

### No More Provider Lock-In
The system abstracts provider-specific details into a **unified abstraction layer**. When a better model launches on any provider, it automatically becomes available. No code changes. No migration project. The intelligent selector routes to it based on merit.

### No More Manual Research
The daily pipeline eliminates the "which model should I use?" research loop. Current data on 50+ models, updated automatically, with performance benchmarks from independent sources.

### No More API Key Management
End users never deal with API credentials, rate limits, or provider accounts. The system handles authentication, fallback, and retry logic internally.

### No More DIY Integration
Instead of building and maintaining separate integrations for each provider, route intelligently through a single layer. The complexity is handled once, centrally.

---

## Component Characteristics

### 1. justask-registry — Data Integration Layer

**Why This Exists**

AI providers don't speak the same language. Each has different API formats, different metadata schemas, different ways of representing the same information. Before you can route intelligently, you need a single source of truth.

justask-registry creates that unified view—aggregating, normalizing, and validating model data from multiple providers into a consistent catalog.

**The Reality of "Good" Data Sources**

| Finding | Detail |
|---------|--------|
| **90% Filtered Out** | 353 models → 34 usable (excludes paid, experimental, preview, cloaked, unknown origin, no-license models) |
| **48 → 6 License Variations** | 48 naming inconsistencies normalized to 6 canonical forms |
| **3 Incompatible Schemas** | Each provider returns fundamentally different structures |
| **APIs Are Incomplete** | Google API has no modalities; Groq has no API at all |
| **Silent Fallbacks** | When parsing fails, provider defaults applied invisibly |
| **Manual Gates Required** | "Preview" status not detectable from API—requires human testing |

#### Why 37 Pipeline Stages Exist

Each provider presents unique data challenges:

- **OpenRouter (19 stages)**: Rich API, but license info scattered across HuggingFace. Requires cross-referencing external sources.
- **Google (8 stages)**: API returns model names only—modalities require web scraping from documentation pages.
- **Groq (10 stages)**: No structured API exists. Everything scraped from HTML tables using Selenium.

---

### 2. justask-router — Routing Intelligence

**Why This Exists**

Having a catalog of models isn't enough. You need to decide which model to use for each query—and that decision should be intelligent, not random or hard-coded.

justask-router turns model selection into a real-time optimization problem, balancing quality, speed, availability, and cost on every request.

**Weighted Selection Score**

| Factor | Weight | Source |
|--------|--------|--------|
| Intelligence Index | 35% | Artificial Analysis API |
| Provider Latency | 25% | Pre-configured tier (Groq > Google > OpenRouter) |
| Rate Limit Headroom | 25% | Real-time iterative calculation |
| Geography | 10% | Model provider country |
| License | 5% | Open-source preference |

---

### 3. JustAsk App — User Access Layer

**Why This Exists**

Most AI tools require technical setup: choose a provider, sign up, get API keys, manage rate limits, handle billing. This creates friction that blocks non-technical users from benefiting from AI.

JustAsk App removes all of that. Open the app, ask a question, get an answer.

| Principle | Implementation |
|-----------|----------------|
| **No Data Collection** | All queries and responses stored locally on device. Nothing sent to cloud storage. |
| **No Signup** | Completely anonymous. No accounts, no registration, no user IDs. |
| **Zero Cost** | Free-tier providers only. No subscriptions, no credit cards. |
| **No API Keys** | Users never see or manage credentials. Keys stored server-side in Supabase Vault. |
| **Offline-First** | Queries queue locally when offline. Auto-sync when connection restored. |
| **Transparent** | Every response shows: which LLM answered, response time, whether it was cached. |

---

### 4. justask-dashboard — Change Tracking & Visualization

**Why This Exists**

The AI model landscape changes constantly. Providers add models, deprecate others, remove free tiers, adjust rate limits, update licensing. Without visibility into these changes, you're operating blind.

justask-dashboard provides that visibility—a dashboard that tracks what changed, when, and across which providers.

---

## Current Scope & Limitations

This is a **proof-of-concept**, not a production system:

| Constraint | Detail |
|------------|--------|
| **3 Providers** | OpenRouter, Google, Groq — free tiers only |
| **50+ Models** | Subset of the broader AI landscape |
| **Rate Limited** | 15-60 RPM depending on provider |
| **Single-User Design** | No enterprise features, no multi-tenancy |
| **Manual Verification** | Data upload requires human review |

---

*Built to demonstrate practical AI platform architecture—and the unglamorous reality of data management that underpins it.*
