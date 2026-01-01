import React, { useState, useEffect, useContext } from 'react';
import {
  View,
  ScrollView,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Switch,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from '@react-navigation/native';
import Constants from 'expo-constants';
import CacheManager from '../services/CacheManager';
import SyncManager from '../services/SyncManager';
import Database from '../services/Database';
import { ThemeContext } from '../theme/ThemeContext';
import { useDispatch } from 'react-redux';
import { clearMessages } from '../store/querySlice';

const SettingsScreen = () => {
  const { isDarkMode, toggleDarkMode, theme } = useContext(ThemeContext);
  const dispatch = useDispatch();
  const [cacheSize, setCacheSize] = useState(0);
  const [pendingCount, setPendingCount] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncedResponses, setSyncedResponses] = useState([]);
  const [chatCount, setChatCount] = useState(0);
  const APP_VERSION = Constants.expoConfig?.extra?.appVersion || '1.0.0';
  const CACHE_LIMIT = parseInt(Constants.expoConfig?.extra?.cacheSizeLimitMb, 10) || 50;
  const BACKEND_URL = Constants.expoConfig?.extra?.backendUrl || 'Not configured';
  const API_TIMEOUT = Constants.expoConfig?.extra?.apiTimeout || 'Not configured';

  // Calculate cache size and pending queries when screen comes into focus
  useFocusEffect(
    React.useCallback(() => {
      calculateCacheSize();
      updateSyncStatus();
      updateChatCount();
    }, [])
  );

  const updateChatCount = async () => {
    try {
      const history = await Database.loadChatHistory();
      setChatCount(history.length);
    } catch (err) {
      console.error('Error getting chat count:', err);
      setChatCount(0);
    }
  };

  const calculateCacheSize = async () => {
    try {
      const size = await CacheManager.getCacheSize();
      setCacheSize(size);
    } catch (err) {
      console.error('Error calculating cache size:', err);
      setCacheSize(0);
    }
  };

  const updateSyncStatus = async () => {
    try {
      const status = await SyncManager.getStatus();
      setPendingCount(status.pendingCount);
      setIsSyncing(status.isSyncing);

      // Get synced responses
      const synced = await Database.getSyncedResponses();
      setSyncedResponses(synced.slice(0, 5)); // Show last 5
    } catch (err) {
      console.error('Error getting sync status:', err);
    }
  };

  const handleSyncNow = async () => {
    if (isSyncing) {
      Alert.alert('Sync in Progress', 'Please wait for current sync to complete');
      return;
    }

    if (pendingCount === 0) {
      Alert.alert('No Pending Queries', 'All queries are synced');
      return;
    }

    setIsSyncing(true);
    try {
      const success = await SyncManager.syncPending();
      if (success) {
        Alert.alert('Sync Complete', `Successfully synced ${pendingCount} queries`);
        await updateSyncStatus();
      } else {
        Alert.alert('Sync Failed', 'Unable to sync queries. Check your internet connection and try again.');
      }
    } catch (err) {
      Alert.alert('Sync Error', err.message || 'An error occurred during sync');
    } finally {
      setIsSyncing(false);
      await updateSyncStatus();
    }
  };

  const handleClearCache = () => {
    Alert.alert(
      'Clear Cache',
      'This will delete all cached responses. Continue?',
      [
        {
          text: 'Cancel',
          onPress: () => {},
          style: 'cancel',
        },
        {
          text: 'Clear',
          onPress: async () => {
            try {
              await CacheManager.clearAll();
              setCacheSize(0);
              Alert.alert('Success', 'Cache cleared');
            } catch (err) {
              Alert.alert('Error', 'Failed to clear cache: ' + err.message);
            }
          },
          style: 'destructive',
        },
      ]
    );
  };

  const handleClearChatHistory = () => {
    if (chatCount === 0) {
      Alert.alert('No Messages', 'Chat history is already empty');
      return;
    }

    Alert.alert(
      'Clear Chat History',
      `This will delete all ${chatCount} messages. Continue?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              dispatch(clearMessages());
              await Database.clearChatHistory();
              setChatCount(0);
              Alert.alert('Success', 'Chat history cleared');
            } catch (err) {
              Alert.alert('Error', 'Failed to clear chat history: ' + err.message);
            }
          },
        },
      ]
    );
  };

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={[styles.section, { backgroundColor: theme.colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.textTertiary }]}>Appearance</Text>
        <View style={[styles.settingItem, { borderTopColor: theme.colors.border }]}>
          <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
            <Ionicons
              name={isDarkMode ? "moon" : "sunny"}
              size={20}
              color={theme.colors.primary}
              style={{ marginRight: 12 }}
            />
            <View>
              <Text style={[styles.settingLabel, { color: theme.colors.textSecondary }]}>Dark Mode</Text>
              <Text style={[styles.settingValue, { color: theme.colors.textTertiary }]}>
                {isDarkMode ? 'Enabled' : 'Disabled'}
              </Text>
            </View>
          </View>
          <Switch
            value={isDarkMode}
            onValueChange={toggleDarkMode}
            trackColor={{ false: '#767577', true: '#81c784' }}
            thumbColor={isDarkMode ? theme.colors.primary : '#f4f3f4'}
          />
        </View>
      </View>

      <View style={[styles.section, { backgroundColor: theme.colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.textTertiary }]}>App Information</Text>
        <View style={[styles.settingItem, { borderTopColor: theme.colors.border }]}>
          <View>
            <Text style={[styles.settingLabel, { color: theme.colors.textSecondary }]}>Version</Text>
            <Text style={[styles.settingValue, { color: theme.colors.textTertiary }]}>{APP_VERSION}</Text>
          </View>
        </View>
        <View style={[styles.settingItem, { borderTopColor: theme.colors.border }]}>
          <View>
            <Text style={[styles.settingLabel, { color: theme.colors.textSecondary }]}>Backend URL</Text>
            <Text style={[styles.settingValue, { color: theme.colors.textTertiary }]}>{BACKEND_URL}</Text>
          </View>
        </View>
        <View style={[styles.settingItem, { borderTopColor: theme.colors.border }]}>
          <View>
            <Text style={[styles.settingLabel, { color: theme.colors.textSecondary }]}>API Timeout</Text>
            <Text style={[styles.settingValue, { color: theme.colors.textTertiary }]}>{API_TIMEOUT}ms</Text>
          </View>
        </View>
      </View>

      <View style={[styles.section, { backgroundColor: theme.colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.textTertiary }]}>Storage</Text>
        <View style={[styles.settingItem, { borderTopColor: theme.colors.border }]}>
          <View>
            <Text style={[styles.settingLabel, { color: theme.colors.textSecondary }]}>Cache Size</Text>
            <Text style={[styles.settingValue, { color: theme.colors.textTertiary }]}>{cacheSize.toFixed(2)} MB / {CACHE_LIMIT} MB</Text>
          </View>
        </View>
        <TouchableOpacity style={[styles.settingItem, { borderTopColor: theme.colors.border }]} onPress={handleClearCache}>
          <View>
            <Text style={[styles.settingLabel, { color: theme.colors.textSecondary }]}>Clear Cache</Text>
            <Text style={[styles.settingValue, { color: theme.colors.textTertiary }]}>Delete all cached responses</Text>
          </View>
          <Ionicons name="trash-outline" size={24} color={theme.colors.error} />
        </TouchableOpacity>
        <TouchableOpacity style={[styles.settingItem, { borderTopColor: theme.colors.border }]} onPress={handleClearChatHistory}>
          <View>
            <Text style={[styles.settingLabel, { color: theme.colors.textSecondary }]}>Clear Chat History</Text>
            <Text style={[styles.settingValue, { color: theme.colors.textTertiary }]}>{chatCount} messages stored</Text>
          </View>
          <Ionicons name="chatbubbles-outline" size={24} color={theme.colors.error} />
        </TouchableOpacity>
      </View>

      <View style={[styles.section, { backgroundColor: theme.colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.textTertiary }]}>Offline Sync</Text>
        <View style={[styles.settingItem, { borderTopColor: theme.colors.border }]}>
          <View>
            <Text style={[styles.settingLabel, { color: theme.colors.textSecondary }]}>Pending Queries</Text>
            <Text style={[styles.settingValue, { color: theme.colors.textTertiary }]}>{pendingCount} queries waiting to sync</Text>
          </View>
        </View>
        <TouchableOpacity
          style={[styles.settingItem, styles.syncButton, { backgroundColor: theme.colors.background, borderTopColor: theme.colors.border }]}
          onPress={handleSyncNow}
          disabled={isSyncing || pendingCount === 0}
        >
          <View>
            <Text style={[styles.settingLabel, { color: theme.colors.textSecondary }]}>Sync Now</Text>
            <Text style={[styles.settingValue, { color: theme.colors.textTertiary }]}>Manually sync offline queries</Text>
          </View>
          {isSyncing ? (
            <ActivityIndicator size="small" color={theme.colors.primary} />
          ) : (
            <Ionicons name="sync-outline" size={24} color={pendingCount > 0 ? theme.colors.primary : theme.colors.textTertiary} />
          )}
        </TouchableOpacity>
      </View>

      {syncedResponses.length > 0 && (
        <View style={[styles.section, { backgroundColor: theme.colors.surface }]}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textTertiary }]}>Recent Synced Responses</Text>
          {syncedResponses.map((item, index) => (
            <View key={index} style={[styles.syncedItem, { backgroundColor: theme.colors.background }]}>
              <Text style={[styles.syncedQuery, { color: theme.colors.textSecondary }]} numberOfLines={1}>{item.query}</Text>
              <Text style={[styles.syncedResponse, { color: theme.colors.textTertiary }]} numberOfLines={2}>{item.response}</Text>
              <View style={styles.syncedMeta}>
                <Text style={[styles.syncedMetaText, { color: theme.colors.textTertiary }]}>Model: {item.llm_used}</Text>
                <Text style={[styles.syncedMetaText, { color: theme.colors.textTertiary }]}>•</Text>
                <Text style={[styles.syncedMetaText, { color: theme.colors.textTertiary }]}>Category: {item.category}</Text>
              </View>
            </View>
          ))}
        </View>
      )}

      <View style={[styles.section, { backgroundColor: theme.colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.textTertiary }]}>Privacy & Data</Text>
        <View style={[styles.privacyBox, { backgroundColor: theme.colors.background }]}>
          <Ionicons name="shield-checkmark-outline" size={32} color={theme.colors.success} />
          <Text style={[styles.privacyText, { color: theme.colors.textSecondary }]}>
            ✅ Your queries are stored locally only{'\n'}
            ✅ No cloud sync{'\n'}
            ✅ No user accounts required{'\n'}
            ✅ No tracking or analytics{'\n'}
            ✅ No API keys in the app
          </Text>
        </View>
      </View>

      <View style={[styles.section, { backgroundColor: theme.colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.textTertiary }]}>About</Text>
        <View style={[styles.aboutBox, { backgroundColor: theme.colors.background }]}>
          <Text style={[styles.aboutTitle, { color: theme.colors.textSecondary }]}>JustAsk</Text>
          <Text style={[styles.aboutSubtitle, { color: theme.colors.textTertiary }]}>Intelligent LLM Query Router</Text>
          <Text style={[styles.aboutDescription, { color: theme.colors.textTertiary }]}>
            Route your queries to the best free LLM provider (Gemini, Groq, OpenRouter) with
            automatic failover and offline support.
          </Text>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  section: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomColor: '#f5f5f5',
    borderBottomWidth: 8,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#666',
    textTransform: 'uppercase',
    marginBottom: 12,
    letterSpacing: 0.5,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderTopColor: '#f5f5f5',
    borderTopWidth: 1,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginBottom: 4,
  },
  settingValue: {
    fontSize: 13,
    color: '#999',
  },
  syncButton: {
    backgroundColor: '#f9f9f9',
    borderRadius: 8,
    marginTop: 8,
    padding: 12,
  },
  syncedItem: {
    backgroundColor: '#f9f9f9',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  syncedQuery: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  syncedResponse: {
    fontSize: 13,
    color: '#666',
    marginBottom: 8,
  },
  syncedMeta: {
    flexDirection: 'row',
    gap: 8,
  },
  syncedMetaText: {
    fontSize: 11,
    color: '#999',
  },
  privacyBox: {
    backgroundColor: '#f9f9f9',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  privacyText: {
    fontSize: 13,
    color: '#333',
    marginLeft: 12,
    lineHeight: 20,
    flex: 1,
  },
  aboutBox: {
    backgroundColor: '#f9f9f9',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  aboutTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#333',
    marginBottom: 4,
  },
  aboutSubtitle: {
    fontSize: 13,
    color: '#666',
    marginBottom: 12,
  },
  aboutDescription: {
    fontSize: 13,
    color: '#666',
    textAlign: 'center',
    lineHeight: 20,
  },
});

export default SettingsScreen;
