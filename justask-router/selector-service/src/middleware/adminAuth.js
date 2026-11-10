/**
 * Admin auth middleware - shared secret in X-Admin-Token header.
 * 503 if ADMIN_TOKEN is not configured, 401 if missing/invalid.
 */

import crypto from 'crypto';

function digest(value) {
  return crypto.createHash('sha256').update(String(value)).digest();
}

export function tokensMatch(provided, expected) {
  if (typeof provided !== 'string' || !expected) return false;
  // Hash both sides so lengths are equal and the compare is constant-time
  return crypto.timingSafeEqual(digest(provided), digest(expected));
}

export function adminAuth(req, res, next) {
  const expected = process.env.ADMIN_TOKEN;

  if (!expected) {
    return res.status(503).json({
      error: 'Admin endpoints disabled: ADMIN_TOKEN not configured',
      code: 'ADMIN_DISABLED'
    });
  }

  if (!tokensMatch(req.get('x-admin-token'), expected)) {
    return res.status(401).json({ error: 'Unauthorized', code: 'UNAUTHORIZED' });
  }

  next();
}

/**
 * Build cors options from CORS_ORIGINS (comma-separated allowlist).
 * Unset -> no cross-origin access (CORS headers omitted).
 */
export function buildCorsOptions(env = process.env) {
  const raw = env.CORS_ORIGINS;
  if (!raw) return { origin: false };
  const list = raw.split(',').map(s => s.trim()).filter(Boolean);
  if (list.includes('*')) return { origin: true };
  return { origin: list };
}
