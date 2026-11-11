import React, { useEffect } from 'react';
import { AppState } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Provider } from 'react-redux';
import { Ionicons } from '@expo/vector-icons';

import store from './src/store';
import HomeScreen from './src/screens/HomeScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import { ThemeProvider } from './src/theme/ThemeContext';
import AgeGate from './src/components/AgeGate';
import ServerWake from './src/services/ServerWake';

const Tab = createBottomTabNavigator();

export default function App() {
  // Start waking the server as soon as the app opens (and when it returns to
  // the foreground), so most of the free-plan wake-up passes before the user asks.
  useEffect(() => {
    ServerWake.ensureAwake();
    const sub = AppState.addEventListener('change', (s) => {
      if (s === 'active') ServerWake.ensureAwake();
    });
    return () => sub.remove();
  }, []);

  return (
    <Provider store={store}>
      <ThemeProvider>
        <AgeGate>
        <NavigationContainer>
        <Tab.Navigator
          screenOptions={({ route }) => ({
            tabBarIcon: ({ focused, color, size }) => {
              let iconName;

              if (route.name === 'Home') {
                iconName = focused ? 'search' : 'search-outline';
              } else if (route.name === 'Settings') {
                iconName = focused ? 'settings' : 'settings-outline';
              }

              return <Ionicons name={iconName} size={size} color={color} />;
            },
            tabBarActiveTintColor: '#007AFF',
            tabBarInactiveTintColor: '#8E8E93',
            headerShown: true,
          })}
        >
          <Tab.Screen
            name="Home"
            component={HomeScreen}
            options={{
              title: 'JustAsk',
              headerStyle: {
                backgroundColor: '#f5f5f5',
              },
              headerTitleStyle: {
                fontWeight: '600',
                fontSize: 18,
              },
            }}
          />
          <Tab.Screen
            name="Settings"
            component={SettingsScreen}
            options={{
              title: 'Settings',
              headerStyle: {
                backgroundColor: '#f5f5f5',
              },
              headerTitleStyle: {
                fontWeight: '600',
                fontSize: 18,
              },
            }}
          />
        </Tab.Navigator>
        </NavigationContainer>
        </AgeGate>
      </ThemeProvider>
    </Provider>
  );
}
