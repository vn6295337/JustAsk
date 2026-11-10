import Constants from 'expo-constants';
import Database from './Database';

/**
 * Normalize query text for cache keys: case/whitespace-insensitive.
 */
const normalizeQuery = (text) => text.trim().replace(/\s+/g, ' ').toLowerCase();

/**
 * FNV-1a string hash with a configurable seed
 */
const fnv = (str, seed) => {
  let hash = seed;
  for (let i = 0; i < str.length; i++) {
    hash ^= str.charCodeAt(i);
    hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
  }
  return (hash >>> 0).toString(36);
};

// Queries whose answers go stale quickly must never be served from cache
const TIME_SENSITIVE =
  /\b(today|tonight|tomorrow|yesterday|now|current(ly)?|latest|recent(ly)?|breaking|news|headlines?|trending|live|update[sd]?|price|prices|quote|stock|stocks|shares?|crypto|bitcoin|ethereum|exchange rate|rates?|weather|forecast|score|scores|this (morning|week|month|year)|right now|as of)\b/i;

const UNCACHEABLE_CATEGORIES = new Set(['business_news', 'financial_analysis']);

const CacheManager = {
  normalizeQuery,

  /**
   * Hash of the normalized query (two independent 32-bit FNV passes).
   * Collisions are still possible, so lookups also compare query_text.
   */
  getQueryHash: (queryText) => {
    const n = normalizeQuery(queryText);
    return `${fnv(n, 2166136261)}${fnv(n, 0x9747b28c)}`;
  },

  /**
   * False for time-sensitive queries (news, prices, "today", ...)
   */
  isCacheable: (queryText) => !!queryText?.trim() && !TIME_SENSITIVE.test(queryText),

  isCacheableCategory: (category) => !UNCACHEABLE_CATEGORIES.has(category),

  /**
   * Check if cached response is valid (not expired)
   */
  isCacheValid: (expiresAt) => {
    return expiresAt > Date.now();
  },

  /**
   * Get cached response if it exists and is valid
   */
  getCachedResponse: async (queryText) => {
    if (!CacheManager.isCacheable(queryText)) return null;

    try {
      const normalized = normalizeQuery(queryText);
      const hash = CacheManager.getQueryHash(queryText);
      const db = await Database.init();

      const cached = await db.getFirstAsync(
        'SELECT * FROM cache WHERE query_hash = ? LIMIT 1',
        [hash]
      );

      if (!cached) {
        return null; // Cache miss
      }

      // Hash collision: same key, different query text
      if (cached.query_text !== normalized) {
        return null;
      }

      // Check if expired
      if (!CacheManager.isCacheValid(cached.expires_at)) {
        // Delete expired entry
        await CacheManager.deleteExpiredEntry(hash);
        return null;
      }

      console.log('✅ Cache hit for query:', queryText);
      return {
        response: cached.response,
        llm_used: cached.llm_used,
        category: cached.category,
        response_time: cached.response_time,
        cached: true,
      };
    } catch (error) {
      console.error('❌ Cache lookup error:', error);
      return null;
    }
  },

  /**
   * Save response to cache with TTL
   */
  saveToCache: async (queryText, response, llmUsed, category, responseTime) => {
    if (!CacheManager.isCacheable(queryText) || !response?.trim()) return false;
    if (!CacheManager.isCacheableCategory(category)) return false;

    try {
      const normalized = normalizeQuery(queryText);
      const hash = CacheManager.getQueryHash(queryText);
      const cacheTTLDays = parseInt(Constants.expoConfig?.extra?.cacheTtlDays || '7', 10);
      const expiresAt = Date.now() + cacheTTLDays * 24 * 60 * 60 * 1000;

      const db = await Database.init();

      // Drop expired rows, then make room; skip caching if still over the limit
      await CacheManager.deleteExpiredAll();
      const sizeOk = await CacheManager.checkAndEnforceSizeLimit();
      if (!sizeOk) {
        console.warn('⚠️ Cache size limit reached, response not cached');
        return false;
      }

      await db.runAsync(
        `INSERT OR REPLACE INTO cache
         (query_hash, query_text, response, llm_used, category, response_time, expires_at)
         VALUES (?, ?, ?, ?, ?, ?, ?)`,
        [hash, normalized, response, llmUsed, category, responseTime, expiresAt]
      );

      console.log('✅ Response cached for:', queryText);
      return true;
    } catch (error) {
      console.error('❌ Cache save error:', error);
      return false;
    }
  },

  /**
   * Delete every expired entry
   */
  deleteExpiredAll: async () => {
    try {
      const db = await Database.init();
      await db.runAsync('DELETE FROM cache WHERE expires_at <= ?', [Date.now()]);
    } catch (error) {
      console.error('❌ Delete expired entries error:', error);
    }
  },

  /**
   * Get total cache size in MB (UTF-8 bytes, not characters)
   */
  getCacheSize: async () => {
    try {
      const db = await Database.init();
      const result = await db.getFirstAsync(
        `SELECT SUM(LENGTH(CAST(response AS BLOB)) + LENGTH(CAST(COALESCE(query_text, '') AS BLOB))) as total_bytes FROM cache`
      );

      if (!result) {
        return 0;
      }

      const totalBytes = result.total_bytes || 0;
      return totalBytes / (1024 * 1024); // Convert to MB
    } catch (error) {
      console.error('❌ Cache size calculation error:', error);
      return 0;
    }
  },

  /**
   * Enforce the size limit by evicting oldest entries (by actual byte size)
   * until usage is under 90% of the limit.
   * @returns {Promise<boolean>} true if the cache is under the limit afterwards
   */
  checkAndEnforceSizeLimit: async () => {
    try {
      const limitMb = parseFloat(Constants.expoConfig?.extra?.cacheSizeLimitMb || '50');
      const currentMb = await CacheManager.getCacheSize();

      if (currentMb <= limitMb) {
        return true;
      }

      const db = await Database.init();
      const targetBytes = limitMb * 0.9 * 1024 * 1024;
      let totalBytes = currentMb * 1024 * 1024;

      const rows = await db.getAllAsync(
        `SELECT id, LENGTH(CAST(response AS BLOB)) + LENGTH(CAST(COALESCE(query_text, '') AS BLOB)) AS bytes
         FROM cache ORDER BY created_at ASC, id ASC`
      );

      const toDelete = [];
      for (const row of rows) {
        if (totalBytes <= targetBytes) break;
        toDelete.push(row.id);
        totalBytes -= row.bytes || 0;
      }

      for (const id of toDelete) {
        await db.runAsync('DELETE FROM cache WHERE id = ?', [id]);
      }
      console.log(`🧹 Cleaned up ${toDelete.length} oldest cache entries`);

      return totalBytes <= limitMb * 1024 * 1024;
    } catch (error) {
      console.error('❌ Cache size enforcement error:', error);
      return true; // Allow operation on error
    }
  },

  /**
   * Delete expired cache entries
   */
  deleteExpiredEntry: async (hash) => {
    try {
      const db = await Database.init();
      await db.runAsync('DELETE FROM cache WHERE query_hash = ?', [hash]);
    } catch (error) {
      console.error('❌ Delete expired entry error:', error);
    }
  },

  /**
   * Clear entire cache
   */
  clearAll: async () => {
    try {
      const db = await Database.init();
      await db.execAsync('DELETE FROM cache');
      console.log('✅ Cache cleared');
    } catch (error) {
      console.error('❌ Clear all cache error:', error);
    }
  },
};

export default CacheManager;
