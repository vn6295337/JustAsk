/**
 * Intelligent Model Selector Service
 * Express API server for dynamic AI model selection
 */

import 'dotenv/config'; // must load before modules that read process.env at import time
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { selectModel } from './services/modelSelector.js';
import cacheManager from './services/cacheManager.js';
import rateLimitTracker from './utils/rateLimitTracker.js';
import { initializeScores } from './services/intelligenceIndex.js';
import supabase, { fetchLatestModels, testConnection } from './utils/supabase.js';
import { CACHE_TTLS } from './config/constants.js';
import { adminAuth, buildCorsOptions } from './middleware/adminAuth.js';
import { validateSelectRequest, parseIntParam } from './utils/validation.js';

const app = express();
const PORT = process.env.PORT || 3001;
const startTime = Date.now();

// Middleware
app.use(helmet());
app.use(cors(buildCorsOptions()));
app.use(express.json());
app.use(morgan(process.env.NODE_ENV === 'production' ? 'combined' : 'dev'));

// Health check endpoint (minimal: no per-model limits/usage or cache keys)
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: (Date.now() - startTime) / 1000
  });
});

// Get all available models
app.get('/models', async (req, res) => {
  try {
    const models = await cacheManager.getOrFetch(
      'models',
      fetchLatestModels,
      CACHE_TTLS.models
    );

    const cacheAge = cacheManager.getAge('models');

    res.json({
      models,
      count: models.length,
      cached: cacheAge > 0,
      cacheAge: cacheAge > 0 ? Math.round(cacheAge / 1000) + 's' : null,
      lastUpdate: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching models:', error);
    res.status(500).json({
      error: 'Failed to fetch models',
      message: error.message
    });
  }
});

// MVP: Get best model by Intelligence Index
// Uses the same joined data as /select-model (justask."11_free-models-live" ->
// justask."21_router-model-benchmark-map" -> justask."20_router-benchmark-scores") via fetchLatestModels.
app.get('/best-model', async (req, res) => {
  try {
    const { provider } = req.query;
    if (provider !== undefined && typeof provider !== 'string') {
      return res.status(400).json({ error: 'provider must be a string', code: 'INVALID_REQUEST' });
    }

    const all = await cacheManager.getOrFetch(
      'models',
      fetchLatestModels,
      CACHE_TTLS.models
    );

    const models = (all || []).filter(m =>
      !provider || (m.inference_provider || '').toLowerCase() === provider.toLowerCase()
    );

    if (models.length === 0) {
      return res.status(404).json({
        error: 'No models found matching criteria',
        code: 'NO_MODELS_AVAILABLE',
        criteria: { provider: provider || 'all' }
      });
    }

    const modelsWithMetrics = models
      .filter(m => m.aa_performance_metrics && m.aa_performance_metrics.intelligence_index != null)
      .sort((a, b) =>
        b.aa_performance_metrics.intelligence_index - a.aa_performance_metrics.intelligence_index);

    if (modelsWithMetrics.length === 0) {
      return res.status(404).json({
        error: 'No models found with intelligence index',
        code: 'NO_MODELS_AVAILABLE',
        criteria: { provider: provider || 'all' }
      });
    }

    const modelData = modelsWithMetrics[0];
    const metrics = modelData.aa_performance_metrics;

    res.json({
      model: {
        provider: modelData.inference_provider,
        modelSlug: metrics.aa_slug,
        humanReadableName: modelData.human_readable_name,
        intelligenceIndex: metrics.intelligence_index,
        codingIndex: metrics.coding_index
      },
      selectionCriteria: {
        method: 'intelligence_index',
        filterProvider: provider || 'all'
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Best model selection error:', error);
    res.status(500).json({
      error: 'Failed to select best model',
      message: error.message,
      code: 'SELECTION_ERROR'
    });
  }
});

// Get top N models from pre-computed selection scores
app.get('/best-models', async (req, res) => {
  try {
    const { provider } = req.query;
    const limitNum = parseIntParam(req.query.limit, 1, 50, 5);

    if (limitNum === null || (provider !== undefined && typeof provider !== 'string')) {
      return res.status(400).json({
        error: 'limit must be an integer between 1 and 50 and provider must be a string',
        code: 'INVALID_REQUEST'
      });
    }

    // Use 23_router-model-ranking for pre-computed rankings
    let query = supabase
      .schema('justask')
      .from('23_router-model-ranking')
      .select('model_name, inference_provider, provider_slug, intelligence_index, selection_score, rpm_limit, overall_headroom, latency_score')
      .order('selection_score', { ascending: false })
      .limit(limitNum);

    if (provider) {
      query = query.eq('inference_provider', provider);
    }

    const { data: models, error: modelsError } = await query;

    if (modelsError) {
      throw new Error(`Database query failed: ${modelsError.message}`);
    }

    if (!models || models.length === 0) {
      return res.status(404).json({
        error: 'No models found',
        code: 'NO_MODELS_AVAILABLE',
        criteria: { provider: provider || 'all', limit: limitNum }
      });
    }

    res.json({
      models: models.map((m, index) => ({
        rank: index + 1,
        provider: m.inference_provider,
        modelName: m.provider_slug,
        humanReadableName: m.model_name,
        selectionScore: m.selection_score,
        intelligenceIndex: m.intelligence_index,
        latencyScore: m.latency_score,
        headroom: m.overall_headroom,
        rpmLimit: m.rpm_limit
      })),
      count: models.length,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Best models query error:', error);
    res.status(500).json({
      error: 'Failed to retrieve best models',
      message: error.message,
      code: 'QUERY_ERROR'
    });
  }
});

// Select optimal model
app.post('/select-model', async (req, res) => {
  try {
    const validated = validateSelectRequest(req.body);
    if (validated.error) {
      return res.status(400).json({ error: validated.error, code: 'INVALID_REQUEST' });
    }
    const { queryType, queryText, modalities, complexityScore } = validated.value;

    // Select model
    const startTime = Date.now();
    const selection = await selectModel({
      queryType,
      queryText,
      modalities,
      complexityScore
    });

    const duration = Date.now() - startTime;

    // Log selection
    console.log('Model selected:', {
      provider: selection.provider,
      modelName: selection.modelName,
      score: selection.score,
      headroom: selection.rateLimitHeadroom,
      duration: duration + 'ms'
    });

    res.json({
      ...selection,
      selectionDuration: duration
    });
  } catch (error) {
    console.error('Model selection error:', error);

    if (error.message.includes('No models')) {
      return res.status(500).json({
        error: error.message,
        code: 'NO_MODELS_AVAILABLE',
        details: {
          queryType: typeof req.body?.queryType === 'string' ? req.body.queryType : undefined
        }
      });
    }

    res.status(500).json({
      error: 'Model selection failed',
      message: error.message,
      code: 'SELECTION_ERROR'
    });
  }
});

// Manually refresh cache
app.post('/cache/refresh', adminAuth, async (req, res) => {
  try {
    // Fetch first; the cache is only replaced on success (old data survives a failure)
    const models = await cacheManager.refresh('models', fetchLatestModels, CACHE_TTLS.models);

    res.json({
      message: 'Cache refreshed',
      timestamp: new Date().toISOString(),
      modelCount: models.length
    });
  } catch (error) {
    console.error('Cache refresh error:', error);
    res.status(500).json({
      error: 'Cache refresh failed',
      message: error.message
    });
  }
});

// Reset rate limit counters (for testing)
app.post('/rate-limits/reset', adminAuth, (req, res) => {
  rateLimitTracker.resetAll();

  res.json({
    message: 'Rate limit counters reset',
    timestamp: new Date().toISOString()
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);

  res.status(500).json({
    error: 'Internal server error',
    message: err.message,
    code: 'INTERNAL_ERROR'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not found',
    code: 'NOT_FOUND',
    path: req.path
  });
});

// Start server
async function startServer() {
  try {
    // Test Supabase connection
    console.log('Testing Supabase connection...');
    const connected = await testConnection();

    if (!connected) {
      console.error('Failed to connect to Supabase. Check your credentials.');
      process.exit(1);
    }

    console.log('✓ Supabase connection successful');

    // Initialize Intelligence Index scores
    console.log('Initializing Intelligence Index...');
    await initializeScores();
    console.log('✓ Intelligence Index initialized');

    // Pre-warm cache
    console.log('Pre-warming cache...');
    const models = await fetchLatestModels();
    cacheManager.set('models', models, CACHE_TTLS.models);
    console.log(`✓ Cached ${models.length} models`);

    // Start listening
    app.listen(PORT, () => {
      console.log(`\n🚀 Intelligent Model Selector running on port ${PORT}`);
      console.log(`   Health check: http://localhost:${PORT}/health`);
      console.log(`   Environment: ${process.env.NODE_ENV || 'development'}\n`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();

export default app;
