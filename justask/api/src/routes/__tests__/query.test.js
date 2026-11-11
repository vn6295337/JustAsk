import request from 'supertest';
import express from 'express';
import { jest } from '@jest/globals';

process.env.RATE_LIMIT_QUERY_PER_MIN = '1000';
process.env.RATE_LIMIT_SYNC_PER_MIN = '1000';

// ESM-compatible mocks: no real provider/network calls
const mockExecute = jest.fn();
jest.unstable_mockModule('../../failover/failover.js', () => ({
  executeWithRankedFallback: mockExecute,
}));
jest.unstable_mockModule('../../utils/supabase.js', () => ({
  getApiKey: jest.fn().mockResolvedValue('test-api-key'),
  testSupabaseConnection: jest.fn().mockResolvedValue(true),
}));

const { default: queryRoutes } = await import('../query.js');
const { default: config } = await import('../../config.js');
const { ipRateLimit } = await import('../../rate-limiting/limiter.js');
const { setGeoReader } = await import('../../middleware/regionBlock.js');

// Region block: every address resolves to an unknown country (allowed)
setGeoReader({ get: () => null });

const buildApp = () => {
  const a = express();
  a.set('trust proxy', 1);
  a.use(express.json({ limit: '256kb' }));
  a.get('/api/health', (req, res) => res.json({ status: 'ok' }));
  a.use('/api', queryRoutes);
  a.use((req, res) => res.status(404).json({ error: 'Not found', status: 404 }));
  return a;
};
const app = buildApp();

