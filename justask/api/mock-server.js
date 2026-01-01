/**
 * Mock Server for Integration Testing
 * Simulates various failure scenarios for LLM providers and Router
 */

import express from 'express';

const app = express();
app.use(express.json());

// Configuration - control behavior via query params or headers
let mockMode = 'success'; // 'success', 'all-fail', 'empty-models', 'timeout', 'rate-limit'

// Middleware to check mock mode from header
app.use((req, res, next) => {
  if (req.headers['x-mock-mode']) {
    mockMode = req.headers['x-mock-mode'];
  }
  next();
});

// Control endpoint to set mock mode
app.post('/mock/mode', (req, res) => {
  mockMode = req.body.mode || 'success';
  console.log(`[MockServer] Mode set to: ${mockMode}`);
  res.json({ mode: mockMode });
});

app.get('/mock/mode', (req, res) => {
  res.json({ mode: mockMode });
});

// Mock Router /best-models endpoint
app.get('/best-models', async (req, res) => {
  console.log(`[MockRouter] /best-models called, mode: ${mockMode}`);

  if (mockMode === 'empty-models') {
    return res.json({ models: [], count: 0, timestamp: new Date().toISOString() });
  }

  if (mockMode === 'router-down') {
    return res.status(503).json({ error: 'Service unavailable' });
  }

  if (mockMode === 'timeout') {
    // Simulate 10s delay
    await new Promise(r => setTimeout(r, 10000));
  }

  // Return mock models that will fail
  res.json({
    models: [
      { rank: 1, provider: 'Groq', modelName: 'mock-model-1', selectionScore: 0.9, intelligenceIndex: 90 },
      { rank: 2, provider: 'Google', modelName: 'mock-model-2', selectionScore: 0.8, intelligenceIndex: 85 },
      { rank: 3, provider: 'OpenRouter', modelName: 'mock-model-3', selectionScore: 0.7, intelligenceIndex: 80 }
    ],
    count: 3,
    timestamp: new Date().toISOString()
  });
});

// Mock Router /health endpoint
app.get('/health', (req, res) => {
  if (mockMode === 'router-down') {
    return res.status(503).json({ error: 'Service unavailable' });
  }
  res.json({ status: 'ok', mode: mockMode, timestamp: new Date().toISOString() });
});

// Mock Groq endpoint
app.post('/openai/v1/chat/completions', (req, res) => {
  console.log(`[MockGroq] Called, mode: ${mockMode}`);

  if (mockMode === 'all-fail' || mockMode === 'rate-limit') {
    return res.status(429).json({ error: { message: 'Rate limit exceeded' } });
  }

  if (mockMode === 'server-error') {
    return res.status(500).json({ error: { message: 'Internal server error' } });
  }

  if (mockMode === 'timeout') {
    // Don't respond (timeout)
    return;
  }

  res.json({
    choices: [{ message: { content: 'Mock Groq response' } }],
    model: 'mock-groq-model'
  });
});

// Mock Gemini endpoint
app.post('/v1beta/models/*', (req, res) => {
  console.log(`[MockGemini] Called, mode: ${mockMode}`);

  if (mockMode === 'all-fail') {
    return res.status(500).json({ error: { message: 'Service unavailable' } });
  }

  if (mockMode === 'timeout') {
    return;
  }

  res.json({
    candidates: [{ content: { parts: [{ text: 'Mock Gemini response' }] } }]
  });
});

// Mock OpenRouter endpoint
app.post('/api/v1/chat/completions', (req, res) => {
  console.log(`[MockOpenRouter] Called, mode: ${mockMode}`);

  if (mockMode === 'all-fail') {
    return res.status(503).json({ error: { message: 'Service unavailable' } });
  }

  if (mockMode === 'timeout') {
    return;
  }

  res.json({
    choices: [{ message: { content: 'Mock OpenRouter response' } }],
    model: 'mock-openrouter-model'
  });
});

const PORT = process.env.MOCK_PORT || 4000;
app.listen(PORT, () => {
  console.log(`[MockServer] Running on port ${PORT}`);
  console.log(`[MockServer] Modes: success, all-fail, empty-models, router-down, timeout, rate-limit, server-error`);
  console.log(`[MockServer] Set mode: POST /mock/mode {mode: "..."}`);
});
