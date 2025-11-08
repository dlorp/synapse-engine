import { create } from 'zustand';

interface WebSocketState {
  connected: boolean;
  connectionError: string | null;
  setConnected: (connected: boolean) => void;
  setConnectionError: (error: string | null) => void;
}

export const useWebSocketStore = create<WebSocketState>((set) => ({
  connected: false,
  connectionError: null,
  setConnected: (connected) => set({ connected, connectionError: connected ? null : undefined }),
  setConnectionError: (error) => set({ connectionError: error, connected: false }),
}));
