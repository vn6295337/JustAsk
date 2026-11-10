/**
 * Ranked Model Selector
 * Fetches pre-computed model rankings from justask-router
 * and provides fallback chain based on selection scores
 */

const SELECTOR_SERVICE_URL = process.env.SELECTOR_SERVICE_URL || 'http://localhost:3001';

const SELECTOR_TIMEOUT_MS = 3000;
const SELECTOR_CACHE_TTL_MS = 60000;
let selectorCache = { models: null, at: 0 };

/**
 * Fetch ranked models from justask-router
 * @param {number} limit - Number of top models to fetch (default: 10)
 * @returns {Promise<Array>} Ranked list of models
 */
export async function fetchRankedModels(limit = 10) {
  const now = Date.now();
  if (selectorCache.models && now - selectorCache.at < SELECTOR_CACHE_TTL_MS) {
    return selectorCache.models;
  }

  try {
    const response = await fetch(`${SELECTOR_SERVICE_URL}/best-models?limit=${limit}`, {
      signal: AbortSignal.timeout(SELECTOR_TIMEOUT_MS),
    });

    if (!response.ok) {
      throw new Error(`Selector service returned ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    const models = Array.isArray(data.models) ? data.models : [];
    if (models.length > 0) {
      selectorCache = { models, at: Date.now() };
    }
    return models;
  } catch (error) {
    console.error('[RankedModelSelector] Error fetching ranked models:', error.message);
    return [];
  }
}

/**
 * Get model fallback chain from pre-computed rankings
 * Returns models in order of selection_score (highest first)
 * @returns {Promise<Array<{provider: string, modelName: string, rank: number}>>}
 */
export async function getModelFallbackChain() {
  const rankedModels = await fetchRankedModels(10);

  if (rankedModels.length === 0) {
    console.warn('[RankedModelSelector] No ranked models available, using hardcoded fallback');
    // Hardcoded fallback if selector service unavailable
    return [
      { provider: 'groq', modelName: 'llama-3.1-70b-versatile', rank: 0, fallback: true },
      { provider: 'gemini', modelName: 'gemini-2.5-flash', rank: 0, fallback: true },
      { provider: 'openrouter', modelName: 'google/gemini-2.0-flash-exp:free', rank: 0, fallback: true }
    ];
  }

  // Normalize provider names to lowercase to match config.providerNames
  return rankedModels.map(m => ({
    provider: m.provider.toLowerCase(),
    modelName: m.modelName,
    rank: m.rank,
    selectionScore: m.selectionScore,
    intelligenceIndex: m.intelligenceIndex
  }));
}

/** Test helper: clear the selector cache */
export function _resetSelectorCache() {
  selectorCache = { models: null, at: 0 };
}

export default {
  fetchRankedModels,
  getModelFallbackChain,
};
