<script setup lang="ts">
import { computed } from 'vue';
import type { Turn } from '@/types';

const props = defineProps<{
  turns: Turn[];
}>();

const stats = computed(() => {
    let totalLen = 0;
    let dialogueLen = 0;
    
    props.turns.forEach(t => {
        const text = t.text || "";
        totalLen += text.length;
        
        // Match content inside quotes: “...” or "..."
        const matches = text.match(/“[^”]+”|"[^"]+"/g);
        if (matches) {
            matches.forEach(m => dialogueLen += m.length);
        }
    });
    
    const ratio = totalLen > 0 ? (dialogueLen / totalLen) : 0;
    return {
        ratio: Math.round(ratio * 100),
        narrative: 100 - Math.round(ratio * 100)
    };
});
</script>

<template>
  <div class="glass-card rounded-2xl p-4 flex flex-col justify-center">
        <div class="font-bold text-slate-400 text-[10px] uppercase mb-2 text-center tracking-widest">对话含量 (Dialogue Ratio)</div>
      
      <div class="flex h-3 rounded-full overflow-hidden bg-white/10 mb-3 relative">
          <!-- Dialogue Bar -->
          <div 
             class="h-full bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.5)] z-10 transition-all duration-700 ease-out" 
             :style="{ width: `${stats.ratio}%` }"
          ></div>
          <!-- Narrative Bar (Background is transparent/white, effectively "empty" but we label it) -->
      </div>
      
      <div class="flex justify-between text-[10px] font-mono">
          <span class="flex items-center gap-1 text-indigo-300">
              <span class="w-1.5 h-1.5 rounded-full bg-indigo-500 shadow-[0_0_5px_rgba(99,102,241,0.8)]"></span>
              Dial {{ stats.ratio }}%
          </span>
          <span class="flex items-center gap-1 text-slate-500">
              <span class="w-1.5 h-1.5 rounded-full bg-white/20"></span>
              Narr {{ stats.narrative }}%
          </span>
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
