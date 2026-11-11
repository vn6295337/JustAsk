/**
 * Ranked Model Selector
 * Reads the hand-approved model ranking (justask."23_router-model-ranking",
 * built by justask-router/selector-service/scripts/db/populate_model_selection_score.js)
 * directly from Supabase and provides the fallback chain.
 * Replaces the separate justask-router service (one consumer, extra cold start).
 */
import { getSupabase } from '../utils/supabase.js';
import { withTimeout } from '../utils/errors.js';

const RANKING_TABLE = '23_router-model-ranking';
const RANKING_TIMEOUT_MS = 3000;
const RANKING_CACHE_TTL_MS = 5 * 60 * 1000;
let rankingCache = { models: null, at: 0 };

/**
 * Fetch the top-ranked models (cached for 5 minutes)
 * @param {number} limit - Number of top models to fetch (default: 10)
 * @returns {Promise<Array>} Ranked list of models, best first
 */
export async function fetchRankedModels(limit = 10) {
  const now = Date.now();
  if (rankingCache.models && now - rankingCache.at < RANKING_CACHE_TTL_MS) {
    return rankingCache.models;
  }

  try {
    const { data, error } = await withTimeout(
      getSupabase()
        .schema('justask')
        .from(RANKING_TABLE)
        .select('model_name, inference_provider, provider_slug, intelligence_index, selection_score')
        .order('selection_score', { ascending: false })
        .limit(limit),
      RANKING_TIMEOUT_MS,
      'supabase'
    );
    if (error) throw new Error(error.message);

    const models = (data || [])
      .filter((m) => m.inference_provider && m.provider_slug)
      .map((m, i) => ({
        rank: i + 1,
        provider: m.inference_provider,
        modelName: m.provider_slug,
        humanReadableName: m.model_name,
        selectionScore: m.selection_score,
        intelligenceIndex: m.intelligence_index,
      }));
    if (models.length > 0) {
      rankingCache = { models, at: Date.now() };
    }
    return models;
  } catch (error) {
    console.error('[RankedModelSelector] Error fetching ranked models:', error.message);
    // Serve the last good ranking if there is one
    return rankingCache.models || [];
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
    // Last resort: providers use their configured default models
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

/** Test helper: clear the ranking cache */
export function _resetSelectorCache() {
  rankingCache = { models: null, at: 0 };
}

export default {
  fetchRankedModels,
  getModelFallbackChain,
};
