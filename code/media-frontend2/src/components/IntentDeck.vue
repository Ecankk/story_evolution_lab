<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  modelValue: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', val: string): void;
}>();

const intents = [
  { id: 'advance', label: '🔴 推进剧情', desc: '加快节奏，推动情节发展' },
  { id: 'deepen',  label: '🔵 深化细节', desc: '丰富描写，增加沉浸感' },
  { id: 'setup',   label: '🟢 铺垫伏笔', desc: '埋下悬念，为未来做准备' },
  { id: 'twist',   label: '🟡 制造转折', desc: '出人意料，改变走向' },
];
</script>

<template>
  <div class="flex gap-2">
    <button
      v-for="item in intents"
      :key="item.id"
      @click="emit('update:modelValue', item.id)"
      class="px-3 py-2 rounded-lg border text-xs font-medium transition-all text-center min-w-[80px]"
      :class="[
        modelValue === item.id 
          ? 'bg-indigo-600/20 border-indigo-500/50 text-indigo-300 shadow-[0_0_15px_rgba(99,102,241,0.2)]' 
          : 'bg-white/5 border-white/5 text-slate-400 hover:bg-white/10 hover:border-white/20'
      ]"
      :title="item.desc"
    >
      <span>{{ item.label }}</span>
    </button>
  </div>
</template>
