import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { formatProvider } from '../utils/providerFormatter';

const MessageBubble = ({ message, theme }) => {
  const isUser = message.type === 'user';

  return (
    <View style={[styles.messageContainer, isUser && styles.userContainer]}>
      <View style={[
        styles.bubble,
        isUser
          ? { backgroundColor: theme?.colors?.userBubble || '#007AFF' }
          : { backgroundColor: theme?.colors?.assistantBubble || '#e5e5ea' }
      ]}>
        <Text style={[
          styles.text,
          isUser
            ? { color: theme?.colors?.userText || '#fff' }
            : { color: theme?.colors?.assistantText || '#000' }
        ]}>
          {message.text}
        </Text>

        {/* Metadata for assistant messages */}
        {!isUser && (message.llmUsed || message.category || message.responseTime) && (
          <View style={styles.metadata}>
            {message.llmUsed && (
              <View style={styles.metadataRow}>
                <Text style={styles.metadataLabel}>Model:</Text>
                <View style={styles.modelDisplay}>
                  <Text style={styles.metadataValue}>{formatProvider(message.llmUsed).displayName}</Text>
                  {formatProvider(message.llmUsed).subtitle && (
                    <Text style={styles.modelSubtitle}>{formatProvider(message.llmUsed).subtitle}</Text>
                  )}
                </View>
              </View>
            )}
            {message.category && (
              <View style={styles.metadataRow}>
                <Text style={styles.metadataLabel}>Category:</Text>
                <Text style={styles.metadataValue}>{message.category.replace('_', ' ')}</Text>
              </View>
            )}
            {message.responseTime && (
              <View style={styles.metadataRow}>
                <Text style={styles.metadataLabel}>Time:</Text>
                <Text style={styles.metadataValue}>{(message.responseTime / 1000).toFixed(1)}s</Text>
              </View>
            )}
          </View>
        )}

        {/* Status badges */}
        <View style={styles.badgesContainer}>
          {message.isCached && (
            <View style={styles.badge}>
              <Ionicons name="layers-outline" size={10} color="#666" />
              <Text style={styles.badgeText}>Cached</Text>
            </View>
          )}
          {message.isQueued && (
            <View style={styles.badge}>
              <Ionicons name="hourglass-outline" size={10} color="#666" />
              <Text style={styles.badgeText}>Queued</Text>
            </View>
          )}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  messageContainer: {
    flexDirection: 'row',
    marginVertical: 8,
    paddingHorizontal: 16,
  },
  userContainer: {
    justifyContent: 'flex-end',
  },
  bubble: {
    maxWidth: '85%',
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  userBubble: {
    backgroundColor: '#007AFF',
  },
  assistantBubble: {
    backgroundColor: '#e5e5ea',
  },
  text: {
    fontSize: 15,
    lineHeight: 22,
  },
  userText: {
    color: '#fff',
  },
  assistantText: {
    color: '#000',
  },
  metadata: {
    marginTop: 8,
    borderTopColor: 'rgba(0,0,0,0.1)',
    borderTopWidth: 1,
    paddingTop: 6,
  },
  metadataRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 2,
  },
  metadataLabel: {
    fontSize: 11,
    color: 'rgba(0,0,0,0.6)',
    textTransform: 'uppercase',
  },
  metadataValue: {
    fontSize: 11,
    fontWeight: '600',
    color: 'rgba(0,0,0,0.7)',
  },
  modelDisplay: {
    flexDirection: 'column',
    alignItems: 'flex-end',
  },
  modelSubtitle: {
    fontSize: 9,
    fontWeight: '400',
    color: 'rgba(0,0,0,0.5)',
    marginTop: 1,
  },
  badgesContainer: {
    flexDirection: 'row',
    marginTop: 6,
    gap: 6,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.05)',
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 4,
    gap: 3,
  },
  badgeText: {
    fontSize: 10,
    color: '#666',
  },
});

export default MessageBubble;
