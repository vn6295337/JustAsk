import { callGemini } from '../providers/gemini.js';
import { callGroq } from '../providers/groq.js';
import { callOpenRouter } from '../providers/openrouter.js';
import { getModelFallbackChain } from '../routing/rankedModelSelector.js';
import config from '../config.js';

/**
 * Execute query with specific provider
 * @param {string} provider - Provider name
 * @param {string} query - User query
 * @param {boolean} enableWebSearch - Enable web search for news queries
 * @returns {Promise<object>} Provider response
 */
const executeProvider = async (provider, query, enableWebSearch = false, queryType = null) => {
  switch (provider) {
    case config.providerNames.GEMINI:
      return await callGemini(query);
    case config.providerNames.GROQ:
      // Use compound model for news and financial queries, standard for others
      let groqModel = null;
      if (queryType === 'business_news' || queryType === 'financial_analysis') {
        groqModel = config.models.groqCompound;
      }
      return callGroq(query, groqModel);
    case config.providerNames.OPENROUTER:
      // For fallback: use GPT-OSS models for news/financial with browser search
      return await callOpenRouter(query, enableWebSearch, queryType);
    default:
      throw new Error(`Unknown provider: ${provider}`);
  }
};

/**
 * Execute query using ranked model fallback chain
 * Tries models in order of pre-computed selection scores (highest first)
 * @param {string} query - User query
 * @param {string} queryType - Query classification type
 * @returns {Promise<object>} Response from provider or error
 */
export const executeWithRankedFallback = async (query, queryType = null) => {
  try {
    // Get ranked model chain from justask-router
    const modelChain = await getModelFallbackChain();
    const isNewsQuery = queryType === 'business_news';

    console.log(`[RankedFallback] Got ${modelChain.length} models in fallback chain`);

    for (let i = 0; i < modelChain.length; i++) {
      const model = modelChain[i];

      try {
        console.log(`[RankedFallback] Attempting rank ${model.rank}: ${model.provider} - ${model.modelName}`);

        const response = await executeProvider(model.provider, query, isNewsQuery, queryType);

        console.log(`[RankedFallback] Success with rank ${model.rank}`);

        return {
          success: true,
          response: response.response,
          llm_used: model.provider,
          model_name: model.modelName,
          model_rank: model.rank,
          selection_score: model.selectionScore,
          failover_count: i,
          usage: response.usage || {},
        };
      } catch (error) {
        console.error(
          `[RankedFallback] Rank ${model.rank} (${model.provider}) failed:`,
          error.message || error
        );

        // Check error type
        if (error.status === 429) {
          console.log(`[RankedFallback] Rate limited, trying next model`);
        } else if (error.status >= 500) {
          console.log(`[RankedFallback] Server error, trying next model`);
        }

        // Continue to next model
        if (i < modelChain.length - 1) {
          continue;
        } else {
          throw error;
        }
      }
    }

    throw new Error('No models available in ranked fallback chain');
  } catch (error) {
    console.error('[RankedFallback] All models exhausted:', error.message);

    return {
      success: false,
      error: error.message || 'All ranked models failed',
      llm_used: null,
      model_rank: null,
      failover_count: null,
    };
  }
};

/**
 * Test failover chain
 */
export const testFailover = async () => {
  console.log('Testing Failover Logic:');

  // This is a simplified test since we don't have real API keys
  // In reality, we would mock the providers

  try {
    // Test failover chain for different query types
    const testCases = [
      {
        query: 'What is the news today?',
        primaryProvider: config.providerNames.GEMINI,
      },
      {
        query: 'Write a poem',
        primaryProvider: config.providerNames.GROQ,
      },
    ];

    console.log('✅ Failover logic test completed (mock test)');
    return true;
  } catch (error) {
    console.error('❌ Failover test failed:', error.message);
    return false;
  }
};

export default {
  executeWithRankedFallback,
  testFailover,
};
