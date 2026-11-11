import path from 'path';
import { fileURLToPath } from 'url';
import maxmind from 'maxmind';

/**
 * Region block for the Gemini API Unpaid Services terms: API clients may not
 * be offered to users in the EEA, Switzerland or the UK on the free tier.
 *
 * Country codes are ISO 3166-1 alpha-2 as returned by the geo database.
 * Includes EU outermost regions and Aland, which geo databases report under
 * their own codes, and the UK Crown Dependencies (conservative choice).
 */
export const BLOCKED_COUNTRIES = new Set([
  // EU member states (27)
  'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE',
  'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE',
  // EEA, non-EU
  'IS', 'LI', 'NO',
  // UK and Switzerland
  'GB', 'CH',
  // EU territories with their own codes: Aland, French outermost regions
  'AX', 'GF', 'GP', 'MQ', 'RE', 'YT', 'MF',
  // UK Crown Dependencies
  'JE', 'GG', 'IM',
]);

export const REGION_BLOCKED_MESSAGE = "Sorry, JustAsk isn't available in your region yet.";

const here = path.dirname(fileURLToPath(import.meta.url));
export const DEFAULT_GEO_DB_PATH = path.resolve(here, '../../geo/dbip-country-lite.mmdb');

let reader = null;

/**
 * Load the country database. Call once at startup; throws if it cannot load.
 */
export const loadGeoDb = async (dbPath = process.env.GEO_DB_PATH || DEFAULT_GEO_DB_PATH) => {
  reader = await maxmind.open(dbPath);
  return reader;
};

/** Test hook: inject a reader (anything with get(ip)), or null to unload. */
export const setGeoReader = (r) => {
  reader = r;
};

export const isGeoDbLoaded = () => reader !== null;

/**
 * Normalize an address for lookup: strip the IPv4-mapped IPv6 prefix and any
 * IPv6 zone index. Returns null for empty or invalid input.
 */
export const normalizeIp = (ip) => {
  if (!ip || typeof ip !== 'string') return null;
  let out = ip.trim();
  if (out.toLowerCase().startsWith('::ffff:') && out.includes('.')) {
    out = out.slice(7);
  }
  const zone = out.indexOf('%');
  if (zone !== -1) out = out.slice(0, zone);
  return maxmind.validate(out) ? out : null;
};

/**
 * Country code for an address, or null if unknown.
 * Throws if the database is not loaded.
 */
export const lookupCountry = (ip) => {
  if (!reader) throw new Error('Geo database not loaded');
  const addr = normalizeIp(ip);
  if (!addr) return null;
  const rec = reader.get(addr);
  return rec?.country?.iso_code || null;
};

/**
 * Express middleware. Fails closed (503) if the database is not loaded.
 * Unknown countries are allowed through. The client IP is never logged.
 */
export const blockRestrictedRegions = (req, res, next) => {
  if (!reader) {
    return res.status(503).json({ error: 'Service temporarily unavailable', status: 503 });
  }

  let country = null;
  try {
    country = lookupCountry(req.ip);
  } catch {
    country = null;
  }

  if (country && BLOCKED_COUNTRIES.has(country)) {
    console.log(`[RegionBlock] Blocked request from ${country}`);
    return res.status(451).json({
      error: REGION_BLOCKED_MESSAGE,
      status: 451,
      code: 'REGION_BLOCKED',
    });
  }
  next();
};

export default {
  BLOCKED_COUNTRIES,
  REGION_BLOCKED_MESSAGE,
  loadGeoDb,
  setGeoReader,
  isGeoDbLoaded,
  normalizeIp,
  lookupCountry,
  blockRestrictedRegions,
};
