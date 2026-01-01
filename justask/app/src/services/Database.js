import * as SQLite from 'expo-sqlite';

let db = null;
let initPromise = null;

const DATABASE_NAME = 'justask.db';

const Database = {
  /**
   * Initialize SQLite database (singleton with lock)
   */
  init: async () => {
    // Return existing db if already initialized
    if (db) return db;

    // If initialization is in progress, wait for it
    if (initPromise) return initPromise;

    // Start initialization
    initPromise = (async () => {
      try {
        db = await SQLite.openDatabaseAsync(DATABASE_NAME);
        console.log('✅ Database initialized');

        // Create tables if they don't exist
        await Database.createTables();

        return db;
      } catch (error) {
        console.error('❌ Database init error:', error);
        initPromise = null; // Allow retry on error
        throw error;
      }
    })();

    return initPromise;
  },

  /**
   * Create database tables
   */
  createTables: async () => {
    if (!db) return;

    try {
      // Offline queue table
      await db.execAsync(`
        CREATE TABLE IF NOT EXISTS offline_queue (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          query TEXT NOT NULL,
          timestamp INTEGER NOT NULL,
          status TEXT DEFAULT 'pending',
          created_at INTEGER DEFAULT (strftime('%s', 'now'))
        );
      `);

      // Offline responses table
      await db.execAsync(`
        CREATE TABLE IF NOT EXISTS offline_responses (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          queue_id INTEGER NOT NULL,
          response TEXT NOT NULL,
          llm_used TEXT,
          category TEXT,
          response_time INTEGER,
          synced_at INTEGER DEFAULT (strftime('%s', 'now')),
          FOREIGN KEY(queue_id) REFERENCES offline_queue(id)
        );
      `);

      // Cache table
      await db.execAsync(`
        CREATE TABLE IF NOT EXISTS cache (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          query_hash TEXT UNIQUE NOT NULL,
          query_text TEXT,
          response TEXT NOT NULL,
          llm_used TEXT,
          category TEXT,
          response_time INTEGER,
          created_at INTEGER DEFAULT (strftime('%s', 'now')),
          expires_at INTEGER NOT NULL
        );
      `);

      // Chat history table
      await db.execAsync(`
        CREATE TABLE IF NOT EXISTS chat_history (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          message_id TEXT UNIQUE NOT NULL,
          type TEXT NOT NULL,
          text TEXT NOT NULL,
          llm_used TEXT,
          category TEXT,
          response_time INTEGER,
          is_cached INTEGER DEFAULT 0,
          is_queued INTEGER DEFAULT 0,
          created_at INTEGER DEFAULT (strftime('%s', 'now'))
        );
      `);

      console.log('✅ Tables created');
    } catch (error) {
      console.error('❌ Create tables error:', error);
    }
  },

  /**
   * Queue a query for offline sync
   */
  queueQuery: async (queryText) => {
    if (!db) await Database.init();

    try {
      const timestamp = Date.now();
      const result = await db.runAsync(
        'INSERT INTO offline_queue (query, timestamp, status) VALUES (?, ?, ?)',
        [queryText, timestamp, 'pending']
      );

      const queueId = result.lastInsertRowId;
      console.log('✅ Query queued with ID:', queueId);
      return queueId;
    } catch (error) {
      console.error('❌ Queue query error:', error);
      throw error;
    }
  },

  /**
   * Get all pending queries
   */
  getPendingQueries: async () => {
    if (!db) await Database.init();

    try {
      const queries = await db.getAllAsync(
        'SELECT * FROM offline_queue WHERE status = ? ORDER BY created_at ASC',
        ['pending']
      );

      return queries;
    } catch (error) {
      console.error('❌ Get pending queries error:', error);
      return [];
    }
  },

  /**
   * Save offline response
   */
  saveOfflineResponse: async (queueId, response, llmUsed, category, responseTime) => {
    if (!db) await Database.init();

    try {
      await db.runAsync(
        'INSERT INTO offline_responses (queue_id, response, llm_used, category, response_time) VALUES (?, ?, ?, ?, ?)',
        [queueId, response, llmUsed, category, responseTime]
      );

      // Mark as synced
      await db.runAsync(
        'UPDATE offline_queue SET status = ? WHERE id = ?',
        ['synced', queueId]
      );

      console.log('✅ Offline response saved');
    } catch (error) {
      console.error('❌ Save offline response error:', error);
      throw error;
    }
  },

  /**
   * Get synced responses
   */
  getSyncedResponses: async () => {
    if (!db) await Database.init();

    try {
      const responses = await db.getAllAsync(`
        SELECT q.query, r.response, r.llm_used, r.category, r.response_time
        FROM offline_queue q
        LEFT JOIN offline_responses r ON q.id = r.queue_id
        WHERE q.status = ?
        ORDER BY r.synced_at DESC
      `, ['synced']);

      return responses;
    } catch (error) {
      console.error('❌ Get synced responses error:', error);
      return [];
    }
  },

  /**
   * Save message to chat history
   */
  saveMessage: async (message) => {
    if (!db) await Database.init();

    try {
      await db.runAsync(`
        INSERT INTO chat_history (message_id, type, text, llm_used, category, response_time, is_cached, is_queued)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        message.id,
        message.type,
        message.text,
        message.llmUsed || null,
        message.category || null,
        message.responseTime || null,
        message.isCached ? 1 : 0,
        message.isQueued ? 1 : 0,
      ]);

      console.log('✅ Message saved:', message.id);
    } catch (error) {
      console.error('❌ Save message error:', error);
      throw error;
    }
  },

  /**
   * Update message in chat history
   */
  updateMessage: async (messageId, updates) => {
    if (!db) await Database.init();

    try {
      const setClauses = Object.keys(updates).map(key => `${key} = ?`).join(', ');
      const values = Object.values(updates);
      values.push(messageId);

      await db.runAsync(`
        UPDATE chat_history SET ${setClauses} WHERE message_id = ?
      `, values);

      console.log('✅ Message updated:', messageId);
    } catch (error) {
      console.error('❌ Update message error:', error);
      throw error;
    }
  },

  /**
   * Load all chat history
   */
  loadChatHistory: async () => {
    if (!db) await Database.init();

    try {
      const rows = await db.getAllAsync(
        'SELECT * FROM chat_history ORDER BY created_at ASC'
      );

      const messages = rows.map(row => ({
        id: row.message_id,
        type: row.type,
        text: row.text,
        llmUsed: row.llm_used,
        category: row.category,
        responseTime: row.response_time,
        isCached: row.is_cached === 1,
        isQueued: row.is_queued === 1,
      }));

      console.log('✅ Chat history loaded:', messages.length, 'messages');
      return messages;
    } catch (error) {
      console.error('❌ Load chat history error:', error);
      return [];
    }
  },

  /**
   * Clear all chat history
   */
  clearChatHistory: async () => {
    if (!db) await Database.init();

    try {
      await db.execAsync('DELETE FROM chat_history');
      console.log('✅ Chat history cleared');
    } catch (error) {
      console.error('❌ Clear chat history error:', error);
      throw error;
    }
  },

  /**
   * Close database
   */
  close: async () => {
    if (db) {
      await db.closeAsync();
      db = null;
      console.log('✅ Database closed');
    }
  },
};

export default Database;
