import { jest } from '@jest/globals';

const create = jest.fn();
jest.unstable_mockModule('groq-sdk', () => ({
  default: class { constructor() { this.chat = { completions: { create } }; } },
}));
jest.unstable_mockModule('../../utils/supabase.js', () => ({
  getApiKey: jest.fn().mockResolvedValue('k'),
}));

const { callGroq } = await import('../groq.js');
const { normalizeStatus, withTimeout, ProviderError } = await import('../../utils/errors.js');

describe('providers', () => {
  test('groq: empty completion throws ProviderError (not a placeholder)', async () => {
    create.mockResolvedValue({ choices: [{ message: { content: '' }, finish_reason: 'length' }] });
    await expect(callGroq('q', 'm')).rejects.toMatchObject({ name: 'ProviderError', status: 502 });
  });

  test('groq: passes modelName and preserves upstream 429 status/message', async () => {
    const err = Object.assign(new Error('rate limited'), { status: 429 });
    create.mockRejectedValue(err);
    await expect(callGroq('q', 'my-model')).rejects.toMatchObject({ status: 429, message: 'rate limited' });
    expect(create.mock.calls.at(-1)[0].model).toBe('my-model');
    expect(create.mock.calls.at(-1)[1].timeout).toBeGreaterThan(0);
  });

  test('normalizeStatus maps timeouts to 504 and unknown codes to 502', () => {
    expect(normalizeStatus({ code: 'ECONNABORTED' })).toBe(504);
    expect(normalizeStatus({ code: 'ENOTFOUND' })).toBe(502);
    expect(normalizeStatus({ response: { status: 429 } })).toBe(429);
  });

  test('withTimeout rejects with 504 ProviderError', async () => {
    await expect(withTimeout(new Promise(() => {}), 20, 'x')).rejects.toBeInstanceOf(ProviderError);
  });
});
