<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();

const features = [
  {
    icon: '🔮',
    title: 'AI 协同共创',
    desc: '与高智能 AI 模型实时协作，无论是续写情节还是生成伏笔，它都是你最得力的助手。'
  },
  {
    icon: '🌌',
    title: '多维宇宙',
    desc: '探索无限的可能性。在一个界面中管理多个剧情分支，像观察平行宇宙一样审视故事走向。'
  },
  {
    icon: '📊',
    title: '全知视角',
    desc: '通过张力曲线、语义漂移等可视化指标，实时监控故事的节奏与质量，掌控全局。'
  }
];

const metrics = [
  { label: 'Tension', value: '张力', color: 'text-amber-400', desc: '监控情节的紧凑度与冲突强度' },
  { label: 'Drift', value: '漂移', color: 'text-emerald-400', desc: '追踪剧情与原始设定的偏离程度' },
  { label: 'Entropy', value: '熵值', color: 'text-rose-400', desc: '分析文本的不可预测性与复杂度' },
];
</script>

<template>
  <div class="min-h-screen w-full flex flex-col items-center pt-20 pb-10 px-4 md:px-0 scroll-smooth">
    
    <!-- Hero Section -->
    <section class="max-w-5xl mx-auto w-full text-center relative mb-32 shrink-0">
        <!-- Decoration -->
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-500/20 rounded-full blur-[100px] pointer-events-none animate-pulse"></div>

        <h1 class="text-6xl md:text-8xl font-black mb-6 relative z-10 tracking-tighter">
            <span class="bg-clip-text text-transparent bg-gradient-to-r from-cyan-200 via-indigo-200 to-amber-200 filter drop-shadow-[0_0_20px_rgba(99,102,241,0.5)]">
                Multiverse
            </span>
            <br>
            <span class="text-4xl md:text-5xl font-light text-slate-300 tracking-widest uppercase mt-2 block">
                Workbench
            </span>
        </h1>
        
        <p class="text-xl text-slate-400 max-w-2xl mx-auto mb-12 relative z-10 leading-relaxed">
            专为创作者打造的智能叙事工作台。<br>
            在 <span class="text-cyan-300">AI</span> 的协助下，编织无限可能的平行故事线。
        </p>
        
        <div class="flex justify-center gap-6 relative z-10">
            <button 
                @click="router.push('/workbench')"
                class="group relative px-8 py-4 rounded-full bg-slate-100 text-slate-900 font-bold text-lg hover:shadow-[0_0_40px_rgba(255,255,255,0.3)] transition-all hover:-translate-y-1 overflow-hidden"
            >
                <span class="relative z-10 flex items-center gap-2">
                    Start Writing <span class="group-hover:translate-x-1 transition-transform">→</span>
                </span>
            </button>
            <button 
                @click="router.push('/game')"
                class="px-8 py-4 rounded-full glass-btn text-slate-200 font-bold text-lg hover:bg-white/10 hover:text-white transition-all flex items-center gap-2"
            >
                <span>🐢</span> Play Turtle Soup
            </button>
            <button 
                @click="router.push('/multiverse')"
                class="px-8 py-4 rounded-full glass-btn text-violet-300 font-bold text-lg hover:bg-white/10 hover:text-white transition-all flex items-center gap-2"
            >
                <span>🪐</span> Explore Multiverse
            </button>
        </div>
    </section>

    <!-- Features Grid -->
    <section class="max-w-6xl mx-auto w-full grid md:grid-cols-3 gap-8 mb-32 relative z-10 shrink-0">
        <div 
            v-for="feat in features" 
            :key="feat.title"
            class="glass-card p-8 rounded-2xl border border-white/5 hover:border-white/20 transition-all hover:-translate-y-2 hover:shadow-[0_0_30px_rgba(99,102,241,0.15)]"
        >
            <div class="text-4xl mb-6">{{ feat.icon }}</div>
            <h3 class="text-2xl font-bold text-slate-200 mb-4">{{ feat.title }}</h3>
            <p class="text-slate-400 leading-relaxed">{{ feat.desc }}</p>
        </div>
    </section>

    <!-- Metrics Showcase -->
    <section class="max-w-5xl mx-auto w-full glass-panel p-10 md:p-16 rounded-3xl relative overflow-hidden mb-20 border border-white/10 shrink-0">
        <div class="absolute -right-20 -top-20 w-96 h-96 bg-cyan-500/10 rounded-full blur-[80px]"></div>
        
        <div class="grid md:grid-cols-2 gap-12 items-center relative z-10">
            <div>
                <h2 class="text-3xl font-bold text-slate-200 mb-6">不仅是写作，更是<span class="text-transparent bg-clip-text bg-gradient-to-r from-amber-300 to-rose-300">掌控全局</span></h2>
                <p class="text-slate-400 mb-8 text-lg">
                    Multiverse 内置了先进的自然语言处理算法，实时分析你的故事结构。从情绪张力到逻辑一致性，让创作不再是盲人摸象。
                </p>
                <button 
                    @click="router.push('/guide')"
                    class="text-cyan-400 font-bold hover:text-cyan-300 flex items-center gap-2 border-b border-transparent hover:border-cyan-300 pb-1 w-fit transition-all"
                >
                    了解详细指标体系 &rarr;
                </button>
            </div>
            
            <div class="grid gap-4">
                <div v-for="m in metrics" :key="m.label" class="bg-black/20 p-4 rounded-xl border border-white/5 flex items-center gap-4">
                    <div class="font-mono font-bold text-2xl w-12 text-right opacity-50">{{ m.label[0] }}</div>
                    <div>
                        <div class="font-bold text-lg" :class="m.color">{{ m.label }} ({{ m.value }})</div>
                        <div class="text-xs text-slate-500">{{ m.desc }}</div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="text-center text-slate-600 pb-8 text-sm relative z-10 w-full shrink-0">
        <p>&copy; 2024 Multiverse Workbench. Powered by Google Gemini & Deep Space Tech.</p>
    </footer>

  </div>
</template>

<style scoped>
.glass-panel {
    background: rgba(15, 23, 42, 0.4);
    backdrop-filter: blur(16px);
}
.glass-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(10px);
}
.glass-btn {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
</style>
