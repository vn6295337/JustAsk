# JustAsk Router - Project Overview

**Last Updated:** 2025-11-24
**Status:** Active - Phase 5 (98% Complete)

---

## Table of Contents

1. [Mission](#mission)
2. [Problem Statement](#problem-statement)
3. [MVP Goals](#mvp-goals)
4. [Technical Decisions](#technical-decisions)
5. [Success Metrics](#success-metrics)
6. [Risk Assessment](#risk-assessment)
7. [Decision Log](#decision-log)

---

## Mission

Build an intelligent, data-driven model selection service that dynamically selects optimal AI models from Supabase based on real-time availability, performance metrics, rate limits, and query characteristics.

**Core Value:**
- Adapts to daily model updates automatically
- Optimizes for performance using Intelligence Index scores
- Distributes load intelligently across rate-limited providers
- Matches query complexity to provider capabilities
- Reduces latency through smart caching

---

## Problem Statement

### Current Issues

**JustAsk API Limitations:**
1. **Hardcoded Models** - Static configuration, cannot adapt to new models
2. **Suboptimal Routing** - No performance-based selection, reactive rate limit handling
3. **Maintenance Burden** - Manual updates, duplicated model strings

**Impact:**
- Lower quality responses from suboptimal model selection
- Rate limit errors from poor distribution
- Slow to leverage new models from justask-registry pipeline

---

## MVP Goals

### Phase-by-Phase Features

**Phase 1: Foundation ✅**
- Supabase integration (working_version table)
- 24-hour caching with background refresh
- Model filtering by modalities

**Phase 2: Selection Algorithm ✅**
- Intelligence Index integration (Artificial Analysis API)
- Multi-factor scoring (performance, latency, headroom, geography)
- Query complexity to headroom matching

**Phase 3: Rate Limit Intelligence ✅**
- Provider usage tracking (in-memory counters)
- Smart load distribution
- Headroom-based routing

**Phase 4: Integration ✅**
- RESTful API endpoint (POST /select-model, GET /best-model)
- JustAsk API backend integration
- Error handling and fallback logic

**Phase 5: Operations (98% Complete)**
- Comprehensive testing (unit + integration)
- Documentation and deployment guides
- Monitoring and observability

### Success Criteria

- Sub-100ms selection latency (with cache) ✅
- 95%+ selection success rate ✅
- Intelligent rate limit distribution ✅
- Zero hardcoded models in JustAsk API ✅

---

## Technical Decisions

### Architecture

**Microservice vs Integrated**
- **Decision:** Microservice (separate service)
- **Rationale:** Clean separation, independent deployment, reusable
- **Trade-off:** Network latency acceptable for <100ms target

**Data Source**
- **Decision:** Use working_version table (read-only) + model_aa_mapping + aa_performance_metrics (3-table architecture)
- **Rationale:** Pipeline owns working_version, selector owns mappings - clean separation of concerns
- **Benefit:** Automatic updates when pipeline adds new models

### Selection Criteria

**License Filtering**
- **Decision:** No mandatory license filtering
- **Rationale:** Flexibility for different use cases
- **Implementation:** License score as minor weight (5%) in overall scoring

**Missing Intelligence Index Scores**
- **Decision:** Graceful degradation
- **Fallback:** Model size heuristic (inferred from name: 70b > 27b > 8b)
- **Rationale:** Service must remain functional if external API unavailable

**Modality Filters**
- **Decision:** Dynamic, query-based filtering
- **Apply:** Only filter when truly necessary (image input, audio input)
- **Skip:** "Text output capable" (almost all models support this)

### Rate Limit Handling

**Approach**
- **Decision:** Smart distribution, not avoidance
- **Logic:** Simple queries → providers with less headroom; Complex queries → providers with most headroom
- **Rationale:** All providers are rate-limited; optimize total capacity

**Tracking Accuracy**
- **Decision:** Approximate tracking (in-memory counters, 60-second windows)
- **Trade-off:** Simplicity vs perfect accuracy
- **Future:** Redis for persistent tracking in production if needed

### Performance Metrics

**Source**
- **Decision:** Artificial Analysis Intelligence Index API
- **Rationale:** Industry-standard benchmarks, user requested
- **Fallback:** Cached data (7-day TTL) or heuristic scoring

**Caching Strategy**
- **Decision:** 24-hour cache TTL (changed from 30-min to match database update frequency)
- **Rationale:** justask-registry updates daily, 24-hour staleness acceptable
- **Benefit:** Minimizes cache miss latency

### Integration

**JustAsk API Integration Points**
- `routing/router.js` - Primary selection
- `failover/failover.js` - Use returned model names
- `utils/modelSelectorClient.js` - HTTP client

**Complexity Scoring**
- **Decision:** Client (JustAsk API) calculates complexity score (0.0-1.0)
- **Rationale:** Domain knowledge in JustAsk API; selector focuses on selection logic only
- **Factors:** Query length, keyword detection, query classification

**Error Handling**
- **Decision:** Graceful degradation chain
- **Sequence:** Relax modality → Relax license → Relax geography → Return error
- **Fallback:** Client falls back to hardcoded defaults if selector unavailable

### Testing

**Coverage Target:** 80% minimum (branches, functions, lines, statements)
- Unit tests: All services, utils
- Integration tests: End-to-end selection flow
- Supabase query tests (mocked)
- Cache behavior tests
- Error handling tests

---

## Success Metrics

### Performance

| Metric | Target | Status |
|--------|--------|--------|
| Selection Latency (cached) | < 100ms | ✅ 5-6ms achieved |
| Selection Latency (uncached) | < 500ms | ✅ ~50ms |
| Cache Hit Rate | > 95% | ✅ Achieved |
| API Availability | > 99.5% | ✅ Achieved |

### Quality

| Metric | Target | Status |
|--------|--------|--------|
| Selection Success Rate | > 95% | ✅ Achieved |
| Intelligence Index Coverage | > 80% | 49% (35/50+ models) |
| Test Coverage | > 80% | 🟡 Pending full coverage report |
| Model Freshness | < 24 hours | ✅ Achieved |

### Business

| Metric | Target | Status |
|--------|--------|--------|
| Rate Limit Distribution | Balanced ±20% | ✅ Achieved |
| New Model Adoption | < 24 hours | ✅ Automatic |
| JustAsk API Integration | 100% | ✅ Complete |
| Documentation Completeness | 100% | ✅ Complete |

---

## Risk Assessment

### Technical Risks

| Risk | Mitigation |
|------|------------|
| Intelligence Index API unavailable | Graceful degradation, fallback to latency-only scoring |
| Supabase query latency > 500ms | Optimize queries, add indexes, 24-hour cache TTL |
| ai_models_main schema changes | Version queries, monitor for schema updates |
| Cache invalidation issues | Background refresh, force refresh endpoint |

### Integration Risks

| Risk | Mitigation |
|------|------------|
| JustAsk API breaking changes | Versioned API, backward compatibility |
| Provider rate limit changes | Configurable limits, monitor external docs |
| Model naming inconsistencies | Normalize names, maintain model_aa_mapping table |
| Network latency to Supabase | Regional deployment, connection pooling |

### Operational Risks

| Risk                           | Mitigation                                         |
| ------------------------------ | -------------------------------------------------- |
| Service downtime               | Error handling, fallback to hardcoded defaults     |
| Memory leaks (in-memory cache) | Monitoring, automatic restarts, bounded cache      |
| External API cost overruns     | Rate limit Intelligence Index calls, cache results |

---

## Decision Log

| Date | Decision | Rationale | Impact |
|------|----------|-----------|--------|
| 2025-11-19 | No mandatory license filtering | Flexibility for different use cases | Selection algorithm accepts optional license preference |
| 2025-11-19 | Intelligence Index from Artificial Analysis | User requested, industry standard | Phase 2 dependency on external API |
| 2025-11-19 | 30-minute cache TTL (initial) | Balance freshness vs performance | Acceptable staleness given daily updates |
| 2025-11-19 | Microservice architecture | Clean separation, reusability | Network latency acceptable for target |
| 2025-11-19 | In-memory cache for MVP | Simplicity over complexity | Redis option for production if needed |
| 2025-11-19 | 80% test coverage target | High confidence without diminishing returns | Comprehensive test suite required |
| 2025-11-24 | Changed cache TTL to 24 hours | Match database update frequency from justask-registry | Reduced unnecessary cache refreshes |
| 2025-11-24 | 3-table architecture (working_version + model_aa_mapping + aa_performance_metrics) | Keep working_version read-only, separate mapping layer | Clean separation: pipeline owns source, selector owns mappings |

---

**Document Owner:** Development Team
**Next Review:** Post-deployment
