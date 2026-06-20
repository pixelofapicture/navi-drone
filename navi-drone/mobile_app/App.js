import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { StatusBar } from "expo-status-bar";
import React from "react";
import { Text } from "react-native";

import { PiConnectionProvider } from "./PiConnection";
import LiveScreen from "./screens/LiveScreen";
import LogsScreen from "./screens/LogsScreen";
import StatsScreen from "./screens/StatsScreen";
import SettingsScreen from "./screens/SettingsScreen";
import { colors } from "./theme";

const Tab = createBottomTabNavigator();

const ICONS = { Live: "◎", Logs: "≡", Stats: "▥", Settings: "⚙" };

function TabIcon({ route, focused }) {
  return (
    <Text style={{ fontSize: 18, color: focused ? colors.accent : colors.textSecondary }}>
      {ICONS[route.name]}
    </Text>
  );
}

const navTheme = {
  dark: true,
  colors: {
    primary: colors.accent,
    background: colors.bg,
    card: colors.surface,
    text: colors.textPrimary,
    border: colors.border,
    notification: colors.alert,
  },
};

export default function App() {
  return (
    <PiConnectionProvider>
      <StatusBar style="light" />
      <NavigationContainer theme={navTheme}>
        <Tab.Navigator
          screenOptions={({ route }) => ({
            headerStyle: { backgroundColor: colors.bg },
            headerTitleStyle: { color: colors.textPrimary, fontWeight: "800" },
            headerTitle: "NAVI DRONE",
            tabBarStyle: { backgroundColor: colors.surface, borderTopColor: colors.border },
            tabBarActiveTintColor: colors.accent,
            tabBarInactiveTintColor: colors.textSecondary,
            tabBarIcon: ({ focused }) => <TabIcon route={route} focused={focused} />,
          })}
        >
          <Tab.Screen name="Live" component={LiveScreen} />
          <Tab.Screen name="Logs" component={LogsScreen} />
          <Tab.Screen name="Stats" component={StatsScreen} />
          <Tab.Screen name="Settings" component={SettingsScreen} />
        </Tab.Navigator>
      </NavigationContainer>
    </PiConnectionProvider>
  );
}
