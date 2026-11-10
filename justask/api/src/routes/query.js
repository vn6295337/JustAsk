import express from 'express';
import { validateQuery, validateBatchQueries } from '../middleware/validate.js';
import { classifyQuery } from '../classification/classifier.js';
import { executeWithRankedFallback } from '../failover/failover.js';
import { ipRateLimit } from '../rate-limiting/limiter.js';
import { requireToken } from '../middleware/auth.js';
import config from '../config.js';

// Only one /queue/sync may run at a time (protects provider quota on a
// single instance); extra concurrent syncs get 429.
let activeSyncs = 0;
const MAX_CONCURRENT_SYNCS = 1;

const timeoutSentinel = Symbol('sync-timeout');

const router = express.Router();

/**
 * POST /api/query
 * Process a single query
 * Request: { query: string }
 * Response: { response: string, llm_used: string, category: string, response_time: number }
 */
router.post(
  '/query',
  requireToken,
  ipRateLimit('query', config.inboundLimits.query),
  validateQuery, async (req, res) => {
  const startTime = Date.now();

  try {
    const query = req.validatedQuery;

    // Step 1: Classify query
    const classification = classifyQuery(query);
    console.log(`[Query] Classified as: ${classification.type}`);

    // Step 2: Execute with ranked model fallback (uses pre-computed selection scores)
    console.log(`[Query] Using ranked model fallback chain`);
    const result = await executeWithRankedFallback(query, classification.type);

    if (!result.success) {
      console.error(`[Query] All providers failed:`, result.error);
      const status = result.status === 429 ? 429 : 500;
      return res.status(status).json({
        error: result.error,
        status,
      });
    }

    // Step 3: Return response
    const responseTime = Date.now() - startTime;

    res.json({
      response: result.response,
      llm_used: result.llm_used,
      model_name: result.model_name,
      model_rank: result.model_rank,
      selection_score: result.selection_score,
      category: classification.type,
      response_time: responseTime,
      confidence: classification.confidence,
      failover_count: result.failover_count
    });
  } catch (error) {
    console.error('[Query] Unexpected error:', error);
    const responseTime = Date.now() - startTime;

    res.status(500).json({
      error: 'Internal server error',
      status: 500,
      response_time: responseTime,
    });
  }
});

/**
 * POST /api/queue/sync
 * Sync offline queries when app comes online
 * Request: { queries: [{ id: number, query: string, timestamp: number }] }
 * Response: { responses: [{id: number, response: string, llm_used: string, response_time: number, ...}] }
 */
router.post(
  '/queue/sync',
  requireToken,
  ipRateLimit('sync', config.inboundLimits.sync),
  validateBatchQueries,
  async (req, res) => {
  if (activeSyncs >= MAX_CONCURRENT_SYNCS) {
    res.set('Retry-After', '10');
    return res.status(429).json({
      error: 'A sync is already in progress. Please try again shortly.',
      status: 429,
    });
  }
  activeSyncs++;
  const startTime = Date.now();
  const deadline = startTime + config.sync.timeBudgetMs;

  try {
    const queries = req.validatedQueries;
    const responses = (req.rejectedQueries || []).map((r) => ({
      id: r.id,
      query: r.query,
      success: false,
      permanent: true,
      error: r.reason,
      llm_used: null,
      response_time: 0,
    }));

    console.log(`[Sync] Processing ${queries.length} offline queries`);

    for (const queryItem of queries) {
      const itemStartTime = Date.now();
      const remaining = deadline - itemStartTime;
      if (remaining <= 0) {
        responses.push({
          id: queryItem.id,
          query: queryItem.query,
          success: false,
          retryable: true,
          deferred: true, // never started; no attempt consumed
          error: 'Deferred: sync time budget exceeded',
          llm_used: null,
          response_time: 0,
        });
        continue;
      }
      try {
        const { id, query } = queryItem;

        // Classify and execute with ranked fallback, bounded by remaining budget
        const classification = classifyQuery(query);
        let budgetTimer;
        const result = await Promise.race([
          executeWithRankedFallback(query, classification.type),
          new Promise((resolve) => {
            budgetTimer = setTimeout(() => resolve(timeoutSentinel), remaining);
          }),
        ]).finally(() => clearTimeout(budgetTimer));
        if (result === timeoutSentinel) {
          responses.push({
            id,
            query,
            success: false,
            retryable: true,
            error: 'Deferred: sync time budget exceeded',
            llm_used: null,
            response_time: Date.now() - itemStartTime,
          });
          continue;
        }
        const itemResponseTime = Date.now() - itemStartTime;

        if (result.success) {
          responses.push({
            id: id,
            query: query,
            response: result.response,
            llm_used: result.llm_used,
            category: classification.type,
            response_time: itemResponseTime,
            success: true,
          });
        } else {
          responses.push({
            id: id,
            query: query,
            success: false,
            retryable: true,
            error: result.error,
            llm_used: null,
            response_time: itemResponseTime,
          });
        }
      } catch (error) {
        console.error(`[Sync] Error processing queue ID ${queryItem.id}:`, error.message);
        responses.push({
          id: queryItem.id,
          query: queryItem.query,
          success: false,
          retryable: true,
          error: 'Processing failed',
          llm_used: null,
          response_time: Date.now() - itemStartTime,
        });
      }
    }

    const responseTime = Date.now() - startTime;

    res.json({
      responses: responses,
      synced: responses.filter((r) => r.success).length,
      failed: responses.filter((r) => !r.success).length,
      response_time: responseTime,
    });
  } catch (error) {
    console.error('[Sync] Unexpected error:', error);
    const responseTime = Date.now() - startTime;

    res.status(500).json({
      error: 'Sync failed',
      status: 500,
      response_time: responseTime,
    });
  } finally {
    activeSyncs--;
  }
});

export default router;
