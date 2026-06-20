import React, { useState } from "react";
import { View, Text, StyleSheet, TextInput, Pressable } from "react-native";
import { usePiConnection } from "../PiConnection";
import { colors, type } from "../theme";

export default function SettingsScreen() {
  const { host, setHost, baseUrl } = usePiConnection();
  const [draft, setDraft] = useState(host);
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);

  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await fetch(`http://${draft}/api/health`);
      const data = await res.json();
      setTestResult(data.status === "ok" ? "ok" : "starting");
    } catch (e) {
      setTestResult("fail");
    }
    setTesting(false);
  };

  return (
    <View style={styles.container}>
      <Text style={type.h1}>Settings</Text>

      <Text style={[type.label, { marginTop: 28 }]}>Pi address</Text>
      <Text style={[type.caption, { marginTop: 4, marginBottom: 10 }]}>
        Try "navi-drone.local:8000" first. If your phone's network doesn't
        support mDNS, use the Pi's IP instead, e.g. "192.168.1.42:8000".
      </Text>
      <TextInput
        value={draft}
        onChangeText={setDraft}
        autoCapitalize="none"
        autoCorrect={false}
        placeholder="192.168.1.42:8000"
        placeholderTextColor={colors.textSecondary}
        style={styles.input}
      />

      <View style={styles.buttonRow}>
        <Pressable style={styles.secondaryButton} onPress={testConnection} disabled={testing}>
          <Text style={styles.secondaryButtonText}>{testing ? "Testing..." : "Test connection"}</Text>
        </Pressable>
        <Pressable
          style={styles.primaryButton}
          onPress={() => setHost(draft)}
        >
          <Text style={styles.primaryButtonText}>Save</Text>
        </Pressable>
      </View>

      {testResult === "ok" && (
        <Text style={[type.caption, { color: colors.accent, marginTop: 12 }]}>
          Connected — the Pi is online and streaming.
        </Text>
      )}
      {testResult === "starting" && (
        <Text style={[type.caption, { color: colors.textSecondary, marginTop: 12 }]}>
          Reached the Pi, but the camera hasn't produced a frame yet. Give it a moment.
        </Text>
      )}
      {testResult === "fail" && (
        <Text style={[type.caption, { color: colors.alert, marginTop: 12 }]}>
          Couldn't reach that address. Make sure your phone is on the same WiFi as the Pi.
        </Text>
      )}

      <Text style={[type.label, { marginTop: 32 }]}>Currently active</Text>
      <Text style={[type.mono, { marginTop: 6 }]}>{baseUrl}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg, padding: 16 },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    borderRadius: 10,
    padding: 12,
    color: colors.textPrimary,
    fontFamily: "monospace",
  },
  buttonRow: { flexDirection: "row", gap: 10, marginTop: 14 },
  primaryButton: {
    backgroundColor: colors.accent,
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 18,
  },
  primaryButtonText: { color: colors.bg, fontWeight: "700" },
  secondaryButton: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 18,
  },
  secondaryButtonText: { color: colors.textPrimary, fontWeight: "600" },
});
