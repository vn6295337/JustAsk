import { selectPrimaryProvider, getFailoverChain } from '../router.js';
import config from '../../config.js';

describe('Routing Engine', () => {
  describe('Primary Provider Selection', () => {
    test('should select Gemini for business_news queries', () => {
      const provider = selectPrimaryProvider(config.queryCategories.BUSINESS_NEWS);
      expect(provider).toBe(config.providerNames.GEMINI);
    });

    test('should select Groq for creative queries', () => {
      const provider = selectPrimaryProvider(config.queryCategories.CREATIVE);
      expect(provider).toBe(config.providerNames.GROQ);
    });

    test('should select Groq for general_knowledge queries', () => {
      const provider = selectPrimaryProvider(config.queryCategories.GENERAL_KNOWLEDGE);
      expect(provider).toBe(config.providerNames.GROQ);
    });

    test('should select Groq for unknown category (default)', () => {
      const provider = selectPrimaryProvider('unknown_category');
      expect(provider).toBe(config.providerNames.GROQ);
    });
  });

  describe('Failover Chain', () => {
    test('should return failover chain starting with primary provider', () => {
      const chain = getFailoverChain(config.providerNames.GEMINI);
      expect(chain[0]).toBe(config.providerNames.GEMINI);
      expect(chain.length).toBeGreaterThan(0);
    });

    test('should not have duplicate providers in chain', () => {
      const chain = getFailoverChain(config.providerNames.GEMINI);
      const uniqueChain = new Set(chain);
      expect(uniqueChain.size).toBe(chain.length);
    });

    test('should include secondary and tertiary providers', () => {
      const chain = getFailoverChain(config.providerNames.GEMINI);
      expect(chain.length).toBeGreaterThanOrEqual(2);
    });

    test('should have Groq in failover chain', () => {
      const chain = getFailoverChain(config.providerNames.GEMINI);
      expect(chain).toContain(config.providerNames.GROQ);
    });

    test('should have OpenRouter in failover chain', () => {
      const chain = getFailoverChain(config.providerNames.GEMINI);
      expect(chain).toContain(config.providerNames.OPENROUTER);
    });

    test('failover chain order should be: primary → groq → openrouter', () => {
      const chain = getFailoverChain(config.providerNames.GEMINI);
      expect(chain[0]).toBe(config.providerNames.GEMINI);
      expect(chain[1]).toBe(config.providerNames.GROQ);
      expect(chain[2]).toBe(config.providerNames.OPENROUTER);
    });
  });

  describe('Edge Cases', () => {
    test('should handle null category', () => {
      const provider = selectPrimaryProvider(null);
      expect(provider).toBe(config.providerNames.GROQ); // Default
    });

    test('should handle empty string category', () => {
      const provider = selectPrimaryProvider('');
      expect(provider).toBe(config.providerNames.GROQ); // Default
    });

    test('should return valid provider names', () => {
      const validProviders = [
        config.providerNames.GEMINI,
        config.providerNames.GROQ,
        config.providerNames.OPENROUTER,
      ];

      const provider = selectPrimaryProvider(config.queryCategories.BUSINESS_NEWS);
      expect(validProviders).toContain(provider);
    });
  });

  describe('Complete Routing Flow', () => {
    test('news query → Gemini → failover chain includes Groq and OpenRouter', () => {
      const primary = selectPrimaryProvider(config.queryCategories.BUSINESS_NEWS);
      expect(primary).toBe(config.providerNames.GEMINI);

      const chain = getFailoverChain(primary);
      expect(chain[0]).toBe(config.providerNames.GEMINI);
      expect(chain).toContain(config.providerNames.GROQ);
      expect(chain).toContain(config.providerNames.OPENROUTER);
    });

    test('creative query → Groq → failover chain includes Gemini and OpenRouter', () => {
      const primary = selectPrimaryProvider(config.queryCategories.CREATIVE);
      expect(primary).toBe(config.providerNames.GROQ);

      const chain = getFailoverChain(primary);
      expect(chain[0]).toBe(config.providerNames.GROQ);
      expect(chain).toContain(config.providerNames.OPENROUTER);
    });
  });
});
