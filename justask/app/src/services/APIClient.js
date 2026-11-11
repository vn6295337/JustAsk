import axios from 'axios';
import Constants from 'expo-constants';

const BACKEND_URL = Constants.expoConfig?.extra?.backendUrl || 'https://justask-api.onrender.com';
const TIMEOUT = parseInt(Constants.expoConfig?.extra?.apiTimeout, 10) || 30000;

// Optional shared token (must match API_AUTH_TOKEN on the server, if set)
const API_TOKEN = Constants.expoConfig?.extra?.apiToken || '';

const client = axios.create({
  baseURL: BACKEND_URL,
  timeout: TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    ...(API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}),
  },
});

const APIClient = {
  /**
   * Send a query to the backend
   * @param {string} query - User query
   * @returns {Promise<{response, llm_used, category, response_time}>}
   */
  query: async (query) => {
    try {
      console.log('📤 Sending query to:', BACKEND_URL + '/api/query');
      const response = await client.post('/api/query', { query });
      console.log('✅ Query successful');
      return response.data;
    } catch (error) {
      console.log('❌ Query failed:', error.message);
      console.log('Error code:', error.code);
      console.log('Has response:', !!error.response);
      throw handleError(error);
    }
  },

  /**
   * Sync offline queries with the backend
   * @param {Array} queries - Array of offline queries to sync
   * @returns {Promise<{responses}>}
   */
  syncOfflineQueries: async (queries) => {
    try {
      const response = await client.post('/api/queue/sync', { queries });
      return response.data;
    } catch (error) {
      throw handleError(error);
    }
  },

  /**
   * Health check endpoint
   * @returns {Promise<{status}>}
   */
  health: async () => {
    try {
      const response = await client.get('/api/health');
      return response.data;
    } catch (error) {
      throw handleError(error);
    }
  },
};

/**
 * Handle API errors and return user-friendly messages
 */
function handleError(error) {
  const wrap = (message, props) => Object.assign(new Error(message), props);

  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const message = error.response.data?.error || 'Server error';

    if (status === 400) {
      return wrap(`Invalid request: ${message}`, { status });
    } else if (status === 451) {
      // Region block (EU, EEA, UK, Switzerland): permanent, never retry
      return wrap(message || "Sorry, JustAsk isn't available in your region yet.", {
        status,
        permanent: true,
      });
    } else if (status === 429) {
      return wrap('Rate limited. All providers are busy. Please try again in a moment.', { status });
    } else if (status === 500) {
      return wrap('All LLM providers unavailable. Please try again later.', { status });
    } else {
      return wrap(`Error (${status}): ${message}`, { status });
    }
  } else if (error.request) {
    // Request made but no response
    const errorDetails = `Code: ${error.code || 'none'}, Message: ${error.message}`;
    console.log('Request error details:', errorDetails);

    if (error.code === 'ECONNABORTED') {
      return wrap(`Timeout after ${TIMEOUT}ms. Backend may be starting up (Render cold start). Please try again.`, { isNetworkError: true });
    } else if (error.code === 'ECONNREFUSED') {
      return wrap(`Cannot reach ${BACKEND_URL}. Check network connection.`, { isNetworkError: true });
    } else if (error.code === 'NETWORK_ERROR' || error.code === 'ERR_NETWORK') {
      return wrap(`Network error (${error.code}). Check your internet connection and try again.`, { isNetworkError: true });
    } else {
      return wrap(`Network error: ${error.message || 'No response from server'}`, { isNetworkError: true });
    }
  } else {
    // Other errors
    return new Error(error.message || 'Unknown error occurred');
  }
}

export default APIClient;
