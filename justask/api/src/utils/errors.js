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
 * Wrap any upstream error as a ProviderError.
 */
export const toProviderError = (provider, error) => {
  if (error instanceof ProviderError) return error;
  return new ProviderError(provider, error?.message, normalizeStatus(error));
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
