/**
 * Tests for Model Selector (real tracker + cache, mocked DB layer)
 */

import { jest } from '@jest/globals';

const mockFetchLatestModels = jest.fn();

jest.unstable_mockModule('../../utils/supabase.js', () => ({
  fetchLatestModels: mockFetchLatestModels,
  default: {}
}));

const {
  filterByModalities,
  calculateScores,
  matchComplexityToHeadroom,
  selectBestModel,
  selectModel,
  trackerKey
} = await import('../modelSelector.js');
const { default: rateLimitTracker } = await import('../../utils/rateLimitTracker.js');
const { default: cacheManager } = await import('../cacheManager.js');

function model(overrides = {}) {
  return {
    inference_provider: 'groq',
    model_provider: 'Meta',
    human_readable_name: 'llama-3-3-70b',
    input_modalities: 'Text',
    output_modalities: 'Text',
    license_name: 'Llama-3.3',
    model_provider_country: 'United States',
    aa_slug: null,
    aa_performance_metrics: null,
    rate_limits_normalized: { rpm: 30, rpd: 1000, tpm: 100000, tpd: 1000000 },
    ...overrides
  };
}

const MODELS = [
  model({
    human_readable_name: 'llama-3-3-70b',
    aa_slug: 'llama-3-3-instruct-70b',
    aa_performance_metrics: { aa_slug: 'llama-3-3-instruct-70b', intelligence_index: 90 }
  }),
  model({
    inference_provider: 'openrouter',
    human_readable_name: 'tiny-model-1b',
    license_name: 'MIT',
    rate_limits_normalized: { rpm: 20, rpd: 50 }
  }),
  model({
    inference_provider: 'google',
    human_readable_name: 'gemini-flash',
    input_modalities: 'Text, Image',
    license_name: 'Gemini',
    rate_limits_normalized: { rpm: 15 }
  })
];

