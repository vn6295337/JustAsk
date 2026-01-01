import axios from 'axios';
import { getApiKey } from '../utils/supabase.js';
import config from '../config.js';

/**
 * Call OpenRouter API (fallback provider)
 * Uses HTTP client since there's no official SDK
 * @param {string} query - User query
 * @param {boolean} enableWebSearch - Enable web search for news queries
 * @param {string} queryType - Query classification type for model selection
 * @returns {Promise<{response: string, model: string, usage: object}>}
 */
export const callOpenRouter = async (query, enableWebSearch = false, queryType = null) => {
  try {
    const apiKey = await getApiKey('openrouter');

    // Select model based on query type
    let model = config.models.openrouter;

    if (queryType === 'financial_analysis') {
      // Use GPT-OSS 120B for financial analysis (web search + reasoning for market data)
      model = config.models.openaiGptOss120b;
    } else if (queryType === 'business_news') {
      // Use GPT-OSS 20B for news (web search + fast inference)
      model = config.models.openaiGptOss20b;
    }

    // Build request body
    const requestBody = {
      model: model,
      messages: [
        {
          role: 'user',
          content: query,
        },
      ],
      temperature: 0.7,
      max_tokens: 2048,
    };

    // Add browser search tool for GPT-OSS models (news and financial queries)
    if (model && model.includes('gpt-oss')) {
      requestBody.tools = [
        {
          type: 'browser_search',
        },
      ];
      requestBody.tool_choice = 'auto';
    }

    const response = await axios.post(
      `${config.apiEndpoints.openrouter}/chat/completions`,
      requestBody,
      {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
          'HTTP-Referer': 'https://justask.app',
          'X-Title': 'JustAsk',
        },
        timeout: config.responseTimeouts.openrouter,
      }
    );

    // Extract response text
    const responseText =
      response.data.choices?.[0]?.message?.content ||
      'No response from OpenRouter';

    return {
      response: responseText,
      model: config.models.openrouter,
      provider: 'openrouter',
      usage: {
        promptTokens: response.data.usage?.prompt_tokens || 0,
        completionTokens: response.data.usage?.completion_tokens || 0,
        totalTokens: response.data.usage?.total_tokens || 0,
      },
    };
  } catch (error) {
    console.error('OpenRouter API error:', error.message);

    // Extract status code if available
    const status = error.response?.status || error.code || 500;

    throw {
      provider: 'openrouter',
      error: error.message,
      status,
    };
  }
};

/**
 * Test OpenRouter connection
 */
export const testOpenRouter = async () => {
  try {
    const result = await callOpenRouter('Say hello');
    console.log('✅ OpenRouter test successful:', result);
    return true;
  } catch (error) {
    console.error('❌ OpenRouter test failed:', error.message);
    return false;
  }
};

export default {
  callOpenRouter,
  testOpenRouter,
};
