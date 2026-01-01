/**
 * Format provider name and model info for display
 * Handles various provider formats and extracts model subtitles
 */

const formatProvider = (llmUsed, category) => {
  if (!llmUsed) return { displayName: 'Unknown', subtitle: null };

  const lower = llmUsed.toLowerCase();

  // Groq providers
  if (lower.includes('groq')) {
    if (lower.includes('compound')) {
      return {
        displayName: 'Groq',
        subtitle: 'compound',
      };
    } else if (lower.includes('llama') || lower.includes('8b')) {
      return {
        displayName: 'Groq',
        subtitle: 'Llama 8B',
      };
    }
    return {
      displayName: 'Groq',
      subtitle: 'Standard',
    };
  }

  // Gemini providers
  if (lower.includes('gemini') || lower.includes('google')) {
    if (lower.includes('2.0')) {
      return {
        displayName: 'Gemini',
        subtitle: '2.0-Flash',
      };
    }
    return {
      displayName: 'Gemini',
      subtitle: 'Flash',
    };
  }

  // OpenRouter/GPT-OSS providers
  if (lower.includes('openrouter') || lower.includes('gpt-oss') || lower.includes('openai')) {
    if (lower.includes('120b')) {
      return {
        displayName: 'OpenRouter',
        subtitle: 'GPT-OSS 120B',
      };
    } else if (lower.includes('20b')) {
      return {
        displayName: 'OpenRouter',
        subtitle: 'GPT-OSS 20B',
      };
    }
    return {
      displayName: 'OpenRouter',
      subtitle: 'GPT-OSS',
    };
  }

  // Generic fallback
  return {
    displayName: llmUsed.split('/')[0] || llmUsed,
    subtitle: llmUsed.split('/').slice(1).join('/') || null,
  };
};

export { formatProvider };
