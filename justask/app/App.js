import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Provider } from 'react-redux';
import { Ionicons } from '@expo/vector-icons';

import store from './src/store';
import HomeScreen from './src/screens/HomeScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import { ThemeProvider } from './src/theme/ThemeContext';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <Provider store={store}>
      <ThemeProvider>
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
      </ThemeProvider>
    </Provider>
  );
}
