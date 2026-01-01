/**
 * Response Normalization
 * Converts different LLM provider response formats to unified format
 */

/**
 * Normalize response from any LLM provider
 * @param {object} rawResponse - Raw response from provider
 * @param {string} provider - Provider name (gemini, groq, openrouter)
 * @returns {object} Normalized response
 */
export const normalizeResponse = (rawResponse, provider) => {
  try {
    switch (provider) {
      case 'gemini':
        return normalizeGemini(rawResponse);
      case 'groq':
        return normalizeGroq(rawResponse);
      case 'openrouter':
        return normalizeOpenRouter(rawResponse);
      default:
        throw new Error(`Unknown provider: ${provider}`);
    }
  } catch (error) {
    console.error(`Error normalizing ${provider} response:`, error.message);
    throw error;
  }
};

/**
 * Normalize Gemini response
 * Expected format: result.response.candidates[0].content.parts[0].text
 */
const normalizeGemini = (rawResponse) => {
  try {
    if (!rawResponse || !rawResponse.response) {
      throw new Error('Invalid Gemini response structure');
    }

    const response = rawResponse.response;
    const candidates = response.candidates || [];

    if (candidates.length === 0) {
      throw new Error('No candidates in Gemini response');
    }

    const firstCandidate = candidates[0];
    const content = firstCandidate.content || {};
    const parts = content.parts || [];

    if (parts.length === 0) {
      throw new Error('No text parts in Gemini response');
    }

    const text = parts[0].text || '';

    if (!text) {
      throw new Error('Empty text in Gemini response');
    }

    return {
      text,
      model: rawResponse.model || 'gemini-1.5-flash',
      usage: rawResponse.usage || {},
    };
  } catch (error) {
    throw new Error(`Gemini normalization failed: ${error.message}`);
  }
};

/**
 * Normalize Groq response
 * Expected format: message.choices[0].message.content
 */
const normalizeGroq = (rawResponse) => {
  try {
    if (!rawResponse || typeof rawResponse !== 'object') {
      throw new Error('Invalid Groq response structure');
    }

    const choices = rawResponse.choices || [];

    if (choices.length === 0) {
      throw new Error('No choices in Groq response');
    }

    const firstChoice = choices[0];
    const message = firstChoice.message || {};
    const text = message.content || '';

    if (!text) {
      throw new Error('Empty content in Groq response');
    }

    return {
      text,
      model: rawResponse.model || 'mixtral-8x7b-32768',
      usage: rawResponse.usage || {},
    };
  } catch (error) {
    throw new Error(`Groq normalization failed: ${error.message}`);
  }
};

/**
 * Normalize OpenRouter response
 * Expected format: response.data.choices[0].message.content (same as Groq)
 */
const normalizeOpenRouter = (rawResponse) => {
  try {
    if (!rawResponse || typeof rawResponse !== 'object') {
      throw new Error('Invalid OpenRouter response structure');
    }

    const choices = rawResponse.choices || [];

    if (choices.length === 0) {
      throw new Error('No choices in OpenRouter response');
    }

    const firstChoice = choices[0];
    const message = firstChoice.message || {};
    const text = message.content || '';

    if (!text) {
      throw new Error('Empty content in OpenRouter response');
    }

    return {
      text,
      model: rawResponse.model || 'openrouter-default',
      usage: rawResponse.usage || {},
    };
  } catch (error) {
    throw new Error(`OpenRouter normalization failed: ${error.message}`);
  }
};

/**
 * Test normalization with sample responses
 */
export const testNormalization = () => {
  // Test Gemini format
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
      usageMetadata: { totalTokenCount: 20 },
    },
    model: 'gemini-1.5-flash',
  };

  // Test Groq format
  const groqResponse = {
    choices: [
      {
        message: { content: 'Hello from Groq' },
      },
    ],
    usage: { total_tokens: 25 },
    model: 'mixtral-8x7b-32768',
  };

  // Test OpenRouter format
  const openrouterResponse = {
    choices: [
      {
        message: { content: 'Hello from OpenRouter' },
      },
    ],
    usage: { total_tokens: 22 },
    model: 'openrouter-default',
  };

  try {
    const normalized1 = normalizeResponse(geminiResponse, 'gemini');
    console.log('✅ Gemini normalization:', normalized1);

    const normalized2 = normalizeResponse(groqResponse, 'groq');
    console.log('✅ Groq normalization:', normalized2);

    const normalized3 = normalizeResponse(openrouterResponse, 'openrouter');
    console.log('✅ OpenRouter normalization:', normalized3);

    return true;
  } catch (error) {
    console.error('❌ Normalization test failed:', error.message);
    return false;
  }
};

export default {
  normalizeResponse,
  testNormalization,
};
