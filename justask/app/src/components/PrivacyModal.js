import React, { useContext } from 'react';
import { Modal, View, ScrollView, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ThemeContext } from '../theme/ThemeContext';
import { PRIVACY_TITLE, PRIVACY_SECTIONS } from '../legal/privacyText';

const PrivacyModal = ({ visible, onClose }) => {
  const { theme } = useContext(ThemeContext);
  const c = theme.colors;

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <SafeAreaView style={[styles.container, { backgroundColor: c.background }]}>
        <View style={[styles.header, { borderBottomColor: c.border }]}>
          <Text style={[styles.title, { color: c.text }]}>{PRIVACY_TITLE}</Text>
          <TouchableOpacity onPress={onClose} accessibilityRole="button" accessibilityLabel="Close">
            <Text style={[styles.close, { color: c.primary }]}>Close</Text>
          </TouchableOpacity>
        </View>
        <ScrollView contentContainerStyle={styles.body}>
          {PRIVACY_SECTIONS.map((s) => (
            <View key={s.heading} style={styles.section}>
              <Text style={[styles.heading, { color: c.text }]}>{s.heading}</Text>
              {s.items.map((item) => (
                <Text key={item} style={[styles.item, { color: c.textSecondary }]}>
                  {'• '}
                  {item}
                </Text>
              ))}
            </View>
          ))}
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  title: { fontSize: 18, fontWeight: '600', flex: 1, marginRight: 12 },
  close: { fontSize: 16, fontWeight: '600' },
  body: { padding: 16, paddingBottom: 40 },
  section: { marginBottom: 20 },
  heading: { fontSize: 16, fontWeight: '600', marginBottom: 8 },
  item: { fontSize: 15, lineHeight: 22, marginBottom: 6 },
});

export default PrivacyModal;
