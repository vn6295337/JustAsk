import { jest } from '@jest/globals';

let result = { data: [], error: null };
let calls = 0;
const builder = () => {
  const b = {
    schema: () => b,
    from: () => b,
    select: () => b,
    order: () => b,
    limit: () => {
      calls++;
      return Promise.resolve(typeof result === 'function' ? result() : result);
    },
  };
  return b;
};
jest.unstable_mockModule('../../utils/supabase.js', () => ({
  getSupabase: () => builder(),
  getApiKey: jest.fn(),
}));

const { fetchRankedModels, getModelFallbackChain, _resetSelectorCache } = await import(
  '../rankedModelSelector.js'
);

const rows = [
  { model_name: 'Model A', inference_provider: 'Groq', provider_slug: 'model-a', intelligence_index: 50, selection_score: 0.8 },
  { model_name: 'Model B', inference_provider: 'openrouter', provider_slug: 'org/model-b:free', intelligence_index: 40, selection_score: 0.7 },
];

beforeEach(() => {
  _resetSelectorCache();
  calls = 0;
  result = { data: rows, error: null };
  jest.spyOn(console, 'error').mockImplementation(() => {});
  jest.spyOn(console, 'warn').mockImplementation(() => {});
});

describe('rankedModelSelector (direct Supabase read)', () => {
  test('maps rows to a ranked chain with lowercase providers', async () => {
    const chain = await getModelFallbackChain();
    expect(chain).toEqual([
      { provider: 'groq', modelName: 'model-a', rank: 1, selectionScore: 0.8, intelligenceIndex: 50 },
      { provider: 'openrouter', modelName: 'org/model-b:free', rank: 2, selectionScore: 0.7, intelligenceIndex: 40 },
    ]);
  });

  test('caches the ranking (one database read for repeated calls)', async () => {
    await fetchRankedModels();
    await fetchRankedModels();
    expect(calls).toBe(1);
  });

  test('database error with no cached ranking -> hardcoded fallback chain', async () => {
    result = { data: null, error: { message: 'down' } };
    const chain = await getModelFallbackChain();
    expect(chain.every((m) => m.fallback)).toBe(true);
  });

  test('empty table -> hardcoded fallback chain', async () => {
    result = { data: [], error: null };
    const chain = await getModelFallbackChain();
    expect(chain.every((m) => m.fallback)).toBe(true);
  });
});
