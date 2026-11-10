import * as SQLite from 'expo-sqlite';
import Database from '../services/Database';
import CacheManager from '../services/CacheManager';

jest.spyOn(console, 'log').mockImplementation(() => {});
jest.spyOn(console, 'warn').mockImplementation(() => {});
jest.spyOn(console, 'error').mockImplementation(() => {});

beforeEach(async () => {
  await Database.close(); // fresh in-memory DB each test
  SQLite.openDatabaseAsync.mockClear();
});

describe('Database', () => {
  test('concurrent init() opens once and tables exist before db is returned', async () => {
    const [a, b] = await Promise.all([Database.init(), Database.init()]);
    expect(a).toBe(b);
    expect(SQLite.openDatabaseAsync).toHaveBeenCalledTimes(1);
    const t = await a.getAllAsync("SELECT name FROM sqlite_master WHERE name='offline_queue'");
    expect(t).toHaveLength(1);
  });

  test('close() resets state so a later init reopens', async () => {
    const first = await Database.init();
    await Database.close();
    const second = await Database.init();
    expect(second).not.toBe(first);
    expect(SQLite.openDatabaseAsync).toHaveBeenCalledTimes(2);
  });

  test('queue cap is enforced (QUEUE_FULL)', async () => {
    await Database.queueQuery('a');
    await Database.queueQuery('b');
    await Database.queueQuery('c'); // cap = 3 in mock Constants
    await expect(Database.queueQuery('d')).rejects.toMatchObject({ code: 'QUEUE_FULL' });
  });

  test('recordSyncFailure counts attempts and marks failed at the limit', async () => {
    const id = await Database.queueQuery('q');
    expect(await Database.recordSyncFailure(id, 'x')).toBe('pending');
    expect(await Database.recordSyncFailure(id, 'x')).toBe('pending');
    expect(await Database.recordSyncFailure(id, 'x')).toBe('failed');
    expect(await Database.getPendingQueries()).toHaveLength(0);
  });

  test('permanent failure marks failed immediately', async () => {
    const id = await Database.queueQuery('q');
    expect(await Database.recordSyncFailure(id, 'bad', true)).toBe('failed');
  });

  test('saveOfflineResponse is transactional and idempotent', async () => {
    const id = await Database.queueQuery('q');
    const db = await Database.init();
    await Database.saveOfflineResponse(id, 'r', 'groq', 'general', 5);
    await Database.saveOfflineResponse(id, 'r', 'groq', 'general', 5);
    expect(await db.getAllAsync('SELECT * FROM offline_responses')).toHaveLength(1);
    expect((await db.getFirstAsync('SELECT status FROM offline_queue WHERE id=?', [id])).status).toBe('synced');

    // rollback: failing second statement must not leave a response row
    const id2 = await Database.queueQuery('q2');
    await db.execAsync("CREATE TRIGGER fail_upd BEFORE UPDATE ON offline_queue BEGIN SELECT RAISE(ABORT, 'boom'); END");
    await expect(Database.saveOfflineResponse(id2, 'r2', 'g', 'c', 1)).rejects.toBeDefined();
    expect(await db.getAllAsync('SELECT * FROM offline_responses WHERE queue_id=?', [id2])).toHaveLength(0);
  });

  test('updateMessage ignores non-allowlisted keys (no SQL injection via keys)', async () => {
    await Database.saveMessage({ id: 'm1', type: 'assistant', text: 'old' });
    await Database.updateMessage('m1', { text: 'new', 'text = 1; DROP TABLE chat_history; --': 'x', message_id: 'hijack' });
    const history = await Database.loadChatHistory();
    expect(history).toHaveLength(1);
    expect(history[0].id).toBe('m1');
    expect(history[0].text).toBe('new');
  });

  test('history ordering uses id tiebreak within the same second', async () => {
    for (const id of ['a', 'b', 'c']) await Database.saveMessage({ id, type: 'user', text: id });
    const db = await Database.init();
    await db.execAsync('UPDATE chat_history SET created_at = 1000');
    expect((await Database.loadChatHistory()).map((m) => m.id)).toEqual(['a', 'b', 'c']);
  });

  test('recoverInterruptedMessages replaces stale "Thinking..."', async () => {
    await Database.saveMessage({ id: 't', type: 'assistant', text: 'Thinking...' });
    await Database.recoverInterruptedMessages();
    expect((await Database.loadChatHistory())[0].text).toMatch(/interrupted/i);
  });
});

describe('CacheManager', () => {
  test('keys are case/whitespace-insensitive', async () => {
    await CacheManager.saveToCache('What is   AI?', 'an answer', 'groq', 'general_knowledge', 1);
    const hit = await CacheManager.getCachedResponse('  what is ai? ');
    expect(hit.response).toBe('an answer');
  });

  test('hash collision returns a miss (query_text compared)', async () => {
    await CacheManager.saveToCache('real question', 'answer', 'groq', 'general_knowledge', 1);
    const db = await Database.init();
    const collidingHash = CacheManager.getQueryHash('other question');
    await db.runAsync("UPDATE cache SET query_hash = ?", [collidingHash]);
    expect(await CacheManager.getCachedResponse('other question')).toBeNull();
  });

  test('time-sensitive queries and categories are never cached', async () => {
    expect(await CacheManager.saveToCache('latest news on X', 'a', 'groq', 'general_knowledge', 1)).toBe(false);
    expect(await CacheManager.saveToCache('explain recursion', 'a', 'groq', 'business_news', 1)).toBe(false);
    expect(CacheManager.isCacheable('bitcoin price today')).toBe(false);
    expect(CacheManager.isCacheable('explain recursion')).toBe(true);
  });

  test('size eviction removes oldest entries by bytes and returns accurate result', async () => {
    const Constants = require('expo-constants').default;
    Constants.expoConfig.extra.cacheSizeLimitMb = '0.001'; // ~1 KB
    try {
      const big = 'é'.repeat(300); // 600 bytes
      await CacheManager.saveToCache('q1', big, 'g', 'c', 1);
      await CacheManager.saveToCache('q2', big, 'g', 'c', 1);
      await CacheManager.saveToCache('q3', big, 'g', 'c', 1);
      const db = await Database.init();
      const rows = await db.getAllAsync('SELECT query_text FROM cache ORDER BY id');
      expect(rows.length).toBeLessThan(3);
      expect(rows.map((r) => r.query_text)).toContain('q3');
    } finally {
      Constants.expoConfig.extra.cacheSizeLimitMb = '50';
    }
  });

  test('expired rows are purged on save', async () => {
    await CacheManager.saveToCache('old one', 'a', 'g', 'c', 1);
    const db = await Database.init();
    await db.runAsync('UPDATE cache SET expires_at = 1');
    await CacheManager.saveToCache('new one', 'b', 'g', 'c', 1);
    const rows = await db.getAllAsync('SELECT query_text FROM cache');
    expect(rows.map((r) => r.query_text)).toEqual(['new one']);
  });
});
