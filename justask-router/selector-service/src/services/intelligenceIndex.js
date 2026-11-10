/**
 * Intelligence Index Service - Artificial Analysis API Integration
 *
 * Fetches model performance scores from Artificial Analysis API
 * Caches results for 7 days to minimize API calls
 * Provides fallback scoring when API unavailable
 */

import cacheManager from './cacheManager.js';
import { MODEL_SIZE_SCORES, CACHE_TTLS } from '../config/constants.js';

const API_BASE_URL = 'https://artificialanalysis.ai/api/v2';

/**
 * Get API key from environment variables
 * @returns {string|undefined} API key
 * @private
 */
function getApiKey() {
  return process.env.ARTIFICIALANALYSIS_API_KEY || process.env.ARTIFICIAL_ANALYSIS_API_KEY;
}

/**
 * Fetch Intelligence Index scores for all models
 * @returns {Promise<Object>} Map of model names to intelligence scores
 */
export async function fetchIntelligenceScores() {
  // Check cache first (expired entries are not returned)
  const cached = await cacheManager.get('intelligenceIndex');
  if (cached) {
    console.log('Intelligence Index: Using cached scores');
    return cached;
  }

  // Share one in-flight fetch between concurrent callers
  if (!inflightFetch) {
    inflightFetch = loadScores().finally(() => {
      inflightFetch = null;
    });
  }
  return inflightFetch;
}

let inflightFetch = null;

async function loadScores() {
  const apiKey = getApiKey();
  if (apiKey && apiKey !== 'your-api-key-here') {
    try {
      const scores = await fetchFromAPI();

      // Cache for 7 days
      await cacheManager.set('intelligenceIndex', scores, CACHE_TTLS.intelligenceIndex);

      console.log(`Intelligence Index: Fetched ${Object.keys(scores).length} model scores from API`);
      return scores;
    } catch (error) {
      console.warn('Intelligence Index: API fetch failed, using fallback', error.message);
    }
  } else {
    console.log('Intelligence Index: No API key configured, using fallback scoring');
  }

  // Failure: keep serving stale scores if any, else empty map (size-based fallback).
  // Negative-cache briefly so a failing API is not hit on every request.
  const stale = await cacheManager.get('intelligenceIndex', { allowStale: true });
  const fallback = stale || {};
  await cacheManager.set('intelligenceIndex', fallback, CACHE_TTLS.negative);
  return fallback;
}

/**
 * Fetch scores from Artificial Analysis API
 * @returns {Promise<Object>} Map of model names to scores
 * @private
 */
async function fetchFromAPI() {
  const url = `${API_BASE_URL}/data/llms/models`;

  const apiKey = getApiKey();
  const response = await fetch(url, {
    headers: {
      'x-api-key': apiKey,
      'Accept': 'application/json'
    }
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API request failed: ${response.status} - ${error}`);
  }

  // Check rate limit headers
  const rateLimitRemaining = response.headers.get('X-RateLimit-Remaining');
  if (rateLimitRemaining) {
    console.log(`Artificial Analysis API: ${rateLimitRemaining} requests remaining`);
  }

  const data = await response.json();

  if (!data.data || !Array.isArray(data.data)) {
    throw new Error('Invalid API response format');
  }

  // Parse scores into map
  return parseScores(data.data);
}

/**
 * Parse API response into model name -> score map
 * @param {Array} models - Array of model data from API
 * @returns {Object} Map of model names to normalized scores
 * @private
 */
function parseScores(models) {
  const scores = {};

  models.forEach(model => {
    // Use slug as the key (exact format from API)
    const slug = model.slug;

    if (!slug) return;

    // Get Intelligence Index score (primary metric)
    // API structure: model.evaluations.artificial_analysis_intelligence_index
    const evaluations = model.evaluations || {};
    let score = evaluations.artificial_analysis_intelligence_index;

    // If Intelligence Index not available, try other metrics
    if (score === null || score === undefined) {
      // Use average of available benchmarks
      const benchmarks = [
        evaluations.mmlu_pro,
        evaluations.gpqa,
        evaluations.artificial_analysis_coding_index,
        evaluations.artificial_analysis_math_index
      ].filter(v => v !== null && v !== undefined);

      if (benchmarks.length > 0) {
        score = benchmarks.reduce((sum, v) => sum + v, 0) / benchmarks.length;
      }
    }

    // Normalize score to 0-1 range
    // Intelligence Index is typically 0-100
    if (score !== null && score !== undefined) {
      // Store with exact slug as key (e.g., "gemini-2-5-flash", "gemma-3-27b")
      scores[slug] = normalizeScore(score);
    }
  });

  return scores;
}

/**
 * Normalize score to 0-1 range
 * @param {number} score - Raw score (typically 0-100)
 * @returns {number} Normalized score (0-1)
 * @private
 */
function normalizeScore(score) {
  // Intelligence Index is typically 0-100
  if (score >= 0 && score <= 1) {
    // Already normalized
    return score;
  }

  if (score > 1 && score <= 100) {
    // Normalize from 0-100 to 0-1
    return score / 100;
  }

  // Cap at 1.0
  return Math.min(1.0, score);
}

/**
 * Get intelligence score for a specific model
 * @param {Object} model - Model object from database
 * @param {Object} scoresMap - Map of slugs to scores from Artificial Analysis API
 * @returns {number} Intelligence score (0-1)
 */
export function getModelScore(model, scoresMap = {}) {
  if (!model) {
    return calculateFallbackScore(model);
  }

  const map = scoresMap || {};
  const metrics = model.aa_performance_metrics || null;

  // The scores map is keyed by Artificial Analysis slug. Resolve the model's AA slug
  // through the mapping (ims.10_model_aa_mapping), never via human_readable_name.
  const aaSlug = model.aa_slug || metrics?.aa_slug || null;

  if (aaSlug && map[aaSlug] != null) {
    return map[aaSlug];
  }

  // Mapped metrics joined at fetch time (ims.20_aa_performance_metrics)
  if (metrics && typeof metrics.intelligence_index === 'number' && Number.isFinite(metrics.intelligence_index)) {
    return normalizeScore(metrics.intelligence_index);
  }

  // Fallback to size-based scoring if no mapped score
  return calculateFallbackScore(model);
}

/**
 * Calculate fallback score based on model size
 * @param {Object} model - Model object
 * @returns {number} Fallback score (0-1)
 */
export function calculateFallbackScore(model) {
  if (!model || typeof model.human_readable_name !== 'string') {
    return 0.6; // Default moderate score
  }

  const modelName = model.human_readable_name.toLowerCase();

  // Try to extract model size from name
  // Match the size as a whole token so "qwen3-32b" does not hit "2b" and
  // "llama-3.2-11b" does not hit "1b"
  for (const [size, score] of Object.entries(MODEL_SIZE_SCORES)) {
    const re = new RegExp(`(?<![a-z0-9.])${size}(?![a-z0-9])`);
    if (re.test(modelName)) {
      return score;
    }
  }

  // Default moderate score
  return 0.6;
}

/**
 * Initialize intelligence index scores on service startup
 * @returns {Promise<void>}
 */
export async function initializeScores() {
  try {
    const scores = await fetchIntelligenceScores();
    console.log(`Intelligence Index: Initialized with ${Object.keys(scores).length} model scores`);
  } catch (error) {
    console.error('Intelligence Index: Initialization failed', error.message);
    // Continue with fallback scoring
  }
}

export default {
  fetchIntelligenceScores,
  getModelScore,
  calculateFallbackScore,
  initializeScores
};
