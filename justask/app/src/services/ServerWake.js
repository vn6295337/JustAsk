import APIClient from './APIClient';

/**
 * Tracks whether the backend is awake. On Render's free plan the server
 * sleeps after 15 minutes without traffic and takes about a minute to wake.
 *
 * Status: 'unknown' | 'checking' | 'waking' | 'ready' | 'timeout' | 'unreachable'
 * - checking: health request sent, under QUIET_MS (no banner yet)
 * - waking: still no answer after QUIET_MS (show the banner)
 * - timeout: no answer within WAKE_TIMEOUT_MS
 * - unreachable: fast network failure (offline); the offline queue handles it
 */
export const QUIET_MS = 3000;
export const WAKE_TIMEOUT_MS = 90000;
// Server sleeps after 15 min idle; re-check if we have not heard from it in 10
export const FRESH_MS = 10 * 60 * 1000;

/** "Waiting for the server to wake up… (0:25)" */
export const waitingText = (elapsedMs) => {
  const s = Math.max(0, Math.floor(elapsedMs / 1000));
  return `Waiting for the server to wake up\u2026 (${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')})`;
};

let state = { status: 'unknown', startedAt: null };
let lastOkAt = 0;
let inFlight = null;
const listeners = new Set();

const setState = (next) => {
  state = { ...state, ...next };
  listeners.forEach((fn) => fn(state));
};

const ServerWake = {
  getState: () => state,

  /** Subscribe to status changes. Returns an unsubscribe function. */
  subscribe: (fn) => {
    listeners.add(fn);
    return () => listeners.delete(fn);
  },

  /** Record any successful server response (keeps the "awake" window fresh). */
  markOk: () => {
    lastOkAt = Date.now();
    if (state.status !== 'ready') setState({ status: 'ready' });
  },

  /**
   * Make sure the server is awake. Resolves true when it answers,
   * false on timeout or a network failure. Concurrent calls share one check.
   */
  ensureAwake: () => {
    if (Date.now() - lastOkAt < FRESH_MS) return Promise.resolve(true);
    if (inFlight) return inFlight;

    const startedAt = Date.now();
    setState({ status: 'checking', startedAt });
    const quietTimer = setTimeout(() => {
      if (state.status === 'checking') setState({ status: 'waking' });
    }, QUIET_MS);

    inFlight = APIClient.health(WAKE_TIMEOUT_MS)
      .then(() => {
        ServerWake.markOk();
        return true;
      })
      .catch((error) => {
        const timedOut = Date.now() - startedAt >= WAKE_TIMEOUT_MS - 1000 || error?.code === 'ECONNABORTED';
        setState({ status: timedOut ? 'timeout' : 'unreachable' });
        return false;
      })
      .finally(() => {
        clearTimeout(quietTimer);
        inFlight = null;
      });
    return inFlight;
  },

  /** Test helper */
  _reset: () => {
    state = { status: 'unknown', startedAt: null };
    lastOkAt = 0;
    inFlight = null;
    listeners.clear();
  },
};

export default ServerWake;
