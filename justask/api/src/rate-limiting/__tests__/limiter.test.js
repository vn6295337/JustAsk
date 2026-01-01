import { RateLimiter, checkRateLimit, getStatus } from '../limiter.js';
import config from '../../config.js';

describe('Rate Limiter', () => {
  let limiter;

  beforeEach(() => {
    // Create fresh limiter instance for each test
    limiter = new RateLimiter();
  });

  describe('Initialization', () => {
    test('should initialize with correct provider limits', () => {
      const status = limiter.getStatus();
      expect(status.gemini.limit).toBe(config.rateLimits.gemini);
      expect(status.groq.limit).toBe(config.rateLimits.groq);
      expect(status.openrouter.limit).toBe(config.rateLimits.openrouter);
    });

    test('should initialize with zero requests', () => {
      const status = limiter.getStatus();
      expect(status.gemini.count).toBe(0);
      expect(status.groq.count).toBe(0);
      expect(status.openrouter.count).toBe(0);
    });
  });

  describe('Rate Limiting - Allowed Requests', () => {
    test('should allow first request for Groq (30 req/min)', () => {
      const result = limiter.checkRateLimit('groq');
      expect(result.allowed).toBe(true);
      expect(result.remaining).toBe(config.rateLimits.groq - 1);
    });

    test('should allow first request for Gemini (60 req/min)', () => {
      const result = limiter.checkRateLimit('gemini');
      expect(result.allowed).toBe(true);
      expect(result.remaining).toBe(config.rateLimits.gemini - 1);
    });

    test('should increment counter on subsequent allowed requests', () => {
      limiter.checkRateLimit('groq');
      const result1 = limiter.checkRateLimit('groq');
      expect(result1.remaining).toBe(config.rateLimits.groq - 2);

      const result2 = limiter.checkRateLimit('groq');
      expect(result2.remaining).toBe(config.rateLimits.groq - 3);
    });
  });

  describe('Rate Limiting - Rate Limit Exceeded', () => {
    test('should block when Groq limit (30) is exceeded', () => {
      const limit = config.rateLimits.groq;

      // Make 30 allowed requests
      for (let i = 0; i < limit; i++) {
        const result = limiter.checkRateLimit('groq');
        expect(result.allowed).toBe(true);
      }

      // 31st request should be blocked
      const blocked = limiter.checkRateLimit('groq');
      expect(blocked.allowed).toBe(false);
      expect(blocked.error).toContain('Rate limit exceeded');
      expect(blocked.retryAfter).toBeLessThanOrEqual(60);
      expect(blocked.retryAfter).toBeGreaterThan(0);
    });

    test('should provide retryAfter value when rate limited', () => {
      const limit = config.rateLimits.groq;

      // Exhaust limit
      for (let i = 0; i < limit; i++) {
        limiter.checkRateLimit('groq');
      }

      // Try to exceed
      const result = limiter.checkRateLimit('groq');
      expect(result.retryAfter).toBeDefined();
      expect(typeof result.retryAfter).toBe('number');
    });
  });

  describe('Independent Provider Limits', () => {
    test('Groq limit should not affect Gemini', () => {
      const groqLimit = config.rateLimits.groq;

      // Exhaust Groq limit
      for (let i = 0; i < groqLimit; i++) {
        limiter.checkRateLimit('groq');
      }

      // Groq should be blocked
      const grRes = limiter.checkRateLimit('groq');
      expect(grRes.allowed).toBe(false);

      // Gemini should still be allowed
      const geRes = limiter.checkRateLimit('gemini');
      expect(geRes.allowed).toBe(true);
    });

    test('each provider maintains its own counter', () => {
      limiter.checkRateLimit('groq');
      limiter.checkRateLimit('groq');
      limiter.checkRateLimit('gemini');

      const status = limiter.getStatus();
      expect(status.groq.count).toBe(2);
      expect(status.gemini.count).toBe(1);
    });
  });

  describe('Status Reporting', () => {
    test('should report correct remaining count', () => {
      limiter.checkRateLimit('groq');
      limiter.checkRateLimit('groq');

      const status = limiter.getStatus();
      expect(status.groq.remaining).toBe(config.rateLimits.groq - 2);
    });

    test('should report resetIn time', () => {
      const status = limiter.getStatus();
      expect(status.groq.resetIn).toBeLessThanOrEqual(60);
      expect(status.groq.resetIn).toBeGreaterThan(0);
    });

    test('should report status for all providers', () => {
      const status = limiter.getStatus();
      expect(status.gemini).toBeDefined();
      expect(status.groq).toBeDefined();
      expect(status.openrouter).toBeDefined();
    });
  });

  describe('Error Handling', () => {
    test('should handle unknown provider gracefully', () => {
      const result = limiter.checkRateLimit('unknown_provider');
      expect(result.allowed).toBe(false);
      expect(result.error).toContain('Unknown provider');
    });

    test('should not crash on invalid input', () => {
      const result1 = limiter.checkRateLimit(null);
      expect(result1.allowed).toBe(false);

      const result2 = limiter.checkRateLimit(undefined);
      expect(result2.allowed).toBe(false);
    });
  });
});
