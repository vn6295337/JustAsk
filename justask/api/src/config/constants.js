/**
 * Configuration Constants
 * Centralized settings for classification, models, and rate limits
 */

export const KEYWORDS = {
  news: ['news', 'latest', 'today', 'current', 'breaking', 'headline', 'trending'],
  financial: [
    'stock',
    'investment',
    'portfolio',
    'financial',
    'market',
    'trading',
    'crypto',
    'bitcoin',
    'ethereum',
    'forex',
    'bonds',
    'etf',
    'dividend',
    'roi',
    'profit',
    'loss',
    'revenue',
    'earnings',
  ],
  creative: [
    'poem',
    'story',
    'creative',
    'compose',
    'create',
    'author',
    'fiction',
    'narrative',
  ],
};

export const MODELS = {
  gemini: 'models/gemini-2.0-flash',
  groq: 'llama-3.1-8b-instant',
  groqCompound: 'groq/compound',
  openrouter: 'kwaipilot/kat-coder-pro:free',
  openaiGptOss20b: 'openai/gpt-oss-20b',
  openaiGptOss120b: 'openai/gpt-oss-120b',
};

export const RATE_LIMITS = {
  gemini: 60, // requests per minute
  groq: 30,
  openrouter: 100,
};

export const QUERY_CATEGORIES = {
  BUSINESS_NEWS: 'business_news',
  FINANCIAL_ANALYSIS: 'financial_analysis',
  CREATIVE: 'creative',
  GENERAL_KNOWLEDGE: 'general_knowledge',
};

export const PROVIDER_NAMES = {
  GEMINI: 'gemini',
  GROQ: 'groq',
  OPENROUTER: 'openrouter',
};

// Failover chain: Primary → Secondary → Tertiary
export const FAILOVER_CHAIN = [
  PROVIDER_NAMES.GROQ,      // Secondary
  PROVIDER_NAMES.OPENROUTER, // Tertiary
];

export const API_ENDPOINTS = {
  gemini: 'https://generativelanguage.googleapis.com/v1beta/models',
  groq: 'https://api.groq.com/openai/v1',
  openrouter: 'https://openrouter.ai/api/v1',
};

export const RESPONSE_TIMEOUTS = {
  default: 10000, // 10 seconds
  gemini: 12000,  // 12 seconds (web search might be slower)
  groq: 10000,
  openrouter: 10000,
};

export const ERROR_CODES = {
  INVALID_QUERY: 'INVALID_QUERY',
  RATE_LIMITED: 'RATE_LIMITED',
  PROVIDER_ERROR: 'PROVIDER_ERROR',
  TIMEOUT: 'TIMEOUT',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
};
