jest.mock('../services/APIClient', () => ({ __esModule: true, default: { health: jest.fn() } }));

import APIClient from '../services/APIClient';
import ServerWake, { QUIET_MS, WAKE_TIMEOUT_MS, FRESH_MS, waitingText } from '../services/ServerWake';

const deferred = () => {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
};

beforeEach(() => {
  jest.useFakeTimers();
  ServerWake._reset();
  APIClient.health.mockReset();
});
afterEach(() => jest.useRealTimers());

describe('ServerWake', () => {
  test('fast answer: no waking phase, status ready', async () => {
    const statuses = [];
    ServerWake.subscribe((s) => statuses.push(s.status));
    APIClient.health.mockResolvedValue({ status: 'ok' });
    await expect(ServerWake.ensureAwake()).resolves.toBe(true);
    expect(statuses).toEqual(['checking', 'ready']);
    expect(APIClient.health).toHaveBeenCalledWith(WAKE_TIMEOUT_MS);
  });

  test('slow answer: waking after 3 s, then ready', async () => {
    const d = deferred();
    APIClient.health.mockReturnValue(d.promise);
    const p = ServerWake.ensureAwake();
    jest.advanceTimersByTime(QUIET_MS - 1);
    expect(ServerWake.getState().status).toBe('checking');
    jest.advanceTimersByTime(1);
    expect(ServerWake.getState().status).toBe('waking');
    d.resolve({ status: 'ok' });
    await expect(p).resolves.toBe(true);
    expect(ServerWake.getState().status).toBe('ready');
  });

  test('concurrent callers share one health check', async () => {
    const d = deferred();
    APIClient.health.mockReturnValue(d.promise);
    const a = ServerWake.ensureAwake();
    const b = ServerWake.ensureAwake();
    d.resolve({});
    await Promise.all([a, b]);
    expect(APIClient.health).toHaveBeenCalledTimes(1);
  });

  test('recently awake: no new health check until 10 minutes pass', async () => {
    APIClient.health.mockResolvedValue({});
    await ServerWake.ensureAwake();
    await ServerWake.ensureAwake();
    expect(APIClient.health).toHaveBeenCalledTimes(1);
    jest.setSystemTime(Date.now() + FRESH_MS);
    await ServerWake.ensureAwake();
    expect(APIClient.health).toHaveBeenCalledTimes(2);
  });

  test('timeout after 90 s -> status timeout, resolves false', async () => {
    const d = deferred();
    APIClient.health.mockReturnValue(d.promise);
    const p = ServerWake.ensureAwake();
    jest.advanceTimersByTime(WAKE_TIMEOUT_MS);
    d.reject(Object.assign(new Error('Timeout'), { isNetworkError: true, code: 'ECONNABORTED' }));
    await expect(p).resolves.toBe(false);
    expect(ServerWake.getState().status).toBe('timeout');
  });

  test('fast network failure -> unreachable (offline queue handles it)', async () => {
    APIClient.health.mockRejectedValue(Object.assign(new Error('Network'), { isNetworkError: true }));
    await expect(ServerWake.ensureAwake()).resolves.toBe(false);
    expect(ServerWake.getState().status).toBe('unreachable');
  });

  test('waitingText formats minutes and seconds', () => {
    expect(waitingText(25_400)).toBe('Waiting for the server to wake up… (0:25)');
    expect(waitingText(65_000)).toBe('Waiting for the server to wake up… (1:05)');
  });
});
