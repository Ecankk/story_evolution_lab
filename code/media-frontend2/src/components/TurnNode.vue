<script setup lang="ts">
import { computed } from 'vue';
import type { Turn } from '@/types';

const props = defineProps<{
  turn: Turn;
  index: number;
}>();

const isAi = computed(() => props.turn.author === 'ai');
const hasSnapshot = computed(() => !!props.turn.snapshot);

const emit = defineEmits<{
  (e: 'branch', turnIndex: number): void;
  (e: 'restore', turnIndex: number): void; // Added for completeness, though currently unused in logic
}>();
</script>

<template>
  <div 
    :id="`turn-node-${index}`"
    class="w-full relative group transition-colors duration-500"
    :class="[
      isAi 
        ? 'bg-gradient-to-r from-slate-900/60 to-slate-900/40 hover:bg-slate-900/70' 
        : 'bg-indigo-900/10 hover:bg-indigo-900/20'
    ]"
  >
    <!-- Content Wrapper -->
    <!-- Zero vertical margin, padding matches paragraph spacing -->
    <div class="max-w-3xl mx-auto py-4 px-8 relative border-l-2 transition-all duration-300"
         :class="isAi ? 'border-cyan-500/30' : 'border-amber-500/30'">
        
        <!-- Hover-only Meta (Gutter) -->
        <div class="absolute -left-12 top-4 opacity-0 group-hover:opacity-60 transition-opacity text-[9px] font-mono text-right w-8 select-none">
            <span v-if="isAi" class="text-cyan-400">AI</span>
            <span v-else class="text-amber-400">HUMAN</span>
        </div>

        <!-- Content -->
        <div 
            class="prose prose-base max-w-none prose-invert leading-7 font-serif text-slate-200 whitespace-pre-wrap selection:bg-cyan-500/30 selection:text-cyan-50"
            :class="!isAi ? 'text-amber-50/90' : ''"
        >
            {{ turn.text }}
        </div>
        
        <!-- Actions (Floating, minimal) -->
        <div class="absolute -right-12 top-4 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col gap-1">
            <button 
              v-if="hasSnapshot"
              @click="emit('branch', index + 1)" 
              class="p-1 text-cyan-500/50 hover:text-cyan-300 transition-colors"
              title="Branch"
            >
              <span class="text-xs">🔀</span>
            </button>
            <button
               @click="emit('restore', index)"
               class="p-1 text-slate-600 hover:text-slate-400 transition"
               title="Rewind"
            >
               ⏪
            </button>
        </div>
    </div>
    
  </div>
</template>

<style scoped>
/* No specific styles needed, using Tailwind */
</style>
