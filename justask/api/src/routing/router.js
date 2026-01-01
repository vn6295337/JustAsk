import config from '../config.js';

/**
 * Routing Engine
 * Selects primary LLM provider based on query classification
 * Fallback chain: Primary → Groq → OpenRouter
 */

/**
 * Select primary provider based on query classification
 * @param {string} queryType - Query category (business_news, creative, general_knowledge)
 * @returns {string} Provider name
 */
export const selectPrimaryProvider = (queryType) => {
  try {
    switch (queryType) {
      case config.queryCategories.BUSINESS_NEWS:
        // News queries go to Groq compound (reliable, no payment issues)
        return config.providerNames.GROQ;

      case config.queryCategories.FINANCIAL_ANALYSIS:
        // Financial queries go to Groq compound (reliable, no payment issues)
        return config.providerNames.GROQ;

      case config.queryCategories.CREATIVE:
        // Creative queries go to Groq (fast, good at creative)
        return config.providerNames.GROQ;

      case config.queryCategories.GENERAL_KNOWLEDGE:
      default:
        // Default to Gemini for general knowledge
        return config.providerNames.GEMINI;
    }
  } catch (error) {
    console.error('Routing error:', error.message);
    // Fallback to Gemini on error
    return config.providerNames.GEMINI;
  }
};

/**
 * Get failover chain for a provider
 * Returns: [Primary, Secondary, Tertiary]
 * @param {string} primaryProvider - Primary provider name
 * @returns {string[]} Ordered list of providers to try
 */
export const getFailoverChain = (primaryProvider) => {
  // Start with primary provider
  const chain = [primaryProvider];

  // Standard failover chain for all providers
  // Primary → Groq (secondary) → OpenRouter (tertiary)

  // Add secondary and tertiary from config
  const secondary = config.failoverChain[0] || config.providerNames.GROQ;
  const tertiary = config.failoverChain[1] || config.providerNames.OPENROUTER;

  // Don't add duplicates
  if (secondary !== primaryProvider) {
    chain.push(secondary);
  }
  if (tertiary !== primaryProvider && tertiary !== secondary) {
    chain.push(tertiary);
  }

  return chain;
};

/**
 * Test routing logic
 */
export const testRouting = () => {
  console.log('Testing Query Routing:');

  const testCases = [
    {
      type: config.queryCategories.BUSINESS_NEWS,
      expected: config.providerNames.GEMINI,
    },
    {
      type: config.queryCategories.CREATIVE,
      expected: config.providerNames.GROQ,
    },
    {
      type: config.queryCategories.GENERAL_KNOWLEDGE,
      expected: config.providerNames.GROQ,
    },
  ];

  let passed = 0;

  testCases.forEach((testCase) => {
    const primary = selectPrimaryProvider(testCase.type);
    const isCorrect = primary === testCase.expected;

    console.log(
      `${isCorrect ? '✅' : '❌'} ${testCase.type} → ${primary}`
    );

    if (isCorrect) passed++;

    // Also test failover chain
    const chain = getFailoverChain(primary);
    console.log(
      `    Failover chain: ${chain.join(' → ')}`
    );
  });

  console.log(`\nRouting Tests: ${passed}/${testCases.length} passed`);
  return passed === testCases.length;
};

export default {
  selectPrimaryProvider,
  getFailoverChain,
  testRouting,
};
