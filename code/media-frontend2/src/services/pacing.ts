// src/services/pacing.ts
import type { Turn } from "@/types";

export interface PacingStats {
  short: number; // < 20 chars
  medium: number; // 20-50 chars
  long: number; // > 50 chars
  avgLength: number;
}

export const pacingService = {
  analyze(turns: Turn[]): PacingStats {
    let totalLen = 0;
    const stats = { short: 0, medium: 0, long: 0, avgLength: 0 };
    
    if (!turns.length) return stats;

    for (const t of turns) {
      if (!t.text) continue;
      const len = t.text.length;
      totalLen += len;
      
      if (len < 20) stats.short++;
      else if (len <= 50) stats.medium++;
      else stats.long++;
    }
    
    stats.avgLength = Math.round(totalLen / turns.length);
    return stats;
  }
};
