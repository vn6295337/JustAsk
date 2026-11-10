import { jest } from '@jest/globals';
import { validateSelectRequest, parseIntParam } from '../utils/validation.js';
import { adminAuth, tokensMatch, buildCorsOptions } from '../middleware/adminAuth.js';
import { parseRateLimits } from '../utils/rateLimitParser.js';

const ok = { queryType: 'general', queryText: 'hello', complexityScore: 0.5 };

describe('validateSelectRequest', () => {
  test('accepts a valid body and defaults modalities', () => {
    expect(validateSelectRequest(ok).value.modalities).toEqual(['text']);
  });

  test.each([
    [{ ...ok, queryText: ['a', 'b'] }, /queryText must be a string/],
    [{ ...ok, queryText: 123 }, /queryText must be a string/],
    [{ ...ok, queryType: {} }, /queryType must be a string/],
    [{ ...ok, complexityScore: 'abc' }, /finite number/],
    [{ ...ok, complexityScore: NaN }, /finite number|Missing/],
    [{ ...ok, complexityScore: 1.5 }, /between 0 and 1/],
    [{ ...ok, complexityScore: '0.5' }, /finite number/],
    [{ ...ok, modalities: 'text' }, /modalities/],
    [{ ...ok, modalities: [1] }, /modalities/],
    [{ ...ok, queryText: undefined }, /Missing required field: queryText/],
    [null, /Missing required field: queryType/],
    [[], /Missing required field: queryType/]
  ])('rejects %j', (body, re) => {
    expect(validateSelectRequest(body).error).toMatch(re);
  });

  test('accepts explicit modalities', () => {
    expect(validateSelectRequest({ ...ok, modalities: ['text', 'image'] }).value.modalities)
      .toEqual(['text', 'image']);
  });
});

describe('parseIntParam', () => {
  test('defaults, valid, invalid', () => {
    expect(parseIntParam(undefined, 1, 50, 5)).toBe(5);
    expect(parseIntParam('10', 1, 50, 5)).toBe(10);
    expect(parseIntParam('abc', 1, 50, 5)).toBeNull();
    expect(parseIntParam('0', 1, 50, 5)).toBeNull();
    expect(parseIntParam('51', 1, 50, 5)).toBeNull();
    expect(parseIntParam(['1', '2'], 1, 50, 5)).toBeNull();
  });
});

describe('adminAuth', () => {
  const mkRes = () => {
    const res = { statusCode: null, body: null };
    res.status = c => { res.statusCode = c; return res; };
    res.json = b => { res.body = b; return res; };
    return res;
  };
  const mkReq = token => ({ get: () => token });
  const saved = process.env.ADMIN_TOKEN;
  afterEach(() => {
    if (saved === undefined) delete process.env.ADMIN_TOKEN; else process.env.ADMIN_TOKEN = saved;
  });

  test('503 when ADMIN_TOKEN unset', () => {
    delete process.env.ADMIN_TOKEN;
    const res = mkRes(); const next = jest.fn();
    adminAuth(mkReq('x'), res, next);
    expect(res.statusCode).toBe(503);
    expect(next).not.toHaveBeenCalled();
  });

  test('401 on missing/wrong token', () => {
    process.env.ADMIN_TOKEN = 'secret';
    for (const t of [undefined, 'wrong', 'secre', 'secrett']) {
      const res = mkRes(); const next = jest.fn();
      adminAuth(mkReq(t), res, next);
      expect(res.statusCode).toBe(401);
      expect(next).not.toHaveBeenCalled();
    }
  });

  test('passes with correct token', () => {
    process.env.ADMIN_TOKEN = 'secret';
    const next = jest.fn();
    adminAuth(mkReq('secret'), mkRes(), next);
    expect(next).toHaveBeenCalled();
    expect(tokensMatch('secret', 'secret')).toBe(true);
  });
});

describe('buildCorsOptions', () => {
  test('unset disables CORS; list and wildcard', () => {
    expect(buildCorsOptions({})).toEqual({ origin: false });
    expect(buildCorsOptions({ CORS_ORIGINS: 'https://a.com, https://b.com' }))
      .toEqual({ origin: ['https://a.com', 'https://b.com'] });
    expect(buildCorsOptions({ CORS_ORIGINS: '*' })).toEqual({ origin: true });
  });
});

describe('parseRateLimits', () => {
  test('comma format with bare /day', () => {
    const r = parseRateLimits('20 requests/min, 50/day', 'openrouter');
    expect(r).toMatchObject({ rpm: 20, rpd: 50, parseable: true });
  });
  test('space format', () => {
    expect(parseRateLimits('20 requests/min 50/day', 'openrouter')).toMatchObject({ rpm: 20, rpd: 50 });
  });
  test('unknown provider with no data is not parseable', () => {
    expect(parseRateLimits('', 'mystery')).toMatchObject({ rpm: null, parseable: false });
  });
});
