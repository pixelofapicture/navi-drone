import React, { useCallback, useState } from "react";
import { View, Text, StyleSheet, FlatList, RefreshControl } from "react-native";
import { usePiConnection } from "../PiConnection";
import { colors, type } from "../theme";

export default function StatsScreen() {
  const { baseUrl } = usePiConnection();
  const [stats, setStats] = useState({ total_detections: 0, by_person: [] });
  const [refreshing, setRefreshing] = useState(false);

  const fetchStats = useCallback(async () => {
    setRefreshing(true);
    try {
      const res = await fetch(`${baseUrl}/api/stats`);
      setStats(await res.json());
    } catch (e) {
      // surfaced via empty state below
    }
    setRefreshing(false);
  }, [baseUrl]);

  React.useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const maxCount = Math.max(1, ...stats.by_person.map((p) => p.count));

  return (
    <View style={styles.container}>
      <Text style={type.h1}>Stats</Text>

      <View style={styles.totalCard}>
        <Text style={type.label}>Total detections</Text>
        <Text style={styles.totalNumber}>{stats.total_detections}</Text>
      </View>

      <Text style={[type.label, { marginTop: 24, marginBottom: 12 }]}>By person</Text>
      <FlatList
        data={stats.by_person}
        keyExtractor={(item) => item.name}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={fetchStats} tintColor={colors.accent} />}
        ListEmptyComponent={<Text style={type.caption}>No data yet.</Text>}
        renderItem={({ item }) => (
          <View style={styles.barRow}>
            <View style={styles.barLabelRow}>
              <Text style={type.body}>{item.name}</Text>
              <Text style={type.caption}>{item.count}</Text>
            </View>
            <View style={styles.barTrack}>
              <View
                style={[
                  styles.barFill,
                  {
                    width: `${(item.count / maxCount) * 100}%`,
                    backgroundColor: item.name === "Unknown" ? colors.alert : colors.accent,
                  },
                ]}
              />
            </View>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg, padding: 16 },
  totalCard: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    padding: 18,
    marginTop: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  totalNumber: { fontSize: 40, fontWeight: "800", color: colors.accent, marginTop: 6 },
  barRow: { marginBottom: 14 },
  barLabelRow: { flexDirection: "row", justifyContent: "space-between", marginBottom: 6 },
  barTrack: { height: 8, borderRadius: 4, backgroundColor: colors.surfaceRaised, overflow: "hidden" },
  barFill: { height: "100%", borderRadius: 4 },
});
