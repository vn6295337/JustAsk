import axios from 'axios';
import Constants from 'expo-constants';

const BACKEND_URL = Constants.expoConfig?.extra?.backendUrl || 'https://justask-api.onrender.com';
const TIMEOUT = parseInt(Constants.expoConfig?.extra?.apiTimeout, 10) || 30000;

const client = axios.create({
  baseURL: BACKEND_URL,
  timeout: TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
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
  console.log('Full error object:', JSON.stringify(error, null, 2));

  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const message = error.response.data?.error || 'Server error';

    if (status === 400) {
      return new Error(`Invalid request: ${message}`);
    } else if (status === 429) {
      return new Error('Rate limited. All providers are busy. Please try again in a moment.');
    } else if (status === 500) {
      return new Error('All LLM providers unavailable. Please try again later.');
    } else {
      return new Error(`Error (${status}): ${message}`);
    }
  } else if (error.request) {
    // Request made but no response
    const errorDetails = `Code: ${error.code || 'none'}, Message: ${error.message}`;
    console.log('Request error details:', errorDetails);

    if (error.code === 'ECONNABORTED') {
      return new Error(`Timeout after ${TIMEOUT}ms. Backend may be starting up (Render cold start). Please try again.`);
    } else if (error.code === 'ECONNREFUSED') {
      return new Error(`Cannot reach ${BACKEND_URL}. Check network connection.`);
    } else if (error.code === 'NETWORK_ERROR' || error.code === 'ERR_NETWORK') {
      return new Error(`Network error (${error.code}). Check your internet connection and try again.`);
    } else {
      return new Error(`Network error: ${error.message || 'No response from server'}`);
    }
  } else {
    // Other errors
    return new Error(error.message || 'Unknown error occurred');
  }
}

export default APIClient;
