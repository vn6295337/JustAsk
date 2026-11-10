import { jest } from '@jest/globals';

const callGemini = jest.fn();
const callGroq = jest.fn();
const callOpenRouter = jest.fn();
const getModelFallbackChain = jest.fn();

jest.unstable_mockModule('../../providers/gemini.js', () => ({ callGemini }));
jest.unstable_mockModule('../../providers/groq.js', () => ({ callGroq }));
jest.unstable_mockModule('../../providers/openrouter.js', () => ({ callOpenRouter }));
jest.unstable_mockModule('../../routing/rankedModelSelector.js', () => ({ getModelFallbackChain }));

const { executeWithRankedFallback } = await import('../failover.js');
const { ProviderError } = await import('../../utils/errors.js');
const { default: config } = await import('../../config.js');

const chain = [
  { provider: 'groq', modelName: 'model-a', rank: 1 },
  { provider: 'groq', modelName: 'model-b', rank: 2 },
  { provider: 'gemini', modelName: 'model-c', rank: 3 },
];

beforeEach(() => {
  jest.clearAllMocks();
  getModelFallbackChain.mockResolvedValue(chain);
});

describe('executeWithRankedFallback', () => {
  test('passes each ranked modelName to its provider', async () => {
    callGroq.mockRejectedValueOnce(new ProviderError('groq', 'Empty completion', 502));
    callGroq.mockResolvedValueOnce({ response: 'ok', model: 'model-b' });
    const r = await executeWithRankedFallback('q', 'general_knowledge');
    expect(callGroq.mock.calls[0][1]).toBe('model-a');
    expect(callGroq.mock.calls[1][1]).toBe('model-b');
    expect(r.success).toBe(true);
    expect(r.model_name).toBe('model-b');
    expect(r.failover_count).toBe(1);
  });

  test('empty-completion errors advance failover to next model', async () => {
    callGroq.mockRejectedValue(new ProviderError('groq', 'Empty completion', 502));
    callGemini.mockResolvedValue({ response: 'from gemini', model: 'model-c' });
    const r = await executeWithRankedFallback('q', 'general_knowledge');
    expect(r.success).toBe(true);
    expect(r.llm_used).toBe('gemini');
    expect(callGemini).toHaveBeenCalledWith('q', 'model-c');
  });

  test('all 429 -> status 429 with generic message', async () => {
    callGroq.mockRejectedValue(new ProviderError('groq', 'quota: secret-detail', 429));
    callGemini.mockRejectedValue(new ProviderError('gemini', 'quota: secret-detail', 429));
    const r = await executeWithRankedFallback('q', 'general_knowledge');
    expect(r.success).toBe(false);
    expect(r.status).toBe(429);
    expect(r.error).not.toContain('secret');
  });

  test('non-429 failure -> status 500 with generic message', async () => {
    callGroq.mockRejectedValue(new ProviderError('groq', 'boom internal', 503));
    callGemini.mockRejectedValue(new ProviderError('gemini', 'boom internal', 503));
    const r = await executeWithRankedFallback('q', 'general_knowledge');
    expect(r.status).toBe(500);
    expect(r.error).not.toContain('boom');
  });

  test('hardcoded fallback entries pass null modelName so provider defaults apply', async () => {
    getModelFallbackChain.mockResolvedValue([{ provider: 'groq', modelName: 'stale-name', rank: 0, fallback: true }]);
    callGroq.mockResolvedValue({ response: 'ok', model: 'default-model' });
    await executeWithRankedFallback('q', 'business_news');
    expect(callGroq.mock.calls[0][1]).toBe(config.models.groqCompound);
  });
});
