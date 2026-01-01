import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  query: '',
  response: null,
  loading: false,
  error: null,
  llmUsed: null,
  category: null,
  responseTime: null,
  isOffline: false,
  offlineQueued: false,
  cachedResponse: false,
  messages: [], // Array of {id, type: 'user'|'assistant', text, llmUsed, category, responseTime, isCached, isQueued}
};

const querySlice = createSlice({
  name: 'query',
  initialState,
  reducers: {
    setQuery(state, action) {
      state.query = action.payload;
    },
    setLoading(state, action) {
      state.loading = action.payload;
    },
    setError(state, action) {
      state.error = action.payload;
      state.response = null;
    },
    setOfflineStatus(state, action) {
      state.isOffline = action.payload;
    },
    setOfflineQueued(state, action) {
      state.offlineQueued = action.payload;
    },
    setCachedResponse(state, action) {
      state.cachedResponse = action.payload;
    },
    addMessage(state, action) {
      state.messages.push(action.payload);
    },
    updateMessage(state, action) {
      const { id, updates } = action.payload;
      const messageIndex = state.messages.findIndex(msg => msg.id === id);
      if (messageIndex !== -1) {
        state.messages[messageIndex] = {
          ...state.messages[messageIndex],
          ...updates,
        };
      }
    },
    clearMessages(state) {
      state.messages = [];
    },
  },
});

export const {
  setQuery,
  setLoading,
  setError,
  setOfflineStatus,
  setOfflineQueued,
  setCachedResponse,
  addMessage,
  updateMessage,
  clearMessages,
} = querySlice.actions;

export default querySlice.reducer;
