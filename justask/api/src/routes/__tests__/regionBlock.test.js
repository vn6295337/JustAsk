import fs from 'fs';
import request from 'supertest';
import express from 'express';
import morgan from 'morgan';
import { jest } from '@jest/globals';

process.env.RATE_LIMIT_QUERY_PER_MIN = '1000';
process.env.RATE_LIMIT_SYNC_PER_MIN = '1000';

const mockExecute = jest.fn();
jest.unstable_mockModule('../../failover/failover.js', () => ({
  executeWithRankedFallback: mockExecute,
}));
jest.unstable_mockModule('../../utils/supabase.js', () => ({
  getApiKey: jest.fn().mockResolvedValue('test-api-key'),
  testSupabaseConnection: jest.fn().mockResolvedValue(true),
}));

const { default: queryRoutes } = await import('../query.js');
const {
  BLOCKED_COUNTRIES,
  REGION_BLOCKED_MESSAGE,
  DEFAULT_GEO_DB_PATH,
  loadGeoDb,
  setGeoReader,
  normalizeIp,
  lookupCountry,
} = await import('../../middleware/regionBlock.js');

// Fake geo database
const GB = '81.2.69.142';
const DE6 = '2a00:1450:4001:800::200e';
const US = '8.8.8.8';
const UNKNOWN = '10.0.0.1';
const fakeDb = {
  [GB]: 'GB',
  [DE6]: 'DE',
  [US]: 'US',
};
const fakeReader = {
  get: (ip) => (fakeDb[ip] ? { country: { iso_code: fakeDb[ip] } } : null),
};

const buildApp = (logStream) => {
  const a = express();
  a.set('trust proxy', 1);
  if (logStream) a.use(morgan('tiny', { stream: logStream }));
  a.use(express.json({ limit: '256kb' }));
  a.get('/api/health', (req, res) => res.json({ status: 'ok' }));
  a.use('/api', queryRoutes);
  return a;
};

beforeEach(() => {
  setGeoReader(fakeReader);
  mockExecute.mockReset();
  mockExecute.mockResolvedValue({
    success: true,
    response: 'answer',
    llm_used: 'groq',
    model_name: 'm',
    model_rank: 1,
    failover_count: 0,
  });
});

describe('normalizeIp', () => {
  test('strips IPv4-mapped IPv6 prefix', () => {
    expect(normalizeIp(`::ffff:${GB}`)).toBe(GB);
  });
  test('keeps plain IPv6', () => {
    expect(normalizeIp(DE6)).toBe(DE6);
  });
  test('strips IPv6 zone index', () => {
    expect(normalizeIp('fe80::1%eth0')).toBe('fe80::1');
  });
  test('rejects empty and invalid input', () => {
    expect(normalizeIp('')).toBeNull();
    expect(normalizeIp(undefined)).toBeNull();
    expect(normalizeIp('not-an-ip')).toBeNull();
  });
});

describe('blocked country list', () => {
  test('covers EU, EEA, UK, Switzerland and EU territories', () => {
    for (const c of ['DE', 'FR', 'IE', 'IS', 'LI', 'NO', 'GB', 'CH', 'AX', 'RE', 'GP', 'MQ', 'GF', 'YT', 'MF']) {
      expect(BLOCKED_COUNTRIES.has(c)).toBe(true);
    }
    expect(BLOCKED_COUNTRIES.has('US')).toBe(false);
  });
});

describe('region block middleware', () => {
  const app = buildApp();

  test.each(['/api/query', '/api/queue/sync'])('451 for a UK address on %s', async (route) => {
    const body = route === '/api/query' ? { query: 'hi' } : { queries: [{ id: 1, query: 'hi', timestamp: 1 }] };
    const res = await request(app).post(route).set('X-Forwarded-For', GB).send(body);
    expect(res.status).toBe(451);
    expect(res.body.error).toBe(REGION_BLOCKED_MESSAGE);
    expect(res.body.code).toBe('REGION_BLOCKED');
    expect(mockExecute).not.toHaveBeenCalled();
  });

  test('451 for an IPv6 address in Germany', async () => {
    const res = await request(app).post('/api/query').set('X-Forwarded-For', DE6).send({ query: 'hi' });
    expect(res.status).toBe(451);
  });

  test('451 for an IPv4-mapped IPv6 UK address', async () => {
    const res = await request(app).post('/api/query').set('X-Forwarded-For', `::ffff:${GB}`).send({ query: 'hi' });
    expect(res.status).toBe(451);
  });

  test('US address is allowed', async () => {
    const res = await request(app).post('/api/query').set('X-Forwarded-For', US).send({ query: 'hi' });
    expect(res.status).toBe(200);
  });

  test('unknown country is allowed', async () => {
    const res = await request(app).post('/api/query').set('X-Forwarded-For', UNKNOWN).send({ query: 'hi' });
    expect(res.status).toBe(200);
  });

  test('health check is never blocked', async () => {
    const res = await request(app).get('/api/health').set('X-Forwarded-For', GB);
    expect(res.status).toBe(200);
  });

  test('fails closed (503) when the geo database is not loaded', async () => {
    setGeoReader(null);
    const res = await request(app).post('/api/query').set('X-Forwarded-For', US).send({ query: 'hi' });
    expect(res.status).toBe(503);
    expect(mockExecute).not.toHaveBeenCalled();
    expect(() => lookupCountry(US)).toThrow();
  });

  test('loadGeoDb rejects when the file is missing', async () => {
    await expect(loadGeoDb('/nonexistent/geo.mmdb')).rejects.toThrow();
  });
});

describe('logs contain no client IP', () => {
  test('request log and block log omit the address', async () => {
    const lines = [];
    const stream = { write: (l) => lines.push(l) };
    const spy = jest.spyOn(console, 'log').mockImplementation((...a) => lines.push(a.join(' ')));
    try {
      const app = buildApp(stream);
      await request(app).post('/api/query').set('X-Forwarded-For', GB).send({ query: 'hi' });
      await request(app).post('/api/query').set('X-Forwarded-For', US).send({ query: 'hi' });
    } finally {
      spy.mockRestore();
    }
    expect(lines.length).toBeGreaterThan(0);
    for (const l of lines) {
      expect(l).not.toContain(GB);
      expect(l).not.toContain(US);
    }
  });
});

// Runs only when the real database has been downloaded (npm install)
const withRealDb = fs.existsSync(DEFAULT_GEO_DB_PATH) ? describe : describe.skip;
withRealDb('real DB-IP database', () => {
  beforeAll(async () => {
    await loadGeoDb();
  });
  test('resolves known addresses', () => {
    expect(lookupCountry(US)).toBe('US');
    expect(lookupCountry(GB)).toBe('GB');
    expect(lookupCountry(DE6)).toBe('DE');
    expect(lookupCountry(`::ffff:${GB}`)).toBe('GB');
  });
});
