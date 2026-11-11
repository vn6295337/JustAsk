import React, { useContext, useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ThemeContext } from '../theme/ThemeContext';
import PrivacyModal from './PrivacyModal';

// Stored answer: 'adult' unlocks the app; 'under18' keeps it locked for good.
export const AGE_GATE_KEY = 'justask.ageGate.v1';

/**
 * Blocks the app until the user confirms they are 18 or older
 * (Gemini API terms). A "No" answer is stored and keeps the app locked.
 */
const AgeGate = ({ children }) => {
  const { theme } = useContext(ThemeContext);
  const c = theme.colors;
  const [status, setStatus] = useState('loading'); // loading | unknown | adult | under18
  const [showPrivacy, setShowPrivacy] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(AGE_GATE_KEY)
      .then((v) => setStatus(v === 'adult' || v === 'under18' ? v : 'unknown'))
      .catch(() => setStatus('unknown'));
  }, []);

  const answer = async (value) => {
    setStatus(value);
    try {
      await AsyncStorage.setItem(AGE_GATE_KEY, value);
    } catch (e) {
      console.error('Failed to save age answer:', e);
    }
  };

  if (status === 'adult') return children;

  if (status === 'loading') {
    return (
      <View style={[styles.center, { backgroundColor: c.background }]}>
        <ActivityIndicator color={c.primary} />
      </View>
    );
  }

  return (
    <SafeAreaView style={[styles.center, { backgroundColor: c.background }]}>
      {status === 'under18' ? (
        <Text style={[styles.title, { color: c.text }]}>Sorry, JustAsk is for adults only.</Text>
      ) : (
        <>
          <Text style={[styles.title, { color: c.text }]}>
            You must be 18 or older to use JustAsk.
          </Text>
          <Text style={[styles.question, { color: c.textSecondary }]}>Are you 18 or older?</Text>
          <View style={styles.row}>
            <TouchableOpacity
              style={[styles.button, { backgroundColor: c.primary }]}
              onPress={() => answer('adult')}
              accessibilityRole="button"
            >
              <Text style={styles.buttonText}>Yes</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, { backgroundColor: c.textTertiary }]}
              onPress={() => answer('under18')}
              accessibilityRole="button"
            >
              <Text style={styles.buttonText}>No</Text>
            </TouchableOpacity>
          </View>
        </>
      )}
      <TouchableOpacity onPress={() => setShowPrivacy(true)} accessibilityRole="link">
        <Text style={[styles.link, { color: c.primary }]}>Privacy and Terms</Text>
      </TouchableOpacity>
      <PrivacyModal visible={showPrivacy} onClose={() => setShowPrivacy(false)} />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  title: { fontSize: 20, fontWeight: '600', textAlign: 'center', marginBottom: 12 },
  question: { fontSize: 17, textAlign: 'center', marginBottom: 24 },
  row: { flexDirection: 'row', marginBottom: 32 },
  button: { paddingVertical: 12, paddingHorizontal: 32, borderRadius: 10, marginHorizontal: 8 },
  buttonText: { color: '#ffffff', fontSize: 17, fontWeight: '600' },
  link: { fontSize: 15, textDecorationLine: 'underline', marginTop: 8 },
});

export default AgeGate;
