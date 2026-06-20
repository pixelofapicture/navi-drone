import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useContext, useEffect, useState } from "react";

const STORAGE_KEY = "navi-drone:pi-host";
const PiConnectionContext = createContext(null);

// "navi-drone.local" works if the Pi's mDNS advertising started successfully
// and your phone's network supports mDNS. Otherwise use the Pi's plain IP,
// e.g. "192.168.1.42:8000".
const DEFAULT_HOST = "navi-drone.local:8000";

export function PiConnectionProvider({ children }) {
  const [host, setHostState] = useState(DEFAULT_HOST);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then((saved) => {
      if (saved) setHostState(saved);
      setLoaded(true);
    });
  }, []);

  const setHost = async (newHost) => {
    setHostState(newHost);
    await AsyncStorage.setItem(STORAGE_KEY, newHost);
  };

  const baseUrl = `http://${host}`;
  const wsUrl = `ws://${host}/ws/events`;

  return (
    <PiConnectionContext.Provider value={{ host, setHost, baseUrl, wsUrl, loaded }}>
      {children}
    </PiConnectionContext.Provider>
  );
}

export function usePiConnection() {
  return useContext(PiConnectionContext);
}
