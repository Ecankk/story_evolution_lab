<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{
  modelValue: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void;
}>();

// Mock seeds (In real app, fetch from backend or efficient local dictionary)
const seedsPool = [
  "量子", "红酒", "匕首", "月光", "时钟", "猫", "谎言", 
  "废墟", "密码", "雨声", "镜子", "香水", "指纹", "日记"
];

// Randomly pick 5 seeds
const activeSeeds = ref<string[]>([]);
refreshSeeds();

function refreshSeeds() {
  const shuffled = [...seedsPool].sort(() => 0.5 - Math.random());
  activeSeeds.value = shuffled.slice(0, 5);
}

function selectSeed(s: string) {
  emit('update:modelValue', s);
}
</script>

<template>
  <div class="flex flex-wrap gap-2 items-center">
    <div class="text-[10px] text-slate-500 uppercase tracking-widest mr-2">Inspiration:</div>
    <button
      v-for="seed in activeSeeds"
      :key="seed"
      @click="selectSeed(seed)"
      class="px-3 py-1 rounded-full text-xs border transition-all"
      :class="[
        modelValue === seed
          ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50 shadow-[0_0_10px_rgba(34,211,238,0.2)]'
          : 'bg-white/5 text-slate-400 border-white/5 hover:bg-white/10 hover:border-white/20 hover:text-slate-200'
      ]"
    >
      {{ seed }}
    </button>
    
    <button 
      @click="refreshSeeds" 
      class="w-6 h-6 rounded-full flex items-center justify-center text-slate-500 hover:text-cyan-400 transition-colors hover:bg-white/5"
      title="Shuffle"
    >
      ↻
    </button>
  </div>
</template>
