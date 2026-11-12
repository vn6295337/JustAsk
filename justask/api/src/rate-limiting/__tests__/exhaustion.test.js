import {
  markExhausted,
  isExhausted,
  _resetExhaustion,
  DEFAULT_COOLDOWN_MS,
  MAX_COOLDOWN_MS,
} from '../exhaustion.js';
import { retryAfterMsFrom, toProviderError } from '../../utils/errors.js';

beforeEach(() => _resetExhaustion());

describe('exhaustion memory', () => {
  const t0 = 1_000_000;

  test('uses the provider wait time, then expires', () => {
    markExhausted('groq', 'm', 30_000, t0);
    expect(isExhausted('groq', 'm', t0 + 29_999)).toBe(true);
    expect(isExhausted('groq', 'm', t0 + 30_000)).toBe(false);
  });

  test('defaults to 60 s when the provider gives no wait time', () => {
    expect(markExhausted('groq', 'm', null, t0)).toBe(DEFAULT_COOLDOWN_MS);
  });

  test('caps the wait at 24 h', () => {
    expect(markExhausted('groq', 'm', 10 * MAX_COOLDOWN_MS, t0)).toBe(MAX_COOLDOWN_MS);
  });

  test('is per provider and model', () => {
    markExhausted('groq', 'm', 30_000, t0);
    expect(isExhausted('groq', 'other', t0)).toBe(false);
    expect(isExhausted('openrouter', 'm', t0)).toBe(false);
  });
});

describe('retryAfterMsFrom', () => {
  const now = 1_700_000_000_000;

  test('Retry-After in seconds (axios-style headers)', () => {
    expect(retryAfterMsFrom({ response: { headers: { 'retry-after': '12' } } }, now)).toBe(12_000);
  });

  test('Retry-After as an HTTP date', () => {
    const date = new Date(now + 5000).toUTCString();
    const ms = retryAfterMsFrom({ headers: { 'retry-after': date } }, now);
    expect(ms).toBeGreaterThan(3000);
    expect(ms).toBeLessThanOrEqual(5000);
  });

  test('X-RateLimit-Reset in epoch ms (OpenRouter)', () => {
    const h = new Map([['x-ratelimit-reset', String(now + 3_600_000)]]);
    expect(retryAfterMsFrom({ headers: { get: (k) => h.get(k) } }, now)).toBe(3_600_000);
  });

  test('no headers -> null', () => {
    expect(retryAfterMsFrom(new Error('x'), now)).toBeNull();
  });

  test('toProviderError keeps the wait time', () => {
    const e = toProviderError('openrouter', { message: 'rate', response: { status: 429, headers: { 'retry-after': '7' } } });
    expect(e.status).toBe(429);
    expect(e.retryAfterMs).toBe(7000);
  });
});
