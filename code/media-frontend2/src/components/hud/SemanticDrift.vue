<script setup lang="ts">
import { computed } from 'vue';
import type { Turn } from '@/types';

const props = defineProps<{
  lastTurn: Turn | null;
}>();

const drift = computed(() => {
    if (!props.lastTurn) return 0;
    return Math.round((props.lastTurn.semantic_drift || 0) * 100);
});

// Color logic
const colorClass = computed(() => {
    if (drift.value < 30) return 'text-emerald-400'; 
    if (drift.value < 70) return 'text-amber-400'; 
    return 'text-rose-500'; 
});

const colorHex = computed(() => {
    if (drift.value < 30) return '#34d399'; // Emerald-400
    if (drift.value < 70) return '#fbbf24'; // Amber-400
    return '#f43f5e'; // Rose-500
});
</script>

<template>
  <div class="glass-card rounded-2xl p-4 flex flex-col items-center justify-center relative overflow-hidden">
        <div class="font-bold text-slate-400 text-[10px] uppercase mb-2 text-center tracking-widest">语义漂移 (Semantic Drift)</div>
      
       <!-- Circular Progress as SVG -->
      <div class="relative w-24 h-24">
         <svg class="w-full h-full transform -rotate-90">
             <!-- Background Circle -->
             <circle 
                cx="48" cy="48" r="40" 
                stroke="rgba(255,255,255,0.1)" 
                stroke-width="8" 
                fill="none" 
             />
             <!-- Drift Value Circle -->
             <circle 
                cx="48" cy="48" r="40" 
                :stroke="colorHex"
                stroke-width="8" 
                fill="none" 
                stroke-dasharray="251.2" 
                :stroke-dashoffset="251.2 - (251.2 * drift / 100)"
                stroke-linecap="round"
                class="transition-all duration-1000 ease-out"
             />
         </svg>
         
         <!-- Centered Value -->
         <div class="absolute inset-0 flex flex-col items-center justify-center">
             <span class="text-xl font-black font-mono" :class="colorClass">{{ drift }}%</span>
         </div>
      </div>
      
      <div class="text-[9px] text-slate-500 mt-2 text-center uppercase">Distance from Origin</div>
  </div>
</template>

<style scoped>
.glass-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
}
</style>
