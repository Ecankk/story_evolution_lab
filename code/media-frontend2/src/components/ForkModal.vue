<script setup lang="ts">
import { computed } from 'vue';
import type { Turn, Snapshot, TurnOption } from '@/types';

const props = defineProps<{
  turn: Turn;
  index: number;
}>();

const emit = defineEmits<{
  (e: 'branch', option: TurnOption): void;
  (e: 'close'): void;
}>();

const snapshot = computed(() => props.turn.snapshot as Snapshot);
const rejectedOptions = computed(() => {
    if (!snapshot.value) return [];
    return snapshot.value.choices.filter(o => o.id !== snapshot.value.selected);
});
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="emit('close')">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden animate-in zoom-in-95 duration-200">
      
      <!-- Header -->
      <div class="bg-purple-600 px-6 py-4 text-white flex justify-between items-center">
        <div>
           <h3 class="font-bold text-lg">Time Travel Protocol</h3>
           <p class="text-purple-200 text-xs">Return to Turn #{{ index + 1 }} · {{ snapshot?.intent }} / {{ snapshot?.seed }}</p>
        </div>
        <button @click="emit('close')" class="text-purple-200 hover:text-white text-2xl">×</button>
      </div>

      <!-- Content -->
      <div class="p-6">
        <p class="text-slate-500 text-sm mb-4">
           You are viewing a <strong>Snapshot</strong> of history. 
           The current timeline committed to: <span class="font-bold text-slate-700">"{{ snapshot?.choices.find(c => c.id === snapshot.selected)?.title }}"</span>.
           <br/>
           Select an alternative path below to <strong class="text-purple-600">Branch</strong> a new reality.
        </p>

        <div class="grid grid-cols-2 gap-4">
           <!-- Alternatives -->
           <div 
             v-for="opt in rejectedOptions" 
             :key="opt.id"
             @click="emit('branch', opt)"
             class="border border-slate-200 rounded-lg p-4 hover:border-purple-500 hover:bg-purple-50 cursor-pointer transition-all group"
           >
              <h4 class="font-bold text-slate-700 group-hover:text-purple-700 mb-1">{{ opt.title }}</h4>
              <p class="text-xs text-slate-500 line-clamp-3 mb-2">{{ opt.preview }}</p>
              <div class="flex gap-1">
                 <span v-for="tag in opt.tags" :key="tag" class="text-[10px] bg-white border px-1 rounded text-slate-400">
                    {{ tag }}
                 </span>
              </div>
           </div>
           
           <div v-if="rejectedOptions.length === 0" class="col-span-2 text-center text-slate-400 py-8 italic border border-dashed rounded-lg">
              No alternative paths recorded for this moment.
           </div>
        </div>
      </div>
      
      <!-- Footer -->
      <div class="bg-slate-50 px-6 py-3 border-t text-right">
         <button @click="emit('close')" class="text-slate-500 hover:text-slate-700 text-sm font-medium">Cancel</button>
      </div>
      
    </div>
  </div>
</template>
