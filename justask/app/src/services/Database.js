import * as SQLite from 'expo-sqlite';
import Constants from 'expo-constants';

let db = null;
let initPromise = null;

const DATABASE_NAME = 'justask.db';

// Queue entries that fail this many times are marked 'failed' (no more billing)
const MAX_ATTEMPTS = 3;

// Columns that updateMessage may set (everything else is ignored)
const UPDATABLE_MESSAGE_COLUMNS = new Set([
  'text',
  'llm_used',
  'category',
  'response_time',
  'is_cached',
  'is_queued',
]);

const getQueueMaxSize = () =>
  parseInt(Constants.expoConfig?.extra?.offlineQueueMaxSize, 10) || 10;

const Database = {
  MAX_ATTEMPTS,

  /**
   * Initialize SQLite database (singleton with lock).
   * `db` is published only after tables exist, so concurrent callers never
   * receive a half-initialized handle.
   */
  init: async () => {
    if (db) return db;
    if (initPromise) return initPromise;

    initPromise = (async () => {
      try {
        const handle = await SQLite.openDatabaseAsync(DATABASE_NAME);
        await Database.createTables(handle);
        db = handle;
        console.log('✅ Database initialized');
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
  createTables: async (db) => {
    try {
      // Offline queue table
      await db.execAsync(`
        CREATE TABLE IF NOT EXISTS offline_queue (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          query TEXT NOT NULL,
          timestamp INTEGER NOT NULL,
          status TEXT DEFAULT 'pending',
          attempts INTEGER DEFAULT 0,
          last_error TEXT,
          message_id TEXT,
          created_at INTEGER DEFAULT (strftime('%s', 'now'))
        );
      `);

      // Migrate older installs that lack the newer queue columns
      const queueCols = (await db.getAllAsync('PRAGMA table_info(offline_queue)')).map(
        (c) => c.name
      );
      if (!queueCols.includes('attempts')) {
        await db.execAsync('ALTER TABLE offline_queue ADD COLUMN attempts INTEGER DEFAULT 0');
      }
      if (!queueCols.includes('last_error')) {
        await db.execAsync('ALTER TABLE offline_queue ADD COLUMN last_error TEXT');
      }
      if (!queueCols.includes('message_id')) {
        await db.execAsync('ALTER TABLE offline_queue ADD COLUMN message_id TEXT');
      }

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
      throw error;
    }
  },

  /**
   * Queue a query for offline sync.
   * @param {string} queryText
   * @param {string|null} messageId - chat placeholder message to update on sync
   * @throws {Error} with code 'QUEUE_FULL' when the pending cap is reached
   */
  queueQuery: async (queryText, messageId = null) => {
    const db = await Database.init();

    try {
      const row = await db.getFirstAsync(
        'SELECT COUNT(*) AS n FROM offline_queue WHERE status = ?',
        ['pending']
      );
      const max = getQueueMaxSize();
      if ((row?.n || 0) >= max) {
        const full = new Error(`Offline queue is full (${max} queries). Sync before adding more.`);
        full.code = 'QUEUE_FULL';
        throw full;
      }

      const timestamp = Date.now();
      const result = await db.runAsync(
        'INSERT INTO offline_queue (query, timestamp, status, message_id) VALUES (?, ?, ?, ?)',
        [queryText, timestamp, 'pending', messageId]
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
    const db = await Database.init();

    try {
      const queries = await db.getAllAsync(
        'SELECT * FROM offline_queue WHERE status = ? ORDER BY created_at ASC, id ASC',
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
    const db = await Database.init();

    try {
      // Insert response + mark synced atomically (no duplicates on partial failure)
      await db.withTransactionAsync(async () => {
        const existing = await db.getFirstAsync(
          'SELECT id FROM offline_responses WHERE queue_id = ? LIMIT 1',
          [queueId]
        );
        if (!existing) {
          await db.runAsync(
            'INSERT INTO offline_responses (queue_id, response, llm_used, category, response_time) VALUES (?, ?, ?, ?, ?)',
            [queueId, response, llmUsed, category, responseTime]
          );
        }

        await db.runAsync(
          'UPDATE offline_queue SET status = ? WHERE id = ?',
          ['synced', queueId]
        );
      });

      console.log('✅ Offline response saved');
    } catch (error) {
      console.error('❌ Save offline response error:', error);
      throw error;
    }
  },

  /**
   * Record a failed sync attempt. The entry becomes 'failed' (never retried,
   * never billed again) when `permanent` or MAX_ATTEMPTS is reached.
   * @returns {Promise<string>} new status
   */
  recordSyncFailure: async (queueId, errorText, permanent = false) => {
    const db = await Database.init();

    try {
      const row = await db.getFirstAsync(
        'SELECT attempts FROM offline_queue WHERE id = ?',
        [queueId]
      );
      const attempts = (row?.attempts || 0) + 1;
      const status = permanent || attempts >= MAX_ATTEMPTS ? 'failed' : 'pending';
      await db.runAsync(
        'UPDATE offline_queue SET attempts = ?, last_error = ?, status = ? WHERE id = ? AND status = ?',
        [attempts, String(errorText || '').slice(0, 200), status, queueId, 'pending']
      );
      return status;
    } catch (error) {
      console.error('❌ Record sync failure error:', error);
      throw error;
    }
  },

  /**
   * Get synced responses
   */
  getSyncedResponses: async () => {
    const db = await Database.init();

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
    const db = await Database.init();

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
    const db = await Database.init();

    try {
      const keys = Object.keys(updates || {}).filter((k) => UPDATABLE_MESSAGE_COLUMNS.has(k));
      if (keys.length === 0) {
        console.warn('⚠️ updateMessage: no allowed columns in update');
        return;
      }
      const setClauses = keys.map((key) => `${key} = ?`).join(', ');
      const values = keys.map((key) => updates[key]);
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
   * Replace "Thinking..." placeholders left behind by an app kill.
   * Call once at startup, before loading history (nothing is in flight yet).
   */
  recoverInterruptedMessages: async () => {
    const db = await Database.init();
    await db.runAsync(
      'UPDATE chat_history SET text = ? WHERE type = ? AND text = ? AND is_queued = 0',
      ['Request interrupted. Please ask again.', 'assistant', 'Thinking...']
    );
  },

  /**
   * Load all chat history
   */
  loadChatHistory: async () => {
    const db = await Database.init();

    try {
      const rows = await db.getAllAsync(
        'SELECT * FROM chat_history ORDER BY created_at ASC, id ASC'
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
    const db = await Database.init();

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
    const pending = initPromise;
    if (pending) {
      try {
        await pending;
      } catch (e) {
        // init failed; nothing to close
      }
    }
    const handle = db;
    db = null;
    initPromise = null;
    if (handle) {
      await handle.closeAsync();
      console.log('✅ Database closed');
    }
  },
};

export default Database;
