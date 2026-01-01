import config from '../config.js';

/**
 * Query Classification Engine
 * Fast keyword-based classification (no API calls)
 * Categories: news, general_knowledge, creative
 */

/**
 * Classify query into category based on keywords
 * @param {string} query - User query
 * @returns {object} {type: string, confidence: number, matchedKeywords: string[]}
 */
export const classifyQuery = (query) => {
  try {
    if (!query || typeof query !== 'string') {
      throw new Error('Query must be a non-empty string');
    }

    const lowerQuery = query.toLowerCase();

    // Check for financial queries (highest priority)
    const financialKeywords = config.keywords.financial || [];
    const financialMatches = financialKeywords.filter((keyword) =>
      lowerQuery.includes(keyword.toLowerCase())
    );

    if (financialMatches.length > 0) {
      return {
        type: config.queryCategories.FINANCIAL_ANALYSIS,
        confidence: Math.min(1.0, financialMatches.length * 0.3),
        matchedKeywords: financialMatches,
      };
    }

    // Check for creative queries
    const creativeKeywords = config.keywords.creative || [];
    const creativeMatches = creativeKeywords.filter((keyword) =>
      lowerQuery.includes(keyword.toLowerCase())
    );

    if (creativeMatches.length > 0) {
      return {
        type: config.queryCategories.CREATIVE,
        confidence: Math.min(1.0, creativeMatches.length * 0.3),
        matchedKeywords: creativeMatches,
      };
    }

    // Check for news queries
    const newsKeywords = config.keywords.news || [];
    const newsMatches = newsKeywords.filter((keyword) =>
      lowerQuery.includes(keyword.toLowerCase())
    );

    if (newsMatches.length > 0) {
      return {
        type: config.queryCategories.BUSINESS_NEWS,
        confidence: Math.min(1.0, newsMatches.length * 0.3),
        matchedKeywords: newsMatches,
      };
    }

    // Default to general knowledge
    return {
      type: config.queryCategories.GENERAL_KNOWLEDGE,
      confidence: 0.5,
      matchedKeywords: [],
    };
  } catch (error) {
    console.error('Classification error:', error.message);

    // Default to general knowledge on error
    return {
      type: config.queryCategories.GENERAL_KNOWLEDGE,
      confidence: 0.0,
      matchedKeywords: [],
      error: error.message,
    };
  }
};

/**
 * Test classification with sample queries
 */
export const testClassification = () => {
  const testCases = [
    { query: "What's in the news today?", expected: 'business_news' },
    { query: 'Write me a poem about the moon', expected: 'creative' },
    { query: 'What is artificial intelligence?', expected: 'general_knowledge' },
    { query: 'Latest breaking news', expected: 'business_news' },
    { query: 'Create a story for me', expected: 'creative' },
    { query: 'Analyze my investment portfolio', expected: 'financial_analysis' },
    { query: 'What is the best crypto to buy?', expected: 'financial_analysis' },
  ];

  console.log('Testing Query Classification:');
  let passed = 0;

  testCases.forEach((testCase) => {
    const result = classifyQuery(testCase.query);
    const isCorrect = result.type === testCase.expected;

    console.log(
      `${isCorrect ? '✅' : '❌'} "${testCase.query}"`,
      `→ ${result.type} (confidence: ${result.confidence.toFixed(2)})`
    );

    if (isCorrect) passed++;
  });

  console.log(`\nClassification Tests: ${passed}/${testCases.length} passed`);
  return passed === testCases.length;
};

export default {
  classifyQuery,
  testClassification,
};
