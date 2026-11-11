/**
 * Error thrown by provider adapters. Preserves HTTP status and a message;
 * the message is for server logs only and must not be returned to clients.
 */
export class ProviderError extends Error {
  constructor(provider, message, status = 502) {
    super(message || 'Provider error');
    this.name = 'ProviderError';
    this.provider = provider;
    this.status = status;
  }
}

/**
 * Normalize an arbitrary upstream error into a numeric HTTP status.
 */
export const normalizeStatus = (error) => {
  const raw = error?.response?.status ?? error?.status;
  if (Number.isInteger(raw) && raw >= 400 && raw <= 599) return raw;
  const code = error?.code;
  if (
    code === 'ECONNABORTED' ||
    code === 'ETIMEDOUT' ||
    code === 'PROVIDER_TIMEOUT' ||
    error?.name === 'AbortError' ||
    error?.name === 'TimeoutError' ||
    /timed? ?out/i.test(error?.message || '')
  ) {
    return 504;
  }
  return 502;
};

/**
 * How long a provider asked us to wait, in ms, from its response headers:
 * Retry-After (seconds or HTTP date), or X-RateLimit-Reset (epoch ms or s,
 * as sent by OpenRouter). Returns null if neither is present or parseable.
 */
export const retryAfterMsFrom = (error, now = Date.now()) => {
  const h = error?.response?.headers || error?.headers;
  if (!h) return null;
  const get = (k) => (typeof h.get === 'function' ? h.get(k) : h[k] ?? h[k.toLowerCase()]);

  const ra = get('retry-after');
  if (ra != null && ra !== '') {
    const secs = Number(ra);
    if (Number.isFinite(secs) && secs >= 0) return secs * 1000;
    const date = Date.parse(ra);
    if (!Number.isNaN(date)) return Math.max(0, date - now);
  }

  const reset = Number(get('x-ratelimit-reset'));
  if (Number.isFinite(reset) && reset > 0) {
    if (reset > 1e12) return Math.max(0, reset - now); // epoch ms
    if (reset > 1e9) return Math.max(0, reset * 1000 - now); // epoch s
  }
  return null;
};

/**
 * Wrap any upstream error as a ProviderError.
 */
export const toProviderError = (provider, error) => {
  if (error instanceof ProviderError) return error;
  const wrapped = new ProviderError(provider, error?.message, normalizeStatus(error));
  wrapped.retryAfterMs = retryAfterMsFrom(error);
  return wrapped;
};

/**
 * Reject if promise does not settle within ms.
 */
export const withTimeout = (promise, ms, provider) => {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => {
      const e = new ProviderError(provider, `${provider} request timed out after ${ms}ms`, 504);
      e.code = 'PROVIDER_TIMEOUT';
      reject(e);
    }, ms);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
};
