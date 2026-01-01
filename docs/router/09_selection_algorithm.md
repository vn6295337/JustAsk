# Selection Algorithm

**Last Updated:** 2025-12-30
**Purpose:** Single source of truth for model selection logic

---

## Algorithm Overview

```
INPUT:
  queryType, queryText, modalities[], complexityScore

PROCESS:
  1. Fetch models from cache (24-hour TTL)
  2. Filter by modality requirements
  3. Calculate multi-factor scores for each model
  4. Apply complexity-headroom matching
  5. Sort by score (descending)
  6. Record usage and return top model

OUTPUT:
  provider, modelName, score, rateLimitHeadroom, intelligenceIndex
```

---

## Scoring Formula

```
score = (
  intelligenceIndex × 0.35 +
  latencyScore      × 0.25 +
  headroomScore     × 0.25 +
  geographyScore    × 0.10 +
  licenseScore      × 0.05
)
```

**Weights must sum to 1.0**

---

## Factor Definitions

### 1. Intelligence Index (35%)

**Source:** Artificial Analysis API → `ims.20_aa_performance_metrics`
**Range:** 0.0 to 1.0 (normalized from 0-100)
**Fallback:** Model size heuristic when API unavailable

| Model Size | Fallback Score |
|------------|----------------|
| 70b+ | 0.9 |
| 27b-69b | 0.7 |
| 8b-26b | 0.5 |
| 4b-7b | 0.4 |
| <4b | 0.3 |

### 2. Latency Score (25%)

**Source:** Static provider mapping
**Range:** 0.6 to 1.0

| Provider | Score | Rationale |
|----------|-------|-----------|
| groq | 1.0 | Fastest inference |
| google | 0.8 | Fast |
| openrouter | 0.6 | Moderate (routing overhead) |

### 3. Headroom Score (25%)

**Source:** In-memory rate limit tracker (per-model)
**Range:** 0.0 to 1.0
**Formula:** `min(rpmHeadroom, rpdHeadroom, tpmHeadroom, tpdHeadroom)`

#### Per-Metric Calculation

```
headroom = (limit - usage) / limit
```

| Metric | Window | Limit Source |
|--------|--------|--------------|
| RPM | 60 seconds | `ims.30_rate_limits.rpm` |
| RPD | 24 hours | `ims.30_rate_limits.rpd` |
| TPM | 60 seconds | `ims.30_rate_limits.tpm` |
| TPD | 24 hours | `ims.30_rate_limits.tpd` |

#### Token Estimation

```javascript
estimatedTokens = Math.ceil(queryText.length * 0.75)
```

#### Example Calculation

```
Model: Llama 3.1 70B Versatile
Limits: RPM=30, RPD=14400, TPM=15000, TPD=500000

Current Usage (tracked in-memory):
- Requests in last 60s: 5
- Requests in last 24h: 2000
- Tokens in last 60s: 3000
- Tokens in last 24h: 150000

Headroom:
- rpmHeadroom = (30 - 5) / 30 = 0.833
- rpdHeadroom = (14400 - 2000) / 14400 = 0.861
- tpmHeadroom = (15000 - 3000) / 15000 = 0.800
- tpdHeadroom = (500000 - 150000) / 500000 = 0.700

headroomScore = min(0.833, 0.861, 0.800, 0.700) = 0.700
```

### 4. Geography Score (10%)

**Source:** `working_version.model_provider_country`
**Range:** 0.0 to 1.0
**Default:** 1.0 (US providers preferred)

| Country | Score |
|---------|-------|
| United States | 1.0 |
| Other | 0.9 |

### 5. License Score (5%)

**Source:** `working_version.license_name`
**Range:** 0.8 to 1.0

| License Type | Score |
|--------------|-------|
| Open-source (MIT, Apache-2.0, Llama, etc.) | 1.0 |
| Proprietary | 0.8 |

---

## Complexity-Headroom Matching

After scoring, models are filtered by complexity requirements:

| Complexity Score | Required Headroom | Use Case |
|------------------|-------------------|----------|
| > 0.7 (High) | > 0.6 | Complex analysis, long responses |
| 0.4 - 0.7 (Medium) | > 0.3 | Moderate queries |
| < 0.4 (Low) | Any | Simple questions |

```javascript
function matchComplexityToHeadroom(models, complexityScore) {
  if (complexityScore > 0.7) {
    return models.filter(m => m.headroomScore > 0.6);
  } else if (complexityScore > 0.4) {
    return models.filter(m => m.headroomScore > 0.3);
  }
  return models;
}
```

---

## Modality Filtering

Models are filtered to match required input/output modalities:

```javascript
function filterByModalities(models, required) {
  return models.filter(model => {
    const inputMods = model.input_modalities?.split(',').map(s => s.trim().toLowerCase());
    const outputMods = model.output_modalities?.split(',').map(s => s.trim().toLowerCase());

    return required.every(mod =>
      inputMods?.includes(mod) || outputMods?.includes(mod)
    );
  });
}
```

---

## Complete Scoring Example

```
Query: "Explain quantum entanglement in detail"
Complexity: 0.6 (medium)
Modalities: ["text"]

Model: Llama 3.1 70B Versatile (groq)

Factors:
- intelligenceIndex: 0.524 (52.4/100 normalized)
- latencyScore: 1.0 (groq = fastest)
- headroomScore: 0.700 (min of 4 metrics)
- geographyScore: 1.0 (US provider)
- licenseScore: 1.0 (Llama-3.1 = open)

Calculation:
score = (0.524 × 0.35) + (1.0 × 0.25) + (0.700 × 0.25) + (1.0 × 0.10) + (1.0 × 0.05)
score = 0.1834 + 0.25 + 0.175 + 0.10 + 0.05
score = 0.7584

Complexity Check:
- complexityScore (0.6) requires headroom > 0.3
- headroomScore (0.700) > 0.3 ✓

Result: Model passes all filters with score 0.7584
```

---

## Implementation

**File:** `src/services/modelSelector.js`

```javascript
export function calculateScores(models, queryType, complexityScore) {
  return models.map(model => {
    const intelligenceScore = getIntelligenceScore(model);
    const latencyScore = LATENCY_SCORES[model.inference_provider] || 0.5;
    const headroomScore = rateLimitTracker.getHeadroom(model.human_readable_name);
    const geographyScore = getGeographyScore(model.model_provider_country);
    const licenseScore = getLicenseScore(model.license_name);

    const score = (
      intelligenceScore * SELECTION_WEIGHTS.intelligenceIndex +
      latencyScore * SELECTION_WEIGHTS.latency +
      headroomScore * SELECTION_WEIGHTS.rateLimitHeadroom +
      geographyScore * SELECTION_WEIGHTS.geography +
      licenseScore * SELECTION_WEIGHTS.license
    );

    return { ...model, score, intelligenceScore, latencyScore, headroomScore, geographyScore, licenseScore };
  });
}
```

---

## Configuration

**File:** `src/config/constants.js`

```javascript
export const SELECTION_WEIGHTS = {
  intelligenceIndex: 0.35,
  latency: 0.25,
  rateLimitHeadroom: 0.25,
  geography: 0.10,
  license: 0.05
};

export const LATENCY_SCORES = {
  groq: 1.0,
  google: 0.8,
  openrouter: 0.6
};

export const COMPLEXITY_THRESHOLDS = {
  high: 0.7,
  medium: 0.4
};
```

---

**Document Owner:** Development Team
