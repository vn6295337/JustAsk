import React, { useContext, useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ThemeContext } from '../theme/ThemeContext';
import ServerWake from '../services/ServerWake';

export const WAKING_TEXT =
  '☕ Waking up the server. This takes about a minute the first time. You can type your question now.';
export const READY_TEXT = '✓ Ready';
export const TIMEOUT_TEXT = 'The server is taking longer than usual. Please try again in a minute.';
const READY_VISIBLE_MS = 2000;

/**
 * Banner shown while the free-plan server wakes up.
 * Hidden when the server answered quickly (no 'waking' phase).
 */
const ServerStatusBanner = () => {
  const { theme } = useContext(ThemeContext);
  const c = theme.colors;
  const [status, setStatus] = useState(ServerWake.getState().status);
  const [showReady, setShowReady] = useState(false);
  const wasWaking = useRef(status === 'waking');
  const readyTimer = useRef(null);

  useEffect(() => {
    const unsubscribe = ServerWake.subscribe((s) => {
      setStatus(s.status);
      if (s.status === 'waking') wasWaking.current = true;
      if (s.status === 'ready' && wasWaking.current) {
        wasWaking.current = false;
        setShowReady(true);
        clearTimeout(readyTimer.current);
        readyTimer.current = setTimeout(() => setShowReady(false), READY_VISIBLE_MS);
      }
      if (s.status === 'timeout') wasWaking.current = false;
    });
    return () => {
      unsubscribe();
      clearTimeout(readyTimer.current);
    };
  }, []);

  let text = null;
  let bg = c.surface;
  let fg = c.textSecondary;
  if (status === 'waking') {
    text = WAKING_TEXT;
  } else if (status === 'timeout') {
    text = TIMEOUT_TEXT;
    fg = c.error;
  } else if (status === 'ready' && showReady) {
    text = READY_TEXT;
    fg = c.success;
  }
  if (!text) return null;

  return (
    <View
      style={[styles.banner, { backgroundColor: bg, borderBottomColor: c.border }]}
      accessibilityLiveRegion="polite"
    >
      <Text style={[styles.text, { color: fg }]}>{text}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  banner: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  text: { fontSize: 14, lineHeight: 20, textAlign: 'center' },
});

export default ServerStatusBanner;
