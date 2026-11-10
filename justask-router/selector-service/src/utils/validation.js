/**
 * Request validation helpers
 */

export const MAX_QUERY_TEXT_LENGTH = 100000;
export const MAX_MODALITIES = 10;

/**
 * Validate and normalize a /select-model request body.
 * @param {Object} body - Parsed JSON body
 * @returns {{error: string}|{value: Object}} Error message or normalized criteria
 */
export function validateSelectRequest(body) {
  const b = body && typeof body === 'object' && !Array.isArray(body) ? body : {};
  const { queryType, queryText, modalities, complexityScore } = b;

  if (queryType === undefined || queryType === null || queryType === '') {
    return { error: 'Missing required field: queryType' };
  }
  if (typeof queryType !== 'string') {
    return { error: 'queryType must be a string' };
  }

  if (queryText === undefined || queryText === null || queryText === '') {
    return { error: 'Missing required field: queryText' };
  }
  if (typeof queryText !== 'string') {
    return { error: 'queryText must be a string' };
  }
  if (queryText.length > MAX_QUERY_TEXT_LENGTH) {
    return { error: `queryText must be at most ${MAX_QUERY_TEXT_LENGTH} characters` };
  }

  if (complexityScore === undefined || complexityScore === null) {
    return { error: 'Missing required field: complexityScore' };
  }
  if (typeof complexityScore !== 'number' || !Number.isFinite(complexityScore)) {
    return { error: 'complexityScore must be a finite number' };
  }
  if (complexityScore < 0 || complexityScore > 1) {
    return { error: 'complexityScore must be between 0 and 1' };
  }

  let effectiveModalities = ['text'];
  if (modalities !== undefined && modalities !== null) {
    if (
      !Array.isArray(modalities) ||
      modalities.length > MAX_MODALITIES ||
      !modalities.every(m => typeof m === 'string' && m.trim() !== '')
    ) {
      return { error: 'modalities must be an array of non-empty strings' };
    }
    if (modalities.length > 0) effectiveModalities = modalities;
  }

  return {
    value: { queryType, queryText, modalities: effectiveModalities, complexityScore }
  };
}

/**
 * Parse an integer query parameter, rejecting NaN and out-of-range values.
 * @returns {number|null} Integer, or null if invalid
 */
export function parseIntParam(raw, min, max, defaultValue) {
  if (raw === undefined) return defaultValue;
  if (typeof raw !== 'string' || !/^\d+$/.test(raw)) return null;
  const n = parseInt(raw, 10);
  return n >= min && n <= max ? n : null;
}
