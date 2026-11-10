import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import * as constants from './config/constants.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from .env file
dotenv.config({ path: path.join(__dirname, '..', '.env') });

export const config = {
  port: process.env.PORT || 3000,
  // Defaults to production so placeholder dev keys are never used unless
  // NODE_ENV=development is set explicitly.
  nodeEnv: process.env.NODE_ENV || 'production',
  supabase: {
    url: process.env.SUPABASE_URL,
    key: process.env.SUPABASE_KEY,
  },
  // Optional shared token. If API_AUTH_TOKEN is unset, auth is disabled.
  authToken: process.env.API_AUTH_TOKEN || '',
  // Extra allowed CORS origins (comma-separated)
  corsOrigins: (process.env.CORS_ORIGINS || '')
    .split(',')
    .map((o) => o.trim())
    .filter(Boolean),
  // Inbound (per-IP) limits, requests per minute
  inboundLimits: {
    query: parseInt(process.env.RATE_LIMIT_QUERY_PER_MIN, 10) || 30,
    sync: parseInt(process.env.RATE_LIMIT_SYNC_PER_MIN, 10) || 4,
  },
  sync: {
    maxBatch: 20,
    timeBudgetMs: 20000,
  },
  logging: {
    level: process.env.LOG_LEVEL || 'info',
  },
  // Application constants
  keywords: constants.KEYWORDS,
  models: constants.MODELS,
  rateLimits: constants.RATE_LIMITS,
  queryCategories: constants.QUERY_CATEGORIES,
  providerNames: constants.PROVIDER_NAMES,
  failoverChain: constants.FAILOVER_CHAIN,
  apiEndpoints: constants.API_ENDPOINTS,
  responseTimeouts: constants.RESPONSE_TIMEOUTS,
  errorCodes: constants.ERROR_CODES,
};

// Verify required environment variables (warn if missing)
const requiredEnvVars = ['SUPABASE_URL', 'SUPABASE_KEY'];
const missingEnvVars = requiredEnvVars.filter(
  (envVar) => !process.env[envVar]
);

if (missingEnvVars.length > 0 && config.nodeEnv === 'production') {
  console.error(
    `Missing required environment variables: ${missingEnvVars.join(', ')}`
  );
  process.exit(1);
}

if (missingEnvVars.length > 0 && config.nodeEnv === 'development') {
  console.warn(
    `Missing environment variables (required for production): ${missingEnvVars.join(', ')}`
  );
}

export default config;
