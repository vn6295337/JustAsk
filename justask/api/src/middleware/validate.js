/**
 * Input validation middleware
 * Validates query length, format, and content
 */

const QUERY_MIN_LENGTH = 1;
import config from '../config.js';

const QUERY_MAX_LENGTH = 2000;

// Event-handler attributes only count inside a tag ("region=EU" is fine);
// "script>" only counts as a tag ("transcript>" is fine).
const DANGEROUS_PATTERNS = [
  /<\s*\/?\s*script\b/i,
  /<\s*iframe\b/i,
  /<[^>]*\bon[a-z]+\s*=/i,
];

export const hasDangerousContent = (text) =>
  DANGEROUS_PATTERNS.some((pattern) => pattern.test(text));

/**
 * Validate query input
 * - Non-empty and non-whitespace
 * - Length between 1-2000 characters
 * - No dangerous patterns
 */
export const validateQuery = (req, res, next) => {
  try {
    const { query } = req.body;

    // Check if query exists
    if (!query) {
      return res.status(400).json({
        error: 'Query is required',
        status: 400,
      });
    }

    // Check if query is string
    if (typeof query !== 'string') {
      return res.status(400).json({
        error: 'Query must be a string',
        status: 400,
      });
    }

    // Trim and check if empty after trimming
    const trimmedQuery = query.trim();
    if (trimmedQuery.length === 0) {
      return res.status(400).json({
        error: 'Query cannot be empty or whitespace only',
        status: 400,
      });
    }

    // Check minimum length
    if (trimmedQuery.length < QUERY_MIN_LENGTH) {
      return res.status(400).json({
        error: `Query must be at least ${QUERY_MIN_LENGTH} character`,
        status: 400,
      });
    }

    // Check maximum length
    if (trimmedQuery.length > QUERY_MAX_LENGTH) {
      return res.status(400).json({
        error: `Query cannot exceed ${QUERY_MAX_LENGTH} characters (received ${trimmedQuery.length})`,
        status: 400,
      });
    }

    // Optional: Reject obviously malicious patterns
    // (This is a basic check; real security requires more)
    if (hasDangerousContent(trimmedQuery)) {
      return res.status(400).json({
        error: 'Query contains potentially dangerous content',
        status: 400,
      });
    }

    // Attach validated query to request
    req.validatedQuery = trimmedQuery;
    next();
  } catch (error) {
    console.error('Validation error:', error);
    res.status(400).json({
      error: 'Invalid request format',
      status: 400,
    });
  }
};

/**
 * Validate batch queries for offline sync
 */
export const validateBatchQueries = (req, res, next) => {
  try {
    const { queries } = req.body;

    // Check if queries array exists
    if (!Array.isArray(queries)) {
      return res.status(400).json({
        error: 'Queries must be an array',
        status: 400,
      });
    }

    // Check if array is not empty
    if (queries.length === 0) {
      return res.status(400).json({
        error: 'Queries array cannot be empty',
        status: 400,
      });
    }

    // Check if array doesn't exceed reasonable limit (prevent abuse)
    const maxBatch = config.sync.maxBatch;
    if (queries.length > maxBatch) {
      return res.status(400).json({
        error: `Cannot sync more than ${maxBatch} queries at once`,
        status: 400,
      });
    }

    // Structural problems (not an object / no string query) reject the batch.
    // Content problems (empty, too long, dangerous) reject only that item so
    // one bad queued entry cannot block the rest.
    const validatedQueries = [];
    const rejectedQueries = [];

    queries.forEach((item, index) => {
      if (!item || typeof item !== 'object' || !item.query || typeof item.query !== 'string') {
        throw new Error(`Query ${index} is invalid`);
      }

      const trimmedQuery = item.query.trim();
      let reason = null;
      if (trimmedQuery.length === 0 || trimmedQuery.length > QUERY_MAX_LENGTH) {
        reason = 'Query is empty or exceeds max length';
      } else if (hasDangerousContent(trimmedQuery)) {
        reason = 'Query contains potentially dangerous content';
      }

      if (reason) {
        rejectedQueries.push({ id: item.id, query: trimmedQuery.slice(0, QUERY_MAX_LENGTH), reason });
        return;
      }

      // Preserve id if provided (for offline queue sync)
      validatedQueries.push({
        id: item.id,
        query: trimmedQuery,
        timestamp: item.timestamp || Date.now(),
      });
    });

    req.rejectedQueries = rejectedQueries;
    req.validatedQueries = validatedQueries;
    next();
  } catch (error) {
    console.error('Batch validation error:', error);
    res.status(400).json({
      error: error.message || 'Invalid batch request format',
      status: 400,
    });
  }
};

export default {
  validateQuery,
  validateBatchQueries,
};
