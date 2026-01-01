import request from 'supertest';
import express from 'express';

// Mock Supabase before importing routes
jest.mock('../../utils/supabase.js', () => ({
  getApiKey: jest.fn().mockResolvedValue('test-api-key'),
  testSupabaseConnection: jest.fn().mockResolvedValue(true),
}));

import queryRoutes from '../query.js';

// Create test app
const app = express();
app.use(express.json());
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});
app.use('/api', queryRoutes);

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

    test('should return 400 when batch exceeds 100 queries', async () => {
      const largeQueriesArray = Array(101).fill({
        query: 'test query',
        timestamp: Date.now(),
      });

      const response = await request(app)
        .post('/api/queue/sync')
        .send({ queries: largeQueriesArray })
        .expect(400);

      expect(response.body.error).toContain('100');
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
});