describe('ModelSelector', () => {
  beforeEach(() => {
    delete process.env.ARTIFICIALANALYSIS_API_KEY;
    delete process.env.ARTIFICIAL_ANALYSIS_API_KEY;
    cacheManager.clear();
    rateLimitTracker.modelTracking = {};
    mockFetchLatestModels.mockReset();
    mockFetchLatestModels.mockResolvedValue(MODELS.map(m => ({ ...m })));
  });

  afterAll(() => {
    rateLimitTracker.stopCleanup();
  });

  describe('filterByModalities', () => {
    it('filters by image input', () => {
      const filtered = filterByModalities(MODELS, ['text', 'image']);
      expect(filtered.map(m => m.human_readable_name)).toEqual(['gemini-flash']);
    });

    it('excludes embedding-only models', () => {
      const emb = model({ human_readable_name: 'emb', output_modalities: 'Embeddings' });
      expect(filterByModalities([...MODELS, emb], ['text'])).toHaveLength(3);
    });

    it('returns all for empty/undefined modalities', () => {
      expect(filterByModalities(MODELS, [])).toHaveLength(3);
      expect(filterByModalities(MODELS)).toHaveLength(3);
    });
  });

  describe('calculateScores', () => {
    it('uses the mapped AA slug for intelligence score', () => {
      const scored = calculateScores(MODELS, 'general_knowledge', 0.5, { 'llama-3-3-instruct-70b': 0.77 });
      const llama = scored.find(m => m.human_readable_name === 'llama-3-3-70b');
      expect(llama.intelligenceScore).toBe(0.77);
    });

    it('falls back to joined metrics, then size, for unmapped models', () => {
      const scored = calculateScores(MODELS, 'general_knowledge', 0.5, {});
      expect(scored.find(m => m.human_readable_name === 'llama-3-3-70b').intelligenceScore).toBeCloseTo(0.9);
      expect(scored.find(m => m.human_readable_name === 'tiny-model-1b').intelligenceScore).toBe(0.3);
      expect(scored.find(m => m.human_readable_name === 'gemini-flash').intelligenceScore).toBe(0.6);
    });

    it('does not throw on a null inference_provider', () => {
      const bad = model({ inference_provider: null, human_readable_name: 'nullprov' });
      expect(() => calculateScores([bad], 'x', 0.5, {})).not.toThrow();
    });
  });

  describe('matchComplexityToHeadroom', () => {
    it('excludes exhausted models even at low complexity', () => {
      const m = model({ human_readable_name: 'ex' });
      rateLimitTracker.initializeModel(trackerKey(m), { rpm: 1 }, 'groq');
      rateLimitTracker.recordUsage(trackerKey(m), 'hi');
      expect(rateLimitTracker.getHeadroom(trackerKey(m))).toBe(0);
      expect(matchComplexityToHeadroom([m], 0.1)).toHaveLength(0);
    });

    it('requires more headroom for high complexity', () => {
      const m = model({ human_readable_name: 'half' });
      rateLimitTracker.initializeModel(trackerKey(m), { rpm: 2, rpd: null, tpm: null }, 'groq');
      rateLimitTracker.recordUsage(trackerKey(m), 'hi'); // rpm headroom 0.5
      expect(matchComplexityToHeadroom([m], 0.5)).toHaveLength(1);
      expect(matchComplexityToHeadroom([m], 0.9)).toHaveLength(0);
    });
  });

  describe('selectBestModel', () => {
    it('throws on empty input', () => {
      expect(() => selectBestModel([], 'q')).toThrow('No models');
    });
  });

  describe('selectModel (end to end)', () => {
    it('selects the top-scoring model and records usage under the tracker key', async () => {
      const result = await selectModel({
        queryType: 'general_knowledge',
        queryText: 'hello world',
        modalities: ['text'],
        complexityScore: 0.2
      });

      expect(result.provider).toBe('groq');
      expect(result.humanReadableName).toBe('llama-3-3-70b');
      expect(result.intelligenceIndex).toBeCloseTo(0.9);
      const tracking = rateLimitTracker.modelTracking['groq:llama-3-3-70b'];
      expect(tracking.requests).toHaveLength(1);
    });

    it('honors modality filtering', async () => {
      const result = await selectModel({
        queryType: 'x', queryText: 'describe', modalities: ['text', 'image'], complexityScore: 0.2
      });
      expect(result.humanReadableName).toBe('gemini-flash');
    });

    it('does not 500 when a row has a NULL inference_provider', async () => {
      mockFetchLatestModels.mockResolvedValue([
        ...MODELS.map(m => ({ ...m })),
        model({ inference_provider: null, human_readable_name: 'orphan' })
      ]);
      const result = await selectModel({
        queryType: 'x', queryText: 'hello', modalities: ['text'], complexityScore: 0.2
      });
      expect(result.provider).toBeDefined();
    });

    it('keeps separate counters for same-named models on different providers', async () => {
      mockFetchLatestModels.mockResolvedValue([
        model({ human_readable_name: 'same', inference_provider: 'groq' }),
        model({ human_readable_name: 'same', inference_provider: 'openrouter' })
      ]);
      await selectModel({ queryType: 'x', queryText: 'a', modalities: ['text'], complexityScore: 0.1 });
      const used = ['groq:same', 'openrouter:same']
        .map(k => rateLimitTracker.modelTracking[k].requests.length);
      expect(used.sort()).toEqual([0, 1]);
    });

    it('never selects an exhausted model, and throws when all are exhausted', async () => {
      mockFetchLatestModels.mockResolvedValue([
        model({ human_readable_name: 'only', rate_limits_normalized: { rpm: 1, rpd: 1000, tpm: 100000 } })
      ]);
      const criteria = { queryType: 'x', queryText: 'a', modalities: ['text'], complexityScore: 0.1 };
      await selectModel(criteria); // uses the single request
      await expect(selectModel(criteria)).rejects.toThrow('No models');
    });

    it('falls back to remaining models when high complexity cannot be satisfied', async () => {
      mockFetchLatestModels.mockResolvedValue([
        model({ human_readable_name: 'lowroom', rate_limits_normalized: { rpm: 2, rpd: 1000, tpm: 100000 } })
      ]);
      const first = { queryType: 'x', queryText: 'a', modalities: ['text'], complexityScore: 0.1 };
      await selectModel(first); // headroom now 0.5
      const result = await selectModel({ ...first, complexityScore: 0.95 }); // needs 0.6 -> relaxed
      expect(result.humanReadableName).toBe('lowroom');
    });
  });
});
