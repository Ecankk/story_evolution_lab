<script setup lang="ts">
import { computed } from 'vue';
import type { Turn } from '@/types';

const props = defineProps<{
  turns: Turn[];
}>();

// Calculate Average Style Metrics over the last 5 turns (for immediate feedback)
const recentTurns = computed(() => props.turns.slice(-5));

const avgShowRatio = computed(() => {
    if (!recentTurns.value.length) return 0;
    const sum = recentTurns.value.reduce((acc, t) => acc + (t.show_ratio || 0), 0);
    return sum / recentTurns.value.length;
});

const avgSensory = computed(() => {
    if (!recentTurns.value.length) return 0;
    const sum = recentTurns.value.reduce((acc, t) => acc + (t.sensory_score || 0), 0);
    return sum / recentTurns.value.length;
});

const adjWarning = computed(() => {
    const last = props.turns[props.turns.length - 1];
    if (!last) return false;
    return (last.adj_density || 0) > 0.15;
});

// Normalized Score for UI (Show Ratio 0-5 -> 0-100%)
const showPercent = computed(() => Math.min(100, (avgShowRatio.value / 3.0) * 100));
</script>

<template>
  <div class="glass-card rounded-2xl p-4">
      <div class="flex justify-between items-center mb-3">
          <h4 class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Style Analysis</h4>
          <!-- Adjective Warning -->
          <div v-if="adjWarning" class="text-[9px] text-amber-400 bg-amber-900/40 px-2 py-0.5 rounded border border-amber-500/30 flex items-center gap-1">
              <span>⚠️</span>
              <span>Adj Overload</span>
          </div>
      </div>

      <!-- Show Don't Tell Bar -->
      <div class="mb-5">
          <div class="flex justify-between text-[10px] mb-1 uppercase tracking-wider text-slate-500 font-bold">
              <span>画面感 (Show Ratio)</span>
              <span class="font-mono" :class="{'text-red-400': avgShowRatio < 1.0, 'text-cyan-400': avgShowRatio >= 2.0}">{{ avgShowRatio.toFixed(1) }}</span>
          </div>
          <div class="h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div 
                class="h-full bg-gradient-to-r from-cyan-600 to-cyan-400 transition-all duration-700 ease-out shadow-[0_0_10px_rgba(34,211,238,0.5)]"
                :style="{ width: `${showPercent}%` }"
              ></div>
          </div>
          <p class="text-[9px] text-slate-600 mt-1 text-right">Target: > 2.0</p>
      </div>

      <!-- Sensory Heatmap (Mini) -->
      <div>
          <div class="flex justify-between text-[10px] mb-1 uppercase tracking-wider text-slate-500 font-bold">
              <span>感官密度 (Sensory)</span>
              <span class="font-mono text-amber-400">{{ avgSensory.toFixed(1) }}</span>
          </div>
          <div class="flex gap-1 h-3">
             <!-- Visualize as 5 blocks, lighting up based on score strength -->
             <div 
                v-for="i in 5" :key="i"
                class="flex-1 rounded-sm transition-all duration-300 border border-white/5"
                :class="avgSensory * 10 >= i * 2 ? 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.6)]' : 'bg-white/5'"
             ></div>
          </div>
          <div class="flex justify-between text-[9px] text-slate-600 mt-1 uppercase">
              <span>Bland</span>
              <span>Vivid</span>
          </div>
      </div>
  </div>
</template>

<style scoped>
.glass-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
}
</style>
