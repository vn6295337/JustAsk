import Groq from 'groq-sdk';
import { getApiKey } from '../utils/supabase.js';
import config from '../config.js';

let groqClient = null;

/**
 * Initialize Groq client
 */
const initializeGroq = async () => {
  try {
    const apiKey = await getApiKey('groq');
    groqClient = new Groq({ apiKey });
    return groqClient;
  } catch (error) {
    console.error('Failed to initialize Groq:', error.message);
    throw error;
  }
};

/**
 * Call Groq API
 * @param {string} query - User query
 * @param {string} modelOverride - Optional model override (for compound models)
 * @returns {Promise<{response: string, model: string, usage: object}>}
 */
export const callGroq = async (query, modelOverride = null) => {
  try {
    if (!groqClient) {
      await initializeGroq();
    }

    const model = modelOverride || config.models.groq;

    // Reduce max_tokens for compound models (they have stricter limits)
    const maxTokens = (model && model.includes('compound')) ? 1024 : 2048;

    const message = await groqClient.chat.completions.create({
      messages: [
        {
          role: 'user',
          content: query,
        },
      ],
      model: model,
      temperature: 0.7,
      max_tokens: maxTokens,
    });

    // Extract response text
    const response = message.choices?.[0]?.message?.content || 'No response from Groq';

    return {
      response,
      model: model,
      provider: 'groq',
      usage: {
        promptTokens: message.usage?.prompt_tokens || 0,
        completionTokens: message.usage?.completion_tokens || 0,
        totalTokens: message.usage?.total_tokens || 0,
      },
    };
  } catch (error) {
    console.error('Groq API error:', error.message);
    throw {
      provider: 'groq',
      error: error.message,
      status: error.status || 500,
    };
  }
};

/**
 * Test Groq connection
 */
export const testGroq = async () => {
  try {
    const result = await callGroq('Say hello');
    console.log('✅ Groq test successful:', result);
    return true;
  } catch (error) {
    console.error('❌ Groq test failed:', error.message);
    return false;
  }
};

export default {
  callGroq,
  testGroq,
};
