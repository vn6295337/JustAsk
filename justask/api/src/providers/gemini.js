import { GoogleGenerativeAI } from '@google/generative-ai';
import { getApiKey } from '../utils/supabase.js';
import config from '../config.js';
import { ProviderError, toProviderError, withTimeout } from '../utils/errors.js';

let geminiClient = null;

/**
 * Initialize Gemini client
 */
const initializeGemini = async () => {
  try {
    const apiKey = await getApiKey('gemini');
    geminiClient = new GoogleGenerativeAI(apiKey);
    return geminiClient;
  } catch (error) {
    console.error('Failed to initialize Gemini:', error.message);
    throw error;
  }
};

/**
 * Call Gemini API
 * @param {string} query - User query
 * @param {string} modelName - Model to call (defaults to config)
 * @returns {Promise<{response: string, model: string, usage: object}>}
 */
export const callGemini = async (query, modelName = null) => {
  const modelId = modelName || config.models.gemini;
  try {
    if (!geminiClient) {
      await initializeGemini();
    }

    const model = geminiClient.getGenerativeModel({
      model: modelId,
    });

    const result = await withTimeout(
      model.generateContent(query),
      config.responseTimeouts.gemini,
      'gemini'
    );

    // Extract response text
    const candidate = result.response.candidates?.[0];
    const response = (candidate?.content?.parts || [])
      .map((p) => p?.text || '')
      .join('')
      .trim();
    if (!response) {
      const reason =
        result.response.promptFeedback?.blockReason || candidate?.finishReason || 'empty';
      throw new ProviderError('gemini', `Empty or blocked completion (${reason})`, 502);
    }

    return {
      response,
      model: modelId,
      provider: 'gemini',
      usage: {
        promptTokens: result.response.usageMetadata?.promptTokenCount || 0,
        completionTokens: result.response.usageMetadata?.candidatesTokenCount || 0,
        totalTokens: result.response.usageMetadata?.totalTokenCount || 0,
      },
    };
  } catch (error) {
    console.error('Gemini API error:', error.message);
    throw toProviderError('gemini', error);
  }
};

/**
 * Test Gemini connection
 */
export const testGemini = async () => {
  try {
    const result = await callGemini('Say hello');
    console.log('✅ Gemini test successful:', result);
    return true;
  } catch (error) {
    console.error('❌ Gemini test failed:', error.message);
    return false;
  }
};

export default {
  callGemini,
  testGemini,
};
