import crypto from 'crypto';
import config from '../config.js';

const safeEqual = (a, b) => {
  const ha = crypto.createHash('sha256').update(a).digest();
  const hb = crypto.createHash('sha256').update(b).digest();
  return crypto.timingSafeEqual(ha, hb);
};

/**
 * Optional shared-token auth. Enabled only when API_AUTH_TOKEN is set;
 * when unset the middleware is a no-op so existing deployments keep working.
 * Client sends `Authorization: Bearer <token>` or `X-API-Key: <token>`.
 */
export const requireToken = (req, res, next) => {
  const expected = config.authToken;
  if (!expected) return next();

  const header = req.get('authorization') || '';
  const provided = header.startsWith('Bearer ')
    ? header.slice(7).trim()
    : req.get('x-api-key') || '';

  if (!provided || !safeEqual(provided, expected)) {
    return res.status(401).json({ error: 'Unauthorized', status: 401 });
  }
  next();
};

export default { requireToken };
