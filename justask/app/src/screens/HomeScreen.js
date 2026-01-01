import React, { useState, useEffect, useContext, useRef } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  Text,
  FlatList,
  ActivityIndicator,
  StyleSheet,
  Platform,
  Keyboard,
  Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useDispatch, useSelector } from 'react-redux';
import NetInfo from '@react-native-community/netinfo';
import { Ionicons } from '@expo/vector-icons';

import {
  setQuery,
  setLoading,
  setError,
  setOfflineStatus,
  setOfflineQueued,
  setCachedResponse,
  addMessage,
  updateMessage,
  clearMessages,
} from '../store/querySlice';
import APIClient from '../services/APIClient';
import CacheManager from '../services/CacheManager';
import SyncManager from '../services/SyncManager';
import Database from '../services/Database';
import MessageBubble from '../components/MessageBubble';
import { ThemeContext } from '../theme/ThemeContext';
import { SkeletonMessageBubble } from '../components/SkeletonLoader';

const HomeScreen = () => {
  const { theme } = useContext(ThemeContext);
  const dispatch = useDispatch();
  const insets = useSafeAreaInsets();
  const { query, loading, error, isOffline, offlineQueued, messages } = useSelector(
    state => state.query
  );
  const [networkState, setNetworkState] = useState(null);
  const [dbReady, setDbReady] = useState(false);
  const [keyboardHeight, setKeyboardHeight] = useState(0);
  const flatListRef = useRef(null);

  // Keyboard listener
  useEffect(() => {
    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';

    const showSub = Keyboard.addListener(showEvent, (e) => {
      setKeyboardHeight(e.endCoordinates.height);
      // Scroll to end when keyboard opens
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
    });
    const hideSub = Keyboard.addListener(hideEvent, () => {
      setKeyboardHeight(0);
    });

    return () => {
      showSub.remove();
      hideSub.remove();
    };
  }, []);

  // Monitor network status and load chat history
  useEffect(() => {
    let unsub;

    const initializeApp = async () => {
      try {
        // Initialize database and only then load chat history
        await Database.init();
        setDbReady(true);

        // Load chat history from database
        try {
          const history = await Database.loadChatHistory();
          if (history.length > 0) {
            // replace existing messages to avoid duplicates on hot reload
            dispatch(clearMessages());
            history.forEach(msg => dispatch(addMessage(msg)));
          }
        } catch (error) {
          console.error('Error loading chat history:', error);
        }
      } catch (err) {
        console.error('Database init failed:', err);
      }
    };

    initializeApp();

    unsub = NetInfo.addEventListener(state => {
      setNetworkState(prev => {
        // Trigger sync when going from offline -> online
        if (prev && !prev.isConnected && state.isConnected) {
          SyncManager.scheduleSync();
        }
        return state;
      });
      dispatch(setOfflineStatus(!state.isConnected));
    });

    return () => {
      if (unsub) unsub();
    };
  }, [dispatch]);

  const handleSendQuery = async () => {
    if (!query.trim()) {
      dispatch(setError('Please enter a question'));
      return;
    }

    // Store the query before clearing
    const userQuery = query.trim();

    // Dismiss keyboard
    Keyboard.dismiss();

    // Generate unique IDs
    const timestamp = Date.now();
    const userMessageId = `user-${timestamp}`;
    const assistantMessageId = `assistant-${timestamp}`;

    // Add user message to conversation and save to DB
    const userMessage = {
      id: userMessageId,
      type: 'user',
      text: userQuery,
    };
    dispatch(addMessage(userMessage));
    try {
      await Database.saveMessage(userMessage);
    } catch (error) {
      console.error('Error saving user message:', error);
    }

    // Clear current query input and add empty assistant message
    dispatch(setQuery(''));
    dispatch(setLoading(true));
    dispatch(setError(null));
    dispatch(setCachedResponse(false));

    const assistantMessage = {
      id: assistantMessageId,
      type: 'assistant',
      text: 'Thinking...',
      llmUsed: null,
      category: null,
      responseTime: null,
      isCached: false,
      isQueued: false,
    };
    dispatch(addMessage(assistantMessage));
    try {
      await Database.saveMessage(assistantMessage);
    } catch (error) {
      console.error('Error saving assistant message:', error);
    }

    try {
      const startTime = Date.now();

      // Try to get cached response first
      const cachedResult = await CacheManager.getCachedResponse(userQuery);
      if (cachedResult) {
        // Cache hit - update assistant message
        const updateData = {
          text: cachedResult.response,
          llmUsed: cachedResult.llm_used,
          category: cachedResult.category,
          responseTime: cachedResult.response_time,
          isCached: true,
        };
        dispatch(updateMessage({ id: assistantMessageId, updates: updateData }));
        try {
          await Database.updateMessage(assistantMessageId, {
            text: cachedResult.response,
            llm_used: cachedResult.llm_used,
            category: cachedResult.category,
            response_time: cachedResult.response_time,
            is_cached: 1,
          });
        } catch (error) {
          console.error('Error updating message in DB:', error);
        }
        dispatch(setCachedResponse(true));
        dispatch(setOfflineQueued(false));
        dispatch(setLoading(false));
        return;
      }

      // Always try API call first (NetInfo can be unreliable on Android)
      try {
        const result = await APIClient.query(userQuery);
        const elapsed = Date.now() - startTime;

        // Save to cache
        await CacheManager.saveToCache(
          userQuery,
          result.response,
          result.llm_used,
          result.category,
          elapsed
        );

        // Update assistant message with response
        dispatch(updateMessage({
          id: assistantMessageId,
          updates: {
            text: result.response,
            llmUsed: result.llm_used,
            category: result.category,
            responseTime: elapsed,
            isCached: false,
          },
        }));
        try {
          await Database.updateMessage(assistantMessageId, {
            text: result.response,
            llm_used: result.llm_used,
            category: result.category,
            response_time: elapsed,
            is_cached: 0,
          });
        } catch (error) {
          console.error('Error updating message in DB:', error);
        }
        dispatch(setOfflineQueued(false));
      } catch (apiError) {
        // API call failed - queue for offline sync
        console.log('API call failed, queueing offline:', apiError.message);
        const queueId = await Database.queueQuery(userQuery);
        dispatch(updateMessage({
          id: assistantMessageId,
          updates: {
            text: 'Query saved. Will sync when connection is restored.',
            isQueued: true,
          },
        }));
        try {
          await Database.updateMessage(assistantMessageId, {
            text: 'Query saved. Will sync when connection is restored.',
            is_queued: 1,
          });
        } catch (error) {
          console.error('Error updating message in DB:', error);
        }
        dispatch(setError('Cannot reach server. Query saved and will sync when connection is restored.'));
        dispatch(setOfflineQueued(true));
      }
    } catch (err) {
      // Only handle errors not already handled by offline queue
      if (!err.handled) {
        const errorText = err.message || 'Failed to get response. Please try again.';
        dispatch(updateMessage({
          id: assistantMessageId,
          updates: { text: `Error: ${errorText}` },
        }));
        try {
          await Database.updateMessage(assistantMessageId, {
            text: `Error: ${errorText}`,
          });
        } catch (error) {
          console.error('Error updating message in DB:', error);
        }
        dispatch(setError(errorText));
        dispatch(setOfflineQueued(false));
      }
    } finally {
      dispatch(setLoading(false));
    }
  };

  const handleClearChat = () => {
    if (messages.length === 0) return;

    Alert.alert(
      'Clear Chat',
      'This will delete all messages. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            dispatch(clearMessages());
            try {
              await Database.clearChatHistory();
            } catch (error) {
              console.error('Error clearing chat history:', error);
            }
          },
        },
      ]
    );
  };

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Ionicons name="search-outline" size={48} color={theme.colors.textTertiary} />
      <Text style={[styles.emptyStateText, { color: theme.colors.textTertiary }]}>Ask me anything!</Text>
      <Text style={[styles.emptyStateSubtext, { color: theme.colors.textTertiary }]}>Business news, general knowledge, creative questions</Text>
    </View>
  );

  const renderMessageItem = ({ item }) => <MessageBubble message={item} theme={theme} />;

  // Calculate input area height (approximate)
  const inputAreaHeight = 70 + insets.bottom;

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Status Bar */}
      {isOffline && (
        <View style={[styles.offlineBanner, { backgroundColor: theme.colors.offlineBg }]}>
          <Ionicons name="cloud-offline-outline" size={16} color={theme.colors.offlineText} />
          <Text style={[styles.offlineText, { color: theme.colors.offlineText }]}>No internet connection</Text>
        </View>
      )}

      {/* Clear Chat Button */}
      {messages.length > 0 && (
        <View style={styles.headerActions}>
          <TouchableOpacity
            style={[styles.clearButton, { backgroundColor: theme.colors.surface }]}
            onPress={handleClearChat}
          >
            <Ionicons name="trash-outline" size={18} color={theme.colors.textSecondary} />
            <Text style={[styles.clearButtonText, { color: theme.colors.textSecondary }]}>Clear</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Conversation Area using FlatList */}
      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessageItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={[
          styles.listContent,
          { paddingBottom: inputAreaHeight + keyboardHeight }
        ]}
        ListEmptyComponent={renderEmptyState}
        ListFooterComponent={
          <>
            {loading && (
              <View style={styles.loadingIndicator}>
                <SkeletonMessageBubble theme={theme} />
              </View>
            )}
            {error && (
              <View style={[styles.errorBox, { backgroundColor: theme.colors.offlineBg }]}>
                <Ionicons name="alert-circle-outline" size={18} color={theme.colors.error} />
                <Text style={[styles.errorText, { color: theme.colors.error }]}>{error}</Text>
              </View>
            )}
          </>
        }
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        scrollEnabled={true}
        showsVerticalScrollIndicator={true}
        keyboardShouldPersistTaps="handled"
      />

      {/* Input Area (Fixed at Bottom) */}
      <View style={[
        styles.inputSection,
        {
          position: 'absolute',
          bottom: keyboardHeight,
          left: 0,
          right: 0,
          backgroundColor: theme.colors.background,
          borderTopColor: theme.colors.border,
          // Only add safe area padding when keyboard is closed
          paddingBottom: keyboardHeight > 0 ? 0 : insets.bottom,
        }
      ]}>
        <View style={[styles.inputContainer, { backgroundColor: theme.colors.surface }]}>
          <TextInput
            style={[styles.input, { color: theme.colors.text }]}
            placeholder="Ask me something..."
            placeholderTextColor={theme.colors.textTertiary}
            value={query}
            onChangeText={text => dispatch(setQuery(text))}
            onSubmitEditing={handleSendQuery}
            returnKeyType="send"
            returnKeyLabel="Send"
            editable={!loading}
            multiline
            maxLength={500}
            blurOnSubmit={false}
          />
          <TouchableOpacity
            style={[styles.sendButton, loading && styles.sendButtonDisabled, { backgroundColor: theme.colors.primary }]}
            onPress={handleSendQuery}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Ionicons name="send" size={20} color="#fff" />
            )}
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  headerActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  clearButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  clearButtonText: {
    fontSize: 14,
    marginLeft: 4,
  },
  listContent: {
    flexGrow: 1,
    paddingTop: 8,
    paddingBottom: 8,
  },
  loadingIndicator: {
    padding: 12,
  },
  offlineBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFE5E5',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginBottom: 16,
  },
  offlineText: {
    color: '#FF3B30',
    fontSize: 13,
    marginLeft: 8,
    fontWeight: '500',
  },
  inputSection: {
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 12,
    borderTopColor: '#eee',
    borderTopWidth: 1,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: '#f5f5f5',
    borderRadius: 24,
    paddingLeft: 16,
    paddingRight: 8,
    paddingVertical: 8,
  },
  input: {
    flex: 1,
    fontSize: 16,
    maxHeight: 120,
    paddingVertical: 8,
  },
  sendButton: {
    backgroundColor: '#007AFF',
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  sendButtonDisabled: {
    opacity: 0.6,
  },
  errorBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FFE5E5',
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 14,
    color: '#FF3B30',
    marginLeft: 8,
    flex: 1,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 40,
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#666',
    marginTop: 16,
  },
  emptyStateSubtext: {
    fontSize: 13,
    color: '#999',
    marginTop: 8,
  },
});

export default HomeScreen;
