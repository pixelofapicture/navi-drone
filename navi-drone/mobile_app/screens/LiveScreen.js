import React, { useEffect, useRef, useState } from "react";
import { View, Text, StyleSheet, FlatList, Animated } from "react-native";
import { WebView } from "react-native-webview";
import { usePiConnection } from "../PiConnection";
import { colors, type } from "../theme";

const MAX_TICKER_ITEMS = 20;

export default function LiveScreen() {
  const { baseUrl, wsUrl, host } = usePiConnection();
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState([]);
  const wsRef = useRef(null);
  const pulse = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 0.3, duration: 800, useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 1, duration: 800, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  useEffect(() => {
    let ws;
    try {
      ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onclose = () => setConnected(false);
      ws.onerror = () => setConnected(false);
      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data);
          setEvents((prev) => [{ ...data, id: `${data.ts}-${data.name}` }, ...prev].slice(0, MAX_TICKER_ITEMS));
        } catch (e) {}
      };
    } catch (e) {
      setConnected(false);
    }
    return () => ws && ws.close();
  }, [wsUrl]);

  return (
    <View style={styles.container}>
      <View style={styles.statusRow}>
        <Animated.View
          style={[
            styles.dot,
            { backgroundColor: connected ? colors.accent : colors.alert, opacity: pulse },
          ]}
        />
        <Text style={type.label}>{connected ? "LIVE LINK ESTABLISHED" : "NO LINK"}</Text>
        <Text style={[type.caption, { marginLeft: "auto" }]}>{host}</Text>
      </View>

      <View style={styles.videoFrame}>
        <WebView
          source={{ uri: `${baseUrl}/video_feed` }}
          style={styles.video}
          startInLoadingState
        />
      </View>

      <Text style={[type.label, styles.tickerLabel]}>Recognition events</Text>
      <FlatList
        data={events}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingBottom: 24 }}
        ListEmptyComponent={
          <Text style={[type.caption, { padding: 16 }]}>
            No events yet — they'll appear here as soon as a face is recognized.
          </Text>
        }
        renderItem={({ item }) => (
          <View style={styles.eventRow}>
            <View
              style={[
                styles.eventDot,
                { backgroundColor: item.name === "Unknown" ? colors.alert : colors.accent },
              ]}
            />
            <Text style={type.body}>{item.name}</Text>
            <Text style={[type.caption, { marginLeft: "auto" }]}>
              {Math.round(item.similarity * 100)}% match
            </Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg, padding: 16 },
  statusRow: { flexDirection: "row", alignItems: "center", marginBottom: 12, gap: 8 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  videoFrame: {
    borderRadius: 16,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    aspectRatio: 4 / 3,
  },
  video: { flex: 1, backgroundColor: colors.surface },
  tickerLabel: { marginTop: 18, marginBottom: 8 },
  eventRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: colors.surface,
    borderRadius: 10,
    marginBottom: 6,
  },
  eventDot: { width: 6, height: 6, borderRadius: 3 },
});
