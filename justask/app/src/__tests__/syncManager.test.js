import NetInfo from '@react-native-community/netinfo';
import SyncManager from '../services/SyncManager';
import Database from '../services/Database';
import APIClient from '../services/APIClient';

jest.mock('../services/APIClient', () => ({ __esModule: true, default: { syncOfflineQueries: jest.fn() } }));
jest.mock('../store', () => ({ __esModule: true, default: { dispatch: jest.fn() } }));

jest.spyOn(console, 'log').mockImplementation(() => {});
jest.spyOn(console, 'warn').mockImplementation(() => {});
jest.spyOn(console, 'error').mockImplementation(() => {});

beforeEach(async () => {
  await Database.close();
  APIClient.syncOfflineQueries.mockReset();
  NetInfo.fetch.mockResolvedValue({ isConnected: true });
});

describe('SyncManager', () => {
  test('concurrent syncPending calls share one run (isSyncing set synchronously)', async () => {
    const id = await Database.queueQuery('q', 'assistant-1');
    await Database.saveMessage({ id: 'assistant-1', type: 'assistant', text: 'Query saved.', isQueued: true });
    APIClient.syncOfflineQueries.mockImplementation(async (qs) => {
      await new Promise((r) => setTimeout(r, 30));
      return { responses: qs.map((q) => ({ id: q.id, success: true, response: 'ans', llm_used: 'groq', category: 'general' })) };
    });

    const p1 = SyncManager.syncPending();
    expect(SyncManager.isSyncing).toBe(true); // synchronous
    const p2 = SyncManager.syncPending();
    await Promise.all([p1, p2]);

    expect(APIClient.syncOfflineQueries).toHaveBeenCalledTimes(1);
    expect(SyncManager.isSyncing).toBe(false);
    expect(id).toBeDefined();
  });

  test('answer is written onto the queued placeholder message', async () => {
    await Database.queueQuery('q', 'assistant-1');
    await Database.saveMessage({ id: 'assistant-1', type: 'assistant', text: 'Query saved.', isQueued: true });
    APIClient.syncOfflineQueries.mockImplementation(async (qs) => ({
      responses: qs.map((q) => ({ id: q.id, success: true, response: 'the answer', llm_used: 'groq' })),
    }));
    await SyncManager.syncPending();
    const hist = await Database.loadChatHistory();
    expect(hist).toHaveLength(1);
    expect(hist[0]).toMatchObject({ id: 'assistant-1', text: 'the answer', isQueued: false });
  });

  test('failed items count attempts, become failed at the cap, and are not re-sent', async () => {
    await Database.queueQuery('q', 'assistant-1');
    await Database.saveMessage({ id: 'assistant-1', type: 'assistant', text: 'Query saved.', isQueued: true });
    APIClient.syncOfflineQueries.mockImplementation(async (qs) => ({
      responses: qs.map((q) => ({ id: q.id, success: false, error: 'boom' })),
    }));
    for (let i = 0; i < 3; i++) await SyncManager.syncPending();
    expect(APIClient.syncOfflineQueries).toHaveBeenCalledTimes(3);
    await SyncManager.syncPending(); // nothing pending any more
    expect(APIClient.syncOfflineQueries).toHaveBeenCalledTimes(3);
    expect((await Database.loadChatHistory())[0].text).toMatch(/could not answer/i);
  });

  test('permanent rejection marks failed immediately', async () => {
    await Database.queueQuery('q');
    APIClient.syncOfflineQueries.mockImplementation(async (qs) => ({
      responses: qs.map((q) => ({ id: q.id, success: false, permanent: true, error: 'invalid' })),
    }));
    await SyncManager.syncPending();
    expect(await Database.getPendingQueries()).toHaveLength(0);
  });

  test('request failure is NOT retried in-run (no whole-batch re-billing); attempts counted', async () => {
    await Database.queueQuery('q1');
    await Database.queueQuery('q2');
    APIClient.syncOfflineQueries.mockRejectedValue(new Error('timeout'));
    const ok = await SyncManager.syncPending();
    expect(ok).toBe(false);
    expect(APIClient.syncOfflineQueries).toHaveBeenCalledTimes(1);
    const pending = await Database.getPendingQueries();
    expect(pending.map((p) => p.attempts)).toEqual([1, 1]);
  });

  test('pending queries are sent in batches of at most 20', async () => {
    const Constants = require('expo-constants').default;
    Constants.expoConfig.extra.offlineQueueMaxSize = '50';
    for (let i = 0; i < 25; i++) await Database.queueQuery(`q${i}`);
    APIClient.syncOfflineQueries.mockImplementation(async (qs) => ({
      responses: qs.map((q) => ({ id: q.id, success: true, response: 'a', llm_used: 'g' })),
    }));
    await SyncManager.syncPending();
    expect(APIClient.syncOfflineQueries.mock.calls.map((c) => c[0].length)).toEqual([20, 5]);
    Constants.expoConfig.extra.offlineQueueMaxSize = '3';
  });

  test('deferred items (never started by server) do not consume attempts', async () => {
    await Database.queueQuery('q');
    APIClient.syncOfflineQueries.mockImplementation(async (qs) => ({
      responses: qs.map((q) => ({ id: q.id, success: false, retryable: true, deferred: true, error: 'Deferred' })),
    }));
    for (let i = 0; i < 5; i++) await SyncManager.syncPending();
    const pending = await Database.getPendingQueries();
    expect(pending).toHaveLength(1);
    expect(pending[0].attempts).toBe(0);
  });

  test('429 from the server does not consume attempts', async () => {
    await Database.queueQuery('q');
    APIClient.syncOfflineQueries.mockRejectedValue(Object.assign(new Error('rate'), { status: 429 }));
    await SyncManager.syncPending();
    expect((await Database.getPendingQueries())[0].attempts).toBe(0);
  });
});
