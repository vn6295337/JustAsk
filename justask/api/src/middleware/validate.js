/**
 * Input validation middleware
 * Validates query length, format, and content
 */

const QUERY_MIN_LENGTH = 1;
const QUERY_MAX_LENGTH = 2000;

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
    const dangerousPatterns = [
      /script>/i,           // Script tags
      /<iframe/i,          // IFrames
      /on\w+\s*=/i,        // Event handlers
    ];

    for (const pattern of dangerousPatterns) {
      if (pattern.test(trimmedQuery)) {
        return res.status(400).json({
          error: 'Query contains potentially dangerous content',
          status: 400,
        });
      }
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
    if (queries.length > 100) {
      return res.status(400).json({
        error: 'Cannot sync more than 100 queries at once',
        status: 400,
      });
    }

    // Validate each query
    const validatedQueries = queries.map((item, index) => {
      if (!item.query || typeof item.query !== 'string') {
        throw new Error(`Query ${index} is invalid`);
      }

      const trimmedQuery = item.query.trim();
      if (trimmedQuery.length === 0 || trimmedQuery.length > QUERY_MAX_LENGTH) {
        throw new Error(
          `Query ${index} is invalid (empty or exceeds max length)`
        );
      }

      // Preserve id if provided (for offline queue sync)
      return {
        id: item.id,
        query: trimmedQuery,
        timestamp: item.timestamp || Date.now(),
      };
    });

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
