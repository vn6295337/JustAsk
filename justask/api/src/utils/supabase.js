import { createClient } from '@supabase/supabase-js';
import config from '../config.js';

// Initialize Supabase client
const supabase = createClient(config.supabase.url, config.supabase.key);

/**
 * Retrieve API keys from Supabase Vault at runtime
 * Keys are stored server-side only and never exposed to the client
 */
export const getApiKey = async (provider) => {
  try {
    // In development, return dummy keys for testing
    if (config.nodeEnv === 'development') {
      console.warn(
        `[DEV] Using placeholder API key for ${provider}. Set real keys in Supabase Vault for production.`
      );

      switch (provider) {
        case 'gemini':
          return process.env.GEMINI_API_KEY || 'dev-gemini-key';
        case 'groq':
          return process.env.GROQ_API_KEY || 'dev-groq-key';
        case 'openrouter':
          return process.env.OPENROUTER_API_KEY_2 || 'dev-openrouter-key';
        default:
          throw new Error(`Unknown provider: ${provider}`);
      }
    }

    // Production: Retrieve from environment variables (set in Render deployment config)
    let key;

    if (provider === 'openrouter') {
      // OpenRouter uses secondary key
      key = process.env.OPENROUTER_API_KEY_2;
    } else {
      key = process.env[`${provider.toUpperCase()}_API_KEY`];
    }

    if (!key) {
      throw new Error(
        `API key for ${provider} not found in environment variables`
      );
    }

    return key;
  } catch (error) {
    console.error(`Error retrieving API key for ${provider}:`, error.message);
    throw error;
  }
};

/**
 * Test Supabase connection
 */
export const testSupabaseConnection = async () => {
  try {
    const { data, error } = await supabase
      .from('requests')
      .select('count(*)', { count: 'exact', head: true });

    if (error) {
      console.error('Supabase connection error:', error);
      return false;
    }

    console.log('✅ Supabase connection successful');
    return true;
  } catch (error) {
    console.error('Supabase connection test failed:', error.message);
    return false;
  }
};

export default {
  getApiKey,
  testSupabaseConnection,
};
