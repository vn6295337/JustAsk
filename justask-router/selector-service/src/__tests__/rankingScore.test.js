import {
  SELECTION_WEIGHTS,
  UNKNOWN_LIMIT_ROOM_SCORE,
  calculateFreeLimitRoom,
  calculateSelectionScore,
} from '../../scripts/db/populate_model_selection_score.js';

describe('manual ranking score', () => {
  test('weights sum to 1 and exclude speed', () => {
    const sum = Object.values(SELECTION_WEIGHTS).reduce((a, b) => a + b, 0);
    expect(sum).toBeCloseTo(1, 10);
    expect(SELECTION_WEIGHTS).toEqual({
      intelligenceIndex: 0.47,
      freeLimitRoom: 0.33,
      geography: 0.13,
      license: 0.07,
    });
  });

  test('free-limit room is the daily limit relative to the largest', () => {
    expect(calculateFreeLimitRoom(1000, 1000)).toBe(1);
    expect(calculateFreeLimitRoom(50, 1000)).toBeCloseTo(0.05);
  });

  test('unknown daily limit gets the middle score, not full marks', () => {
    expect(calculateFreeLimitRoom(null, 1000)).toBe(UNKNOWN_LIMIT_ROOM_SCORE);
    expect(calculateFreeLimitRoom(0, 1000)).toBe(UNKNOWN_LIMIT_ROOM_SCORE);
    expect(calculateFreeLimitRoom(100, 0)).toBe(UNKNOWN_LIMIT_ROOM_SCORE);
  });

  test('a smart model with a tiny limit no longer wins automatically', () => {
    // A: smarter (index 60) but 50/day; B: index 40 with 1,000/day
    const a = calculateSelectionScore(60, calculateFreeLimitRoom(50, 1000), 1, 1);
    const b = calculateSelectionScore(40, calculateFreeLimitRoom(1000, 1000), 1, 1);
    expect(b).toBeGreaterThan(a);
  });

  test('missing intelligence index uses the 0.6 fallback', () => {
    expect(calculateSelectionScore(null, 1, 1, 1)).toBeCloseTo(0.6 * 0.47 + 0.33 + 0.13 + 0.07);
  });
});
