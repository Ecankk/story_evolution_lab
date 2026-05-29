// src/services/socket.ts
import type { Turn } from "@/types";
import { useStoryStore } from "@/stores/storyStore";

export class SocketService {
  private ws: WebSocket | null = null;
  private storyId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(storyId: string) {
    this.storyId = storyId;
  }

  public connect() {
    if (this.ws) return;

    // Use Vite proxy /ws path
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host; // e.g. localhost:5173
    const url = `${protocol}//${host}/ws/story/${this.storyId}`;

    console.log("Connecting WS:", url);
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log("WS Connected");
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (e) {
        console.error("WS Parse Error", e);
      }
    };

    this.ws.onclose = () => {
      console.log("WS Closed");
      this.ws = null;
      this.attemptReconnect();
    };

    this.ws.onerror = (err) => {
      console.error("WS Error", err);
    };
  }

  private handleMessage(data: any) {
    // Backend pushes a single Turn object
    const store = useStoryStore();
    // Verify if it's a valid turn (has author, text)
    if (data && data.text) {
      // Append directly to store state? 
      // Or use a store action? 
      // Store action is safer for reactivity
      // But store.appendTurn calls API. We just want to PUSH to local state.
      // We need a store action specifically for "receiveTurn"
      // Let's assume we can push to turns array if we had access, 
      // but better to expose a method in store or just push here if we access state.
      // Ideally, store should handle it.
      // Since I can't easily modify store in this file without refetching it...
      // store.turns.push(data) is reactive.
      
      store.turns.push(data as Turn);
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Reconnecting... (${this.reconnectAttempts})`);
        this.connect();
      }, 2000 * this.reconnectAttempts);
    }
  }

  public send(payload: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    } else {
      console.warn("WS not open, cannot send");
    }
  }

  public disconnect() {
    if (this.ws) {
      this.ws.onclose = null; // Prevent reconnect
      this.ws.close();
      this.ws = null;
    }
  }
}
