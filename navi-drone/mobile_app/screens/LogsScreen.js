import React, { useCallback, useState } from "react";
import { View, Text, StyleSheet, FlatList, RefreshControl } from "react-native";
import { usePiConnection } from "../PiConnection";
import { colors, type } from "../theme";

function formatTime(ts) {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function LogsScreen() {
  const { baseUrl } = usePiConnection();
  const [logs, setLogs] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const fetchLogs = useCallback(async () => {
    setRefreshing(true);
    try {
      const res = await fetch(`${baseUrl}/api/logs?limit=200`);
      const data = await res.json();
      setLogs(data);
      setError(null);
    } catch (e) {
      setError("Couldn't reach the Pi. Check Settings for the right address.");
    }
    setRefreshing(false);
  }, [baseUrl]);

  React.useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return (
    <View style={styles.container}>
      <Text style={type.h1}>Detection log</Text>
      {error && <Text style={[type.caption, { color: colors.alert, marginTop: 8 }]}>{error}</Text>}
      <FlatList
        style={{ marginTop: 16 }}
        data={logs}
        keyExtractor={(item, i) => `${item.ts}-${i}`}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={fetchLogs} tintColor={colors.accent} />}
        ListEmptyComponent={!error && <Text style={type.caption}>No detections logged yet.</Text>}
        renderItem={({ item }) => (
          <View style={styles.row}>
            <View
              style={[
                styles.badge,
                { backgroundColor: item.name === "Unknown" ? colors.alertDim : colors.accentDim },
              ]}
            >
              <Text
                style={[
                  type.caption,
                  { color: item.name === "Unknown" ? colors.alert : colors.accent, fontWeight: "700" },
                ]}
              >
                {item.name === "Unknown" ? "UNKNOWN" : "MATCH"}
              </Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={type.body}>{item.name}</Text>
              <Text style={type.caption}>{formatTime(item.ts)} · {Math.round(item.similarity * 100)}% confidence</Text>
            </View>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg, padding: 16 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 12,
    paddingHorizontal: 12,
    backgroundColor: colors.surface,
    borderRadius: 10,
    marginBottom: 6,
  },
  badge: { paddingVertical: 4, paddingHorizontal: 8, borderRadius: 6 },
});
