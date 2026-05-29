<script setup lang="ts">
import type { TurnOption } from '@/types';

defineProps<{
  options: TurnOption[];
  isGenerating: boolean;
}>();

const emit = defineEmits<{
  (e: 'select', option: TurnOption): void;
  (e: 'cancel'): void;
}>();
</script>

<template>
  <div v-if="options.length || isGenerating" class="absolute bottom-0 left-0 right-0 glass-panel-heavy border-t border-cyan-500/20 p-6 z-20 shadow-[0_-10px_40px_rgba(0,0,0,0.5)] transition-all duration-300">
    <div class="max-w-4xl mx-auto">
      
      <!-- Header -->
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-sm font-bold text-cyan-200 uppercase tracking-widest flex items-center gap-2">
          <span v-if="isGenerating" class="animate-spin text-cyan-400">🌀</span>
          <span v-else class="text-amber-300">✨</span>
          {{ isGenerating ? 'AI is dreaming...' : 'Choose a Path' }}
        </h3>
        <button @click="emit('cancel')" class="text-slate-500 hover:text-cyan-300 transition-colors text-sm font-mono">[ CANCEL ]</button>
      </div>

      <!-- Loading State -->
      <div v-if="isGenerating" class="flex gap-4">
         <div v-for="i in 3" :key="i" class="flex-1 h-40 bg-white/5 rounded-lg animate-pulse border border-white/10"></div>
      </div>

      <!-- Options -->
      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div 
          v-for="opt in options" 
          :key="opt.id"
          @click="emit('select', opt)"
          class="group relative glass-card rounded-xl p-4 cursor-pointer hover:border-cyan-500/50 hover:bg-cyan-900/10 hover:shadow-[0_0_20px_rgba(6,182,212,0.1)] hover:-translate-y-1 transition-all"
        >
          <!-- Tags -->
          <div class="flex flex-wrap gap-1 mb-2">
             <span v-for="tag in opt.tags" :key="tag" class="text-[9px] uppercase font-bold text-cyan-700 bg-cyan-950/50 border border-cyan-800/30 px-1.5 py-0.5 rounded group-hover:text-cyan-300 group-hover:border-cyan-500/30">
                {{ tag }}
             </span>
          </div>
          
          <!-- Title -->
          <h4 class="font-bold text-slate-200 mb-1 group-hover:text-cyan-300 transition-colors">{{ opt.title }}</h4>
          
          <!-- Preview -->
          <p class="text-xs text-slate-400 leading-relaxed line-clamp-4 group-hover:text-slate-300">{{ opt.preview }}</p>
          
          <!-- Select Btn -->
          <div class="mt-4 text-center opacity-0 group-hover:opacity-100 transition-opacity">
             <span class="text-xs font-bold text-cyan-950 bg-cyan-400 px-3 py-1 rounded-full shadow-[0_0_10px_rgba(34,211,238,0.4)]">Select Path</span>
          </div>
        </div>
      </div>
      
    </div>
  </div>
</template>

<style scoped>
.glass-panel-heavy {
    background: rgba(15, 23, 42, 0.85); /* Darker for modal */
    backdrop-filter: blur(20px);
}

.glass-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
}
</style>
