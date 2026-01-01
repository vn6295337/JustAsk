import React, { useEffect } from 'react';
import { View, StyleSheet, Animated } from 'react-native';

const SkeletonLoader = ({ width = '100%', height = 20, style = {}, theme }) => {
  const shimmerValue = new Animated.Value(0);

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(shimmerValue, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(shimmerValue, {
          toValue: 0,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, [shimmerValue]);

  const opacity = shimmerValue.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: [0.3, 0.6, 0.3],
  });

  const backgroundColor = theme?.colors?.surface || '#e0e0e0';

  return (
    <Animated.View
      style={[
        styles.skeleton,
        {
          width,
          height,
          backgroundColor,
          opacity,
        },
        style,
      ]}
    />
  );
};

const SkeletonMessageBubble = ({ theme }) => {
  return (
    <View style={styles.messageContainer}>
      <View style={[styles.bubble, { backgroundColor: theme?.colors?.surface || '#e0e0e0' }]}>
        <SkeletonLoader height={40} theme={theme} style={{ marginBottom: 8 }} />
        <SkeletonLoader height={40} width="90%" theme={theme} />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  skeleton: {
    borderRadius: 6,
  },
  messageContainer: {
    flexDirection: 'row',
    marginVertical: 8,
    paddingHorizontal: 16,
  },
  bubble: {
    maxWidth: '85%',
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
    width: '85%',
  },
});

export { SkeletonLoader, SkeletonMessageBubble };
