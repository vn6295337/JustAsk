import config from '../config.js';

/**
 * In-memory rate limiter
 * Tracks requests per provider with 1-minute rolling windows
 */

class RateLimiter {
  constructor() {
    // {provider: {count: number, windowStart: timestamp}}
    this.providers = {};

    // Initialize provider tracking
    for (const [provider, limit] of Object.entries(config.rateLimits)) {
      this.providers[provider] = {
        count: 0,
        windowStart: Date.now(),
        limit: limit,
      };
    }

    // Per-key (e.g. client IP) counters: key -> {count, windowStart}
    this.keys = new Map();

    // Reset counts every minute
    const timer = setInterval(() => {
      this.resetWindows();
      this.pruneKeys();
    }, 60000);
    if (timer.unref) timer.unref();
  }

  /**
   * Drop expired per-key windows
   */
  pruneKeys() {
    const now = Date.now();
    for (const [key, data] of this.keys) {
      if (now - data.windowStart > 60000) this.keys.delete(key);
    }
  }

  /**
   * Fixed-window check for an arbitrary key (client IP + route bucket).
   * @returns {{allowed: boolean, retryAfter?: number}}
   */
  checkKey(key, limit) {
    const now = Date.now();
    let data = this.keys.get(key);
    if (!data || now - data.windowStart >= 60000) {
      data = { count: 0, windowStart: now };
      this.keys.set(key, data);
    }
    if (data.count >= limit) {
      return {
        allowed: false,
        retryAfter: Math.max(1, Math.ceil((60000 - (now - data.windowStart)) / 1000)),
      };
    }
    data.count++;
    // Hard cap on memory: evict oldest if map grows too large
    if (this.keys.size > 10000) {
      this.keys.delete(this.keys.keys().next().value);
    }
    return { allowed: true };
  }

  /**
   * Reset all provider windows
   */
  resetWindows() {
    const now = Date.now();
    for (const provider in this.providers) {
      this.providers[provider].count = 0;
      this.providers[provider].windowStart = now;
    }
    console.log('[RateLimiter] Windows reset');
  }

  /**
   * Check if request is allowed for provider
   * @param {string} provider - Provider name
   * @returns {object} {allowed: boolean, retryAfter: number}
   */
  checkRateLimit(provider) {
    if (!this.providers[provider]) {
      return {
        allowed: false,
        error: `Unknown provider: ${provider}`,
        retryAfter: null,
      };
    }

    const providerData = this.providers[provider];
    const now = Date.now();
    const windowAge = now - providerData.windowStart;

    // Reset window if expired
    if (windowAge > 60000) {
      providerData.count = 0;
      providerData.windowStart = now;
    }

    // Check if rate limit exceeded
    if (providerData.count >= providerData.limit) {
      const retryAfter = Math.ceil((60000 - windowAge) / 1000);
      return {
        allowed: false,
        error: `Rate limit exceeded for ${provider} (${providerData.limit} req/min)`,
        retryAfter: Math.max(1, retryAfter),
      };
    }

    // Increment counter
    providerData.count++;

    return {
      allowed: true,
      remaining: providerData.limit - providerData.count,
      resetIn: Math.ceil((60000 - windowAge) / 1000),
    };
  }

  /**
   * Get current status for all providers
   */
  getStatus() {
    const status = {};
    for (const provider in this.providers) {
      const data = this.providers[provider];
      const windowAge = Date.now() - data.windowStart;
      const resetIn = Math.ceil((60000 - windowAge) / 1000);

      status[provider] = {
        count: data.count,
        limit: data.limit,
        remaining: Math.max(0, data.limit - data.count),
        resetIn: Math.max(0, resetIn),
      };
    }
    return status;
  }

  /**
   * Test rate limiter
   */
  testRateLimiter() {
    console.log('Testing Rate Limiter:');

    // Test Groq limit (30 req/min)
    const groqLimit = config.rateLimits.groq || 30;
    console.log(`Groq limit: ${groqLimit} req/min`);

    // Simulate requests
    for (let i = 0; i < groqLimit + 5; i++) {
      const result = this.checkRateLimit('groq');
      if (i === groqLimit - 1) {
        console.log(
          `✅ Request ${i + 1}: Allowed (${result.remaining} remaining)`
        );
      } else if (i === groqLimit) {
        console.log(
          `❌ Request ${i + 1}: Blocked (retry after ${result.retryAfter}s)`
        );
      }
    }

    console.log('Rate limiter status:', this.getStatus());
    return true;
  }
}

// Singleton instance
let limiterInstance = null;

/**
 * Get or create rate limiter instance
 */
export const getLimiter = () => {
  if (!limiterInstance) {
    limiterInstance = new RateLimiter();
  }
  return limiterInstance;
};

/**
 * Check rate limit (convenience function)
 */
export const checkRateLimit = (provider) => {
  return getLimiter().checkRateLimit(provider);
};

/**
 * Get limiter status
 */
export const getStatus = () => {
  return getLimiter().getStatus();
};

/**
 * Express middleware: per-IP inbound rate limit.
 * @param {string} bucket - Route bucket name
 * @param {number} limit - Max requests per minute per IP
 */
export const ipRateLimit = (bucket, limit) => (req, res, next) => {
  const ip = req.ip || req.socket?.remoteAddress || 'unknown';
  const result = getLimiter().checkKey(`${bucket}:${ip}`, limit);
  if (!result.allowed) {
    res.set('Retry-After', String(result.retryAfter));
    return res.status(429).json({
      error: 'Too many requests. Please try again later.',
      status: 429,
    });
  }
  next();
};

export { RateLimiter };

export default {
  RateLimiter,
  getLimiter,
  checkRateLimit,
  getStatus,
};
