import express from 'express';
import { validateQuery, validateBatchQueries } from '../middleware/validate.js';
import { classifyQuery } from '../classification/classifier.js';
import { executeWithRankedFallback } from '../failover/failover.js';

const router = express.Router();

/**
 * POST /api/query
 * Process a single query
 * Request: { query: string }
 * Response: { response: string, llm_used: string, category: string, response_time: number }
 */
router.post('/query', validateQuery, async (req, res) => {
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
      return res.status(500).json({
        error: result.error,
        status: 500,
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
      error: error.message || 'Internal server error',
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
router.post('/queue/sync', validateBatchQueries, async (req, res) => {
  const startTime = Date.now();

  try {
    const queries = req.validatedQueries;
    const responses = [];

    console.log(`[Sync] Processing ${queries.length} offline queries`);

    for (const queryItem of queries) {
      const itemStartTime = Date.now();
      try {
        const { id, query } = queryItem;

        // Classify and execute with ranked fallback
        const classification = classifyQuery(query);
        const result = await executeWithRankedFallback(query, classification.type);
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
          error: error.message || 'Unknown error',
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

    res.status(400).json({
      error: error.message || 'Invalid sync request',
      status: 400,
      response_time: responseTime,
    });
  }
});

export default router;
