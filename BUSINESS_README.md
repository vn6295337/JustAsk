# JustAsk

**A Proof-of-Concept demonstrating intelligent AI routing, product thinking, and privacy-first system design.**

[![Dashboard](https://img.shields.io/badge/Dashboard-Live-blue)](https://justask-dashboard.vercel.app/)

---

## Problem Statement

The AI model landscape is fragmented and constantly shifting, creating barriers for users, businesses, and developers:

1. **User Friction** — Want to ask a simple question? First, decide which provider. Sign up. Get an API key. Learn their interface. Hit a rate limit? Start over with another provider. Most users never get past this friction.

2. **Vendor Lock-In** — Commit to one provider, and you're locked in when pricing changes or a better model emerges elsewhere. Try to use multiple providers, and you're maintaining parallel integrations while manually tracking which model is best for which task.

3. **Moving Target** — The "best" model today may be outdated next week. There are now 50+ models across 3 free-tier providers (OpenRouter, Google, Groq), each with different APIs, pricing structures, rate limits, and strengths. Keeping up requires constant research.

These challenges prevent both individual users and organizations from realizing the value of AI assistance.

---

## Solution Overview

JustAsk eliminates this complexity through intelligent multi-provider routing:

- **Zero Friction Access** — Open the app, type a question, get an answer. No signup, no API keys, no provider selection. The complexity is invisible to users.

- **Intelligent Routing** — System automatically selects the best available model using a 5-factor scoring algorithm (Intelligence Index, Latency, Rate Limit Headroom, Geography, License). Returns optimal model with fallback chain.

- **Provider Abstraction** — When a better model launches on any provider, it automatically becomes available. No code changes. No migration project. The intelligent selector routes to it based on merit.

---

## Strategic AI Value

**For User Adoption:**
- Removes all signup and configuration barriers that block non-technical users
- Provides consistent experience regardless of underlying provider changes
- Works offline with automatic queue and sync when connected

**For Cost Optimization:**
- Leverages free tiers across multiple providers (Google, Groq, OpenRouter)
- No infrastructure costs—free-tier hosting on Render, Vercel, GitHub Pages
- Zero API key management overhead for end users

**For Competitive Positioning:**
- Abstracts away the "which model should I use?" decision entirely
- Automatically adapts as the AI landscape evolves
- Privacy-first design with no data collection or cloud storage

---

## Product & System Thinking

**Key Design Decisions:**

| Decision | Rationale | Business Impact |
|----------|-----------|-----------------|
| Multi-provider routing | No single provider dependency | 99%+ availability through cascade failover |
| 37-stage ETL pipeline | Each provider returns incompatible formats | Single source of truth for 50+ models |
| Privacy-first architecture | All data stored locally on device | Zero compliance burden, user trust |
| 5-factor scoring algorithm | Balance quality, speed, availability | Optimal model selection in 5-6ms |
| Free-tier only | Validate pattern before investing | Minimal infrastructure cost |

**Architectural Trade-offs Considered:**
- Chose keyword-based classification over LLM classification for query routing—faster, no additional API calls
- Selected in-memory rate limit tracking over persistent storage—simpler, resets on restart acceptable for PoC
- Prioritized offline-first mobile design over always-connected—better UX for real-world usage

**User-Centric Choices:**
- Every response shows which LLM answered, response time, and whether it was cached—full transparency
- 7-day local cache balances performance with privacy—no permanent storage
- API keys stored server-side in Supabase Vault—users never see or manage credentials

---

## PoC Capabilities

- **Unified Data Integration** — 37-stage ETL pipeline aggregating model data from 3 providers into consistent catalog
- **Intelligent Model Selection** — Multi-factor scoring with real-time rate limit tracking and automatic failover
- **Zero-Config Mobile Access** — React Native app requiring no signup, API keys, or configuration. Three-step UX: type question, tap send, get answer
- **Offline-First Design** — Local queue with automatic sync when connection restored
- **Real-Time Benchmarks** — Integration with Artificial Analysis Intelligence Index for performance data
- **Change Visibility** — Dashboard tracking model additions, deprecations, and rate limit updates
- **Privacy-First Architecture** — No history storage, no tracking, no cloud sync
- **Rapid Prototyping** — Complete platform built and deployed using vibe coding methodology

---

**Dashboard:** [justask-dashboard.vercel.app](https://justask-dashboard.vercel.app/)

**Mobile App:** See [README.md](README.md#mobile-app) for installation via Expo Go

**Technical Documentation:** See [README.md](README.md) for architecture details and setup instructions.
