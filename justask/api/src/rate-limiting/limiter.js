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

    // Reset counts every minute
    setInterval(() => this.resetWindows(), 60000);
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

export { RateLimiter };

export default {
  RateLimiter,
  getLimiter,
  checkRateLimit,
  getStatus,
};
