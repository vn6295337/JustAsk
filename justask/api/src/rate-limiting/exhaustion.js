/**
 * Remembers models that answered "limit reached" (HTTP 429) so the failover
 * loop skips them until their limit resets, instead of trying them first on
 * every request. In memory: a restart forgets, which only costs one extra try.
 */
export const DEFAULT_COOLDOWN_MS = 60 * 1000;
export const MAX_COOLDOWN_MS = 24 * 60 * 60 * 1000;
const MIN_COOLDOWN_MS = 1000;

const exhaustedUntil = new Map();

export const modelKey = (provider, modelName) => `${provider}:${modelName || 'default'}`;

/**
 * Mark a model as out of quota.
 * @param {number|null} retryAfterMs - from the provider's headers; default 60 s
 * @returns {number} cooldown applied, in ms
 */
export const markExhausted = (provider, modelName, retryAfterMs = null, now = Date.now()) => {
  const ms = Math.min(
    MAX_COOLDOWN_MS,
    Math.max(MIN_COOLDOWN_MS, Number.isFinite(retryAfterMs) ? retryAfterMs : DEFAULT_COOLDOWN_MS)
  );
  exhaustedUntil.set(modelKey(provider, modelName), now + ms);
  return ms;
};

export const isExhausted = (provider, modelName, now = Date.now()) => {
  const key = modelKey(provider, modelName);
  const until = exhaustedUntil.get(key);
  if (!until) return false;
  if (until <= now) {
    exhaustedUntil.delete(key);
    return false;
  }
  return true;
};

/** Test helper */
export const _resetExhaustion = () => exhaustedUntil.clear();

export default { markExhausted, isExhausted, modelKey };
