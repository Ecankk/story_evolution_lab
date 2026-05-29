// src/services/llm.ts
import axios from "axios";
import type { TurnOption } from "@/types";

export interface SuggestRequest {
  story_id: string;
  context_text: string;
  intent: string;
  seed: string;
}

export interface SuggestResponse {
  options: TurnOption[];
}

export interface ApiSettings {
    provider: 'deepseek' | 'gemini';
    apiKey: string;
    baseUrl?: string;
    model?: string;
}

const SETTINGS_KEY = 'media_lab_api_settings';

export const llmService = {
  getSettings(): ApiSettings {
      try {
          const raw = localStorage.getItem(SETTINGS_KEY);
          if (raw) return JSON.parse(raw);
      } catch (e) {
          console.error("Failed to load settings", e);
      }
      return { provider: 'deepseek', apiKey: '' }; // Default
  },

  saveSettings(settings: ApiSettings) {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  },

  /**
   * Stateless generation of 3 plot options
   */
  async suggest(req: SuggestRequest): Promise<TurnOption[]> {
    try {
      const resp = await axios.post<SuggestResponse>("/api/story/suggest", req);
      return resp.data.options;
    } catch (e: any) {
      console.error("LLM Suggest Error:", e);
      return [];
    }
  },

  /**
   * Deep scan for plot holes (Reasoning Model)
   */
  async scan(text: string): Promise<any> {
    // Placeholder for Phase 4
    console.warn("Scan not implemented yet");
    return { issues: [] };
  },

  async detectiveTurn(start: string, end: string, history: any[]) {
      const config = this.getSettings();
      // Only send config if apiKey is present, otherwise let backend use env
      const payloadConfig = config.apiKey ? {
          api_key: config.apiKey,
          provider: config.provider,
          base_url: config.baseUrl,
          model: config.model
      } : {};
      
      const res = await axios.post("/api/game/detective", { start, end, history, config: payloadConfig }, { timeout: 60000 });
      return res.data.result;
  },
  
  async revealTruth(start: string, end: string, history: any[]) {
      const config = this.getSettings();
      const payloadConfig = config.apiKey ? {
          api_key: config.apiKey,
          provider: config.provider,
          base_url: config.baseUrl,
          model: config.model
      } : {};
      
      const res = await axios.post("/api/game/reveal", { start, end, history, config: payloadConfig }, { timeout: 60000 });
      return res.data.result;
  }
};
