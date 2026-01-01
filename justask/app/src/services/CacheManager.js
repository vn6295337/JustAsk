import Constants from 'expo-constants';
import Database from './Database';

/**
 * Simple string hash function for cache keys (FNV-1a hash)
 */
const simpleHash = (str) => {
  let hash = 2166136261;
  for (let i = 0; i < str.length; i++) {
    hash ^= str.charCodeAt(i);
    hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
  }
  return (hash >>> 0).toString(36);
};

const CacheManager = {
  /**
   * Generate hash of query for cache key
   */
  getQueryHash: (queryText) => {
    return simpleHash(queryText);
  },

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
    if (!queryText?.trim()) return null;

    try {
      const hash = CacheManager.getQueryHash(queryText);
      const db = await Database.init();

      const cached = await db.getFirstAsync(
        'SELECT * FROM cache WHERE query_hash = ? LIMIT 1',
        [hash]
      );

      if (!cached) {
        return null; // Cache miss
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
    if (!queryText?.trim()) return false;

    try {
      const hash = CacheManager.getQueryHash(queryText);
      const cacheTTLDays = parseInt(Constants.expoConfig?.extra?.cacheTtlDays || '7', 10);
      const expiresAt = Date.now() + cacheTTLDays * 24 * 60 * 60 * 1000;

      const db = await Database.init();

      // Check cache size before inserting
      const sizeOk = await CacheManager.checkAndEnforceSizeLimit();
      if (!sizeOk) {
        console.warn('⚠️ Cache size limit reached, clearing oldest entries');
      }

      await db.runAsync(
        `INSERT OR REPLACE INTO cache
         (query_hash, query_text, response, llm_used, category, response_time, expires_at)
         VALUES (?, ?, ?, ?, ?, ?, ?)`,
        [hash, queryText, response, llmUsed, category, responseTime, expiresAt]
      );

      console.log('✅ Response cached for:', queryText);
      return true;
    } catch (error) {
      console.error('❌ Cache save error:', error);
      return false;
    }
  },

  /**
   * Get total cache size in MB
   */
  getCacheSize: async () => {
    try {
      const db = await Database.init();
      const result = await db.getFirstAsync(
        `SELECT SUM(LENGTH(response)) as total_bytes FROM cache`
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
   * Check and enforce 50MB size limit
   * Returns false if limit exceeded and cleanup didn't free enough space
   */
  checkAndEnforceSizeLimit: async () => {
    try {
      const cacheSizeLimit = parseFloat(Constants.expoConfig?.extra?.cacheSizeLimitMb || '50');
      const currentSize = await CacheManager.getCacheSize();

      if (currentSize > cacheSizeLimit) {
        // Delete oldest entries by created_at until under limit
        const db = await Database.init();
        const entriesNeeded = Math.ceil((currentSize - cacheSizeLimit) / 2); // Rough estimate

        const rows = await db.getAllAsync(
          `SELECT id FROM cache ORDER BY created_at ASC LIMIT ?`,
          [entriesNeeded]
        );

        if (rows.length > 0) {
          for (const row of rows) {
            await db.runAsync('DELETE FROM cache WHERE id = ?', [row.id]);
          }

          console.log(`🧹 Cleaned up ${rows.length} oldest cache entries`);
        }

        return false; // Size was over limit
      }

      return true; // Size is ok
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
