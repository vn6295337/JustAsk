import React, { createContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const THEME_KEY = '@justask_theme';

export const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Load theme preference on app start
  useEffect(() => {
    const loadTheme = async () => {
      try {
        const savedTheme = await AsyncStorage.getItem(THEME_KEY);
        if (savedTheme !== null) {
          setIsDarkMode(JSON.parse(savedTheme));
        }
      } catch (error) {
        console.error('Error loading theme:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadTheme();
  }, []);

  const toggleDarkMode = async () => {
    try {
      const newValue = !isDarkMode;
      setIsDarkMode(newValue);
      await AsyncStorage.setItem(THEME_KEY, JSON.stringify(newValue));
    } catch (error) {
      console.error('Error saving theme:', error);
    }
  };

  const theme = isDarkMode ? darkTheme : lightTheme;

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleDarkMode, theme, isLoading }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Light theme colors
const lightTheme = {
  isDark: false,
  colors: {
    background: '#ffffff',
    surface: '#f5f5f5',
    primary: '#007AFF',
    secondary: '#5AC8FA',
    text: '#000000',
    textSecondary: '#333333',
    textTertiary: '#666666',
    border: '#e5e5e5',
    userBubble: '#007AFF',
    userText: '#ffffff',
    assistantBubble: '#e5e5ea',
    assistantText: '#000000',
    error: '#FF3B30',
    success: '#34C759',
    warning: '#FF9500',
    offlineBg: '#FFE5E5',
    offlineText: '#FF3B30',
  },
};

// Dark theme colors
const darkTheme = {
  isDark: true,
  colors: {
    background: '#1a1a1a',
    surface: '#2d2d2d',
    primary: '#0a84ff',
    secondary: '#30b0c0',
    text: '#ffffff',
    textSecondary: '#e0e0e0',
    textTertiary: '#a0a0a0',
    border: '#404040',
    userBubble: '#0a84ff',
    userText: '#ffffff',
    assistantBubble: '#3a3a3a',
    assistantText: '#ffffff',
    error: '#ff453a',
    success: '#30b0c0',
    warning: '#ff9500',
    offlineBg: '#3a2a2a',
    offlineText: '#ff8888',
  },
};