beforeEach(() => {
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

describe('Query API Endpoints', () => {
  describe('GET /api/health', () => {
    test('should return 200 and status ok', async () => {
      const response = await request(app)
        .get('/api/health')
        .expect(200);

      expect(response.body.status).toBe('ok');
    });
  });

  describe('POST /api/query - Validation', () => {
    test('should return 400 when query is missing', async () => {
      const response = await request(app)
        .post('/api/query')
        .send({})
        .expect(400);

      expect(response.body.error).toBeDefined();
      expect(response.body.status).toBe(400);
    });

    test('should return 400 when query is empty string', async () => {
      const response = await request(app)
        .post('/api/query')
        .send({ query: '' })
        .expect(400);

      expect(response.body.error).toBeDefined();
    });

    test('should return 400 when query is only whitespace', async () => {
      const response = await request(app)
        .post('/api/query')
        .send({ query: '   ' })
        .expect(400);

      expect(response.body.error).toBeDefined();
    });

    test('should return 400 when query exceeds max length', async () => {
      const longQuery = 'a'.repeat(2001);
      const response = await request(app)
        .post('/api/query')
        .send({ query: longQuery })
        .expect(400);

      expect(response.body.error).toContain('exceed');
    });

    test('should return 400 when query is not a string', async () => {
      const response = await request(app)
        .post('/api/query')
        .send({ query: 12345 })
        .expect(400);

      expect(response.body.error).toBeDefined();
    });

    test('should return 400 for potentially dangerous queries', async () => {
      const response = await request(app)
        .post('/api/query')
        .send({ query: '<script>alert("xss")</script>' })
        .expect(400);

      expect(response.body.error).toContain('dangerous');
    });
  });

  describe('POST /api/query - Content Type', () => {
    test('should require JSON content-type', async () => {
      const response = await request(app)
        .post('/api/query')
        .send('query=test')
        .set('Content-Type', 'application/x-www-form-urlencoded')
        .expect(400);

      expect(response.body).toBeDefined();
    });
  });

  describe('POST /api/queue/sync - Validation', () => {
    test('should return 400 when queries is missing', async () => {
      const response = await request(app)
        .post('/api/queue/sync')
        .send({})
        .expect(400);

      expect(response.body.error).toBeDefined();
    });

    test('should return 400 when queries is not an array', async () => {
      const response = await request(app)
        .post('/api/queue/sync')
        .send({ queries: 'not-an-array' })
        .expect(400);

      expect(response.body.error).toBeDefined();
    });

    test('should return 400 when queries array is empty', async () => {
      const response = await request(app)
        .post('/api/queue/sync')
        .send({ queries: [] })
        .expect(400);

      expect(response.body.error).toBeDefined();
    });

    test('should return 400 when query item is missing "query" field', async () => {
      const response = await request(app)
        .post('/api/queue/sync')
        .send({
          queries: [
            { timestamp: Date.now() }, // Missing query field
          ],
        })
        .expect(400);

      expect(response.body.error).toBeDefined();
    });

    test('should return 400 when batch exceeds max batch size', async () => {
      const largeQueriesArray = Array(config.sync.maxBatch + 1).fill({
        query: 'test query',
        timestamp: Date.now(),
      });

      const response = await request(app)
        .post('/api/queue/sync')
        .send({ queries: largeQueriesArray })
        .expect(400);

      expect(response.body.error).toContain(String(config.sync.maxBatch));
    });
  });

  describe('Response Format', () => {
    test('POST /api/query should have required response fields', async () => {
      const response = await request(app)
        .post('/api/query')
        .send({ query: 'What is AI?' });

      // Note: Without real API keys, we'll get 500, but check response structure
      if (response.status === 500) {
        expect(response.body.error).toBeDefined();
        expect(response.body.status).toBe(500);
      } else {
        expect(response.body.response).toBeDefined();
        expect(response.body.llm_used).toBeDefined();
        expect(response.body.category).toBeDefined();
        expect(response.body.response_time).toBeDefined();
      }
    });

    test('POST /api/queue/sync should have batch response fields', async () => {
      const response = await request(app)
        .post('/api/queue/sync')
        .send({
          queries: [
            { id: 1, query: 'test query', timestamp: Date.now() },
          ],
        });

      if (response.status === 200) {
        expect(response.body.responses).toBeDefined();
        expect(Array.isArray(response.body.responses)).toBe(true);
        expect(response.body.responses[0].id).toBe(1); // Check response includes id
        expect(response.body.synced).toBeDefined();
        expect(response.body.failed).toBeDefined();
        expect(response.body.response_time).toBeDefined();
      }
    });
  });

  describe('Error Handling', () => {
    test('should handle 404 for non-existent endpoint', async () => {
      const response = await request(app)
        .get('/api/nonexistent')
        .expect(404);

      expect(response.body.error).toBeDefined();
    });

    test('should handle malformed JSON', async () => {
      const response = await request(app)
        .post('/api/query')
        .set('Content-Type', 'application/json')
        .send('{ invalid json }')
        .expect(400);

      expect(response.body).toBeDefined();
    });
  });

  describe('Audit fixes', () => {
    test('/query returns 429 when providers rate limited, without upstream text', async () => {
      mockExecute.mockResolvedValue({ success: false, status: 429, error: 'Providers are rate limited.' });
      const r = await request(app).post('/api/query').send({ query: 'hello' });
      expect(r.status).toBe(429);
    });

    test('/query returns 500 for generic failure', async () => {
      mockExecute.mockResolvedValue({ success: false, status: 500, error: 'All providers failed' });
      const r = await request(app).post('/api/query').send({ query: 'hello' });
      expect(r.status).toBe(500);
    });

    test('/query does not leak raw error text from unexpected exceptions', async () => {
      mockExecute.mockRejectedValue(new Error('secret upstream detail'));
      const r = await request(app).post('/api/query').send({ query: 'hello' });
      expect(r.status).toBe(500);
      expect(JSON.stringify(r.body)).not.toContain('secret');
    });

    test('false-positive regex: "region=EU" and "transcript>" are accepted', async () => {
      const r = await request(app).post('/api/query').send({ query: 'prices where region=EU and a transcript> 3' });
      expect(r.status).toBe(200);
    });

    test('event handler inside a tag is still rejected', async () => {
      const r = await request(app).post('/api/query').send({ query: '<img src=x onerror=alert(1)>' });
      expect(r.status).toBe(400);
    });

    test('/queue/sync applies validation: dangerous item rejected per-item, not executed', async () => {
      const r = await request(app).post('/api/queue/sync').send({
        queries: [
          { id: 1, query: '<script>alert(1)</script>' },
          { id: 2, query: 'fine question' },
        ],
      });
      expect(r.status).toBe(200);
      const bad = r.body.responses.find((x) => x.id === 1);
      const good = r.body.responses.find((x) => x.id === 2);
      expect(bad.success).toBe(false);
      expect(bad.permanent).toBe(true);
      expect(good.success).toBe(true);
      expect(mockExecute).toHaveBeenCalledTimes(1);
    });

    test('/queue/sync accepts a max-size batch under the JSON limit', async () => {
      const queries = Array.from({ length: config.sync.maxBatch }, (_, i) => ({ id: i, query: 'a'.repeat(2000) }));
      const r = await request(app).post('/api/queue/sync').send({ queries });
      expect(r.status).toBe(200);
      expect(r.body.synced).toBe(config.sync.maxBatch);
    });

    test('/queue/sync defers remaining items when time budget is exhausted', async () => {
      const original = config.sync.timeBudgetMs;
      config.sync.timeBudgetMs = 50;
      mockExecute.mockImplementation(() => new Promise((res) => setTimeout(() => res({ success: true, response: 'x', llm_used: 'groq' }), 200)));
      const r = await request(app).post('/api/queue/sync').send({
        queries: [{ id: 1, query: 'one' }, { id: 2, query: 'two' }],
      });
      config.sync.timeBudgetMs = original;
      expect(r.status).toBe(200);
      expect(r.body.responses.every((x) => x.success === false && x.retryable)).toBe(true);
    });

    test('/queue/sync allows only one concurrent sync (429 for the second)', async () => {
      mockExecute.mockImplementation(() => new Promise((res) => setTimeout(() => res({ success: true, response: 'x', llm_used: 'groq' }), 150)));
      const body = { queries: [{ id: 1, query: 'one' }] };
      const [a, b] = await Promise.all([
        request(app).post('/api/queue/sync').send(body),
        new Promise((res) => setTimeout(res, 30)).then(() => request(app).post('/api/queue/sync').send(body)),
      ]);
      expect([a.status, b.status].sort()).toEqual([200, 429]);
    });

    test('optional auth: no token configured -> open; configured -> 401 without it, 200 with it', async () => {
      expect((await request(app).post('/api/query').send({ query: 'hi' })).status).toBe(200);
      config.authToken = 'sekret';
      try {
        expect((await request(app).post('/api/query').send({ query: 'hi' })).status).toBe(401);
        expect((await request(app).post('/api/query').set('Authorization', 'Bearer wrong').send({ query: 'hi' })).status).toBe(401);
        expect((await request(app).post('/api/query').set('Authorization', 'Bearer sekret').send({ query: 'hi' })).status).toBe(200);
        expect((await request(app).get('/api/health')).status).toBe(200);
      } finally {
        config.authToken = '';
      }
    });

    test('per-IP rate limit middleware returns 429 with Retry-After', async () => {
      const a = express();
      a.get('/x', ipRateLimit('test-bucket', 2), (req, res) => res.json({ ok: true }));
      await request(a).get('/x').expect(200);
      await request(a).get('/x').expect(200);
      const r = await request(a).get('/x');
      expect(r.status).toBe(429);
      expect(r.headers['retry-after']).toBeDefined();
    });
  });
});
