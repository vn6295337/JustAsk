import { classifyQuery } from '../classifier.js';
import config from '../../config.js';

describe('Query Classification Engine', () => {
  describe('News Classification', () => {
    test('should classify "What is the latest news?" as business_news', () => {
      const result = classifyQuery('What is the latest news?');
      expect(result.type).toBe(config.queryCategories.BUSINESS_NEWS);
      expect(result.matchedKeywords.length).toBeGreaterThan(0);
    });

    test('should classify "Breaking news today" as business_news', () => {
      const result = classifyQuery('Breaking news today');
      expect(result.type).toBe(config.queryCategories.BUSINESS_NEWS);
    });

    test('should classify "Current headlines" as business_news', () => {
      const result = classifyQuery('Current headlines');
      expect(result.type).toBe(config.queryCategories.BUSINESS_NEWS);
    });
  });

  describe('Creative Classification', () => {
    test('should classify "Write me a poem" as creative', () => {
      const result = classifyQuery('Write me a poem');
      expect(result.type).toBe(config.queryCategories.CREATIVE);
      expect(result.matchedKeywords.length).toBeGreaterThan(0);
    });

    test('should classify "Create a short story" as creative', () => {
      const result = classifyQuery('Create a short story');
      expect(result.type).toBe(config.queryCategories.CREATIVE);
    });

    test('should classify "Compose a poem about nature" as creative', () => {
      const result = classifyQuery('Compose a poem about nature');
      expect(result.type).toBe(config.queryCategories.CREATIVE);
    });

    test('should classify "Generate a narrative" as creative', () => {
      const result = classifyQuery('Generate a narrative');
      expect(result.type).toBe(config.queryCategories.CREATIVE);
    });
  });

  describe('General Knowledge Classification', () => {
    test('should classify "What is AI?" as general_knowledge', () => {
      const result = classifyQuery('What is AI?');
      expect(result.type).toBe(config.queryCategories.GENERAL_KNOWLEDGE);
    });

    test('should classify "How does photosynthesis work?" as general_knowledge', () => {
      const result = classifyQuery('How does photosynthesis work?');
      expect(result.type).toBe(config.queryCategories.GENERAL_KNOWLEDGE);
    });

    test('should classify "Explain quantum physics" as general_knowledge', () => {
      const result = classifyQuery('Explain quantum physics');
      expect(result.type).toBe(config.queryCategories.GENERAL_KNOWLEDGE);
    });
  });

  describe('Edge Cases', () => {
    test('should handle mixed keywords (news takes precedence)', () => {
      const result = classifyQuery('Write me news about today');
      expect(result.type).toBe(config.queryCategories.BUSINESS_NEWS);
    });

    test('should handle lowercase conversion', () => {
      const result = classifyQuery('WRITE ME A POEM');
      expect(result.type).toBe(config.queryCategories.CREATIVE);
    });

    test('should handle empty query gracefully', () => {
      const result = classifyQuery('');
      expect(result.type).toBe(config.queryCategories.GENERAL_KNOWLEDGE);
      expect(result.error).toBeDefined();
    });

    test('should handle very long query', () => {
      const longQuery = 'This is a very long query about something general knowledge related ' + 'a'.repeat(1000);
      const result = classifyQuery(longQuery);
      expect(result.type).toBeDefined();
    });

    test('should return confidence scores', () => {
      const result = classifyQuery('Write a poem');
      expect(result.confidence).toBeGreaterThanOrEqual(0);
      expect(result.confidence).toBeLessThanOrEqual(1);
    });
  });

  describe('Invalid Input Handling', () => {
    test('should handle null input', () => {
      const result = classifyQuery(null);
      expect(result.error).toBeDefined();
    });

    test('should handle undefined input', () => {
      const result = classifyQuery(undefined);
      expect(result.error).toBeDefined();
    });

    test('should handle non-string input', () => {
      const result = classifyQuery(12345);
      expect(result.error).toBeDefined();
    });

    test('should handle whitespace-only query', () => {
      const result = classifyQuery('   ');
      expect(result.type).toBe(config.queryCategories.GENERAL_KNOWLEDGE);
    });
  });
});
