<script setup lang="ts">
import { ref } from 'vue';

const start = ref("");
const end = ref("");

const emit = defineEmits<{
  (e: 'start', start: string, end: string): void
}>();

function onStart() {
    // Debug Auto-fill
    if (!start.value.trim() && !end.value.trim()) {
        start.value = "一个人半夜醒来打了自己一巴掌";
        end.value = "闻着烧焦的味道睡去了";
    }

    if (start.value && end.value) {
        emit('start', start.value, end.value);
    }
}
</script>

<template>
  <div class="glass-panel p-8 rounded-2xl shadow-[0_0_40px_rgba(0,0,0,0.5)] max-w-md w-full border border-white/10 backdrop-blur-xl">
      <h2 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 to-cyan-300 mb-6 flex items-center gap-2">
          <span>🧩</span> 海龟汤：空间侦探
      </h2>
      
      <div class="space-y-5">
          <div>
              <label class="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">汤面 (Start)</label>
              <textarea 
                  v-model="start" 
                  class="w-full bg-black/20 border border-white/10 rounded-lg p-3 h-24 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500/50 focus:bg-black/40 transition-all font-serif resize-none" 
                  placeholder="e.g. 一个人半夜醒来打了自己一巴掌..."
              ></textarea>
          </div>
          
          <div>
              <label class="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">汤底 (End)</label>
              <textarea 
                  v-model="end" 
                  class="w-full bg-black/20 border border-white/10 rounded-lg p-3 h-24 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50 focus:bg-black/40 transition-all font-serif resize-none" 
                  placeholder="e.g. 闻着烧焦的味道睡去了..."
              ></textarea>
          </div>
          
          <button 
            @click="onStart"
            class="w-full bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-bold py-3 rounded-xl hover:shadow-lg hover:shadow-indigo-500/30 transition-all hover:-translate-y-0.5"
          >
              开始推理 (Start Game)
          </button>
      </div>
  </div>
</template>

<style scoped>
.glass-panel {
    background: rgba(30, 41, 59, 0.4); 
}
</style>
