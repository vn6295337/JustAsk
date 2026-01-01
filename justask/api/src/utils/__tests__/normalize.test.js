import { normalizeResponse } from '../normalize.js';

describe('Response Normalization', () => {
  describe('Gemini Response Normalization', () => {
    test('should normalize valid Gemini response', () => {
      const geminiResponse = {
        response: {
          candidates: [
            {
              content: {
                parts: [
                  { text: 'Hello from Gemini' },
                ],
              },
            },
          ],
          usageMetadata: {
            promptTokenCount: 10,
            candidatesTokenCount: 20,
            totalTokenCount: 30,
          },
        },
        model: 'gemini-1.5-flash',
      };

      const normalized = normalizeResponse(geminiResponse, 'gemini');
      expect(normalized.text).toBe('Hello from Gemini');
      expect(normalized.model).toBe('gemini-1.5-flash');
      expect(normalized.usage).toBeDefined();
    });

    test('should handle Gemini response with multiple parts', () => {
      const response = {
        response: {
          candidates: [
            {
              content: {
                parts: [
                  { text: 'First part' },
                  { text: 'Second part' },
                ],
              },
            },
          ],
        },
      };

      const normalized = normalizeResponse(response, 'gemini');
      expect(normalized.text).toBe('First part');
    });

    test('should throw error on missing Gemini candidates', () => {
      const response = {
        response: {
          candidates: [],
        },
      };

      expect(() => {
        normalizeResponse(response, 'gemini');
      }).toThrow();
    });

    test('should throw error on empty Gemini parts', () => {
      const response = {
        response: {
          candidates: [
            {
              content: {
                parts: [],
              },
            },
          ],
        },
      };

      expect(() => {
        normalizeResponse(response, 'gemini');
      }).toThrow();
    });
  });

  describe('Groq Response Normalization', () => {
    test('should normalize valid Groq response', () => {
      const groqResponse = {
        choices: [
          {
            message: {
              content: 'Hello from Groq',
            },
          },
        ],
        usage: {
          prompt_tokens: 15,
          completion_tokens: 25,
          total_tokens: 40,
        },
        model: 'mixtral-8x7b-32768',
      };

      const normalized = normalizeResponse(groqResponse, 'groq');
      expect(normalized.text).toBe('Hello from Groq');
      expect(normalized.model).toBe('mixtral-8x7b-32768');
      expect(normalized.usage).toBeDefined();
    });

    test('should handle Groq response with empty choices', () => {
      const response = {
        choices: [],
      };

      expect(() => {
        normalizeResponse(response, 'groq');
      }).toThrow();
    });

    test('should throw error on missing Groq content', () => {
      const response = {
        choices: [
          {
            message: {
              content: '',
            },
          },
        ],
      };

      expect(() => {
        normalizeResponse(response, 'groq');
      }).toThrow();
    });
  });

  describe('OpenRouter Response Normalization', () => {
    test('should normalize valid OpenRouter response', () => {
      const openrouterResponse = {
        choices: [
          {
            message: {
              content: 'Hello from OpenRouter',
            },
          },
        ],
        usage: {
          prompt_tokens: 12,
          completion_tokens: 22,
          total_tokens: 34,
        },
        model: 'meta-llama/llama-2-70b-chat',
      };

      const normalized = normalizeResponse(openrouterResponse, 'openrouter');
      expect(normalized.text).toBe('Hello from OpenRouter');
      expect(normalized.model).toBe('meta-llama/llama-2-70b-chat');
      expect(normalized.usage).toBeDefined();
    });

    test('should handle OpenRouter response (same format as Groq)', () => {
      const response = {
        choices: [
          {
            message: {
              content: 'Response text',
            },
          },
        ],
      };

      const normalized = normalizeResponse(response, 'openrouter');
      expect(normalized.text).toBe('Response text');
    });
  });

  describe('Error Handling', () => {
    test('should throw error for unknown provider', () => {
      expect(() => {
        normalizeResponse({}, 'unknown_provider');
      }).toThrow('Unknown provider');
    });

    test('should throw error for null response', () => {
      expect(() => {
        normalizeResponse(null, 'gemini');
      }).toThrow();
    });

    test('should throw error for undefined response', () => {
      expect(() => {
        normalizeResponse(undefined, 'groq');
      }).toThrow();
    });

    test('should throw error for invalid structure', () => {
      expect(() => {
        normalizeResponse({ invalid: 'structure' }, 'gemini');
      }).toThrow();
    });
  });

  describe('Field Presence and Types', () => {
    test('normalized response should have required fields', () => {
      const response = {
        choices: [
          {
            message: {
              content: 'Test',
            },
          },
        ],
      };

      const normalized = normalizeResponse(response, 'groq');
      expect(normalized).toHaveProperty('text');
      expect(normalized).toHaveProperty('model');
      expect(normalized).toHaveProperty('usage');
    });

    test('should preserve usage metadata', () => {
      const response = {
        choices: [
          {
            message: {
              content: 'Test',
            },
          },
        ],
        usage: {
          prompt_tokens: 5,
          completion_tokens: 10,
          total_tokens: 15,
        },
      };

      const normalized = normalizeResponse(response, 'groq');
      expect(normalized.usage.prompt_tokens).toBe(5);
      expect(normalized.usage.completion_tokens).toBe(10);
      expect(normalized.usage.total_tokens).toBe(15);
    });
  });
});
