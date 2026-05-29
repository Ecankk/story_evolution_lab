<script setup lang="ts">
import { onMounted, onUnmounted, ref, nextTick, computed } from 'vue';
import { useStoryStore } from '@/stores/storyStore';
import { SocketService } from '@/services/socket';
import { llmService } from '@/services/llm';
import type { TurnOption, Turn } from '@/types';
import TurnNode from '@/components/TurnNode.vue';
import IntentDeck from '@/components/IntentDeck.vue';
import SeedBubbles from '@/components/SeedBubbles.vue';
import PlotSelector from '@/components/PlotSelector.vue';
import ForkModal from '@/components/ForkModal.vue';
import StoryStructure from '@/components/StoryStructure.vue';
import TensionChart from '@/components/hud/TensionChart.vue';
import SemanticDrift from '@/components/hud/SemanticDrift.vue';
import DialogueRatio from '@/components/hud/DialogueRatio.vue';
import CharacterGraph from '@/components/hud/CharacterGraph.vue';
import StyleMonitor from '@/components/hud/StyleMonitor.vue';
import { useRoute, useRouter } from 'vue-router';
// Animation
import gsap from 'gsap';

// State
const store = useStoryStore();
const route = useRoute();
const router = useRouter();
let socket: SocketService | null = null;
const bottomRef = ref<HTMLElement | null>(null);

// UI State
const showHud = ref(true);

// Console State
const userText = ref("");
const selectedIntent = ref("advance");
const selectedSeed = ref("量子");

// AI State
const isGenerating = ref(false);
const suggestionOptions = ref<TurnOption[]>([]);
const showSelector = ref(false);

// Time Travel State
const showForkModal = ref(false);
const forkTargetTurn = ref<Turn | null>(null);
const forkTargetIndex = ref(-1);

// Metrics Computing
const pacingStats = computed(() => {
    const turns = store.turns;
    if (!turns.length) return { avgLen: 0, short: 0, long: 0 };
    
    const lens = turns.map(t => t.text.length);
    const avg = Math.round(lens.reduce((a, b) => a + b, 0) / lens.length);
    
    // Thresholds: Short < 20, Long > 100 (arbitrary for typical chat, adjust for novel)
    const shortCount = lens.filter(l => l < 50).length;
    const longCount = lens.filter(l => l > 200).length;
    
    return {
        avgLen: avg,
        short: Math.round((shortCount / turns.length) * 100),
        long: Math.round((longCount / turns.length) * 100)
    };
});

// Lifecycle
onMounted(async () => {
    // 1. Load Story
    let sid = route.params.id as string;
    if (!sid && store.currentStoryId) sid = store.currentStoryId;
    
    if (sid) {
        await store.fetchStory(sid);
    } else {
        await store.createStory();
    }
    
    // 2. Connect WebSocket
    if (store.currentStoryId) {
        socket = new SocketService(store.currentStoryId);
        socket.connect();
    }
    
    scrollToBottom();
});

onUnmounted(() => {
    socket?.disconnect();
});

// GSAP Animations
const onEnter = (el: Element, done: () => void) => {
    gsap.from(el, {
        opacity: 0,
        y: 20,
        scale: 0.95,
        duration: 0.6,
        ease: "back.out(1.2)",
        onComplete: done
    });
};

function scrollToBottom() {
    nextTick(() => {
        if (bottomRef.value) {
            gsap.to(bottomRef.value, {
                scrollTop: bottomRef.value.scrollHeight,
                duration: 0.8,
                ease: "power2.out"
            });
        }
    });
}

// Helper to check if current story is a leaf (has no children)
const isLeaf = computed(() => {
    if (!store.currentStoryId || !store.treeData.links) return true;
    // If current ID is a 'source' in any link, it has children -> not a leaf
    return !store.treeData.links.some((l: any) => l.source === store.currentStoryId || l.source.id === store.currentStoryId);
});

// Actions
async function handleManualInput() {
    if (!userText.value.trim()) return;
    
    // Strict Branching: If not a leaf, we MUST fork first
    if (!isLeaf.value) {
        try {
            // Fork at the END of the current story (length)
            const newSid = await store.forkStory(store.turns.length);
            if (newSid) {
                // Append to NEW story
                await store.appendTurn({ 
                    text: userText.value, 
                    author: 'human' 
                });
                
                // await store.fetchAllStories(); // Update Tree (Handled by Watcher in StoryStructure)
                
                // Switch Socket
                socket?.disconnect();
                socket = new SocketService(newSid);
                socket.connect();
                
                userText.value = "";
                scrollToBottom();
            }
        } catch(e) {
            console.error("Auto-fork for manual input failed", e);
            alert("Failed to branch history");
        }
        return;
    }

    // Normal Append (Leaf Node)
    try {
        await store.appendTurn({ 
            text: userText.value, 
            author: 'human' 
        });
        userText.value = "";
        scrollToBottom();
    } catch (e) {
        alert("Failed to send");
    }
}

async function handleAiSuggest() {
    isGenerating.value = true;
    showSelector.value = true;
    suggestionOptions.value = [];
    
    try {
        const lastText = store.lastTurn ? store.lastTurn.text : "";
        const opts = await llmService.suggest({
            story_id: store.currentStoryId,
            context_text: lastText, // simplified context
            intent: selectedIntent.value,
            seed: selectedSeed.value
        });
        suggestionOptions.value = opts;
    } catch (e) {
        console.error(e);
        showSelector.value = false;
    } finally {
        isGenerating.value = false;
    }
}

async function handleSnapshotSelect(opt: TurnOption) {
    // ALWAYS Fork for AI? Or only if configured? 
    // User requirement: "Each AI continuation results in a new branch"
    // Current Implementation: Always fork.
    
    // If store.turns is empty, just create new.
    if (store.turns.length === 0) {
        await store.appendTurn({
             text: opt.full_text || opt.preview,
             author: 'ai',
             snapshot: {
                intent: selectedIntent.value,
                seed: selectedSeed.value,
                choices: suggestionOptions.value,
                selected: opt.id
             }
        });
        showSelector.value = false;
        scrollToBottom();
        return;
    }

    try {
        const newSid = await store.forkStory(store.turns.length);
        
        if (newSid) {
            // Append to NEW story
            await store.appendTurn({
                text: opt.full_text || opt.preview,
                author: 'ai',
                snapshot: {
                     intent: selectedIntent.value,
                     seed: selectedSeed.value,
                     choices: suggestionOptions.value,
                     selected: opt.id
                }
            });
            
            // await store.fetchAllStories(); // Update Tree (Handled by Watcher in StoryStructure)
            
            // Reconnect socket for new story
            socket?.disconnect();
            socket = new SocketService(newSid);
            socket.connect();
        }
    } catch (e) {
        console.error("Auto-fork failed", e);
    }
    
    showSelector.value = false;
    scrollToBottom();
}

function handleBranch(turnIndex: number) {
    // Branch from a specific point (Fork Modal)
    const idx = turnIndex; 
    forkTargetTurn.value = store.turns[idx];
    forkTargetIndex.value = idx;
    showForkModal.value = true;
}

// Rewind / Restore Handler
function handleRestore(index: number) {
    // Treat "Restore" as "Branch from this point" (discarding future in the new branch)
    // This effectively creates a new timeline starting from 'index'
    console.log("Rewind requested at index", index);
    
    // We can reuse the Fork Modal logic, or just trigger it immediately?
    // Let's reuse Fork Modal to give context/confirmation if needed, 
    // OR just treat it as "I want to branch here"
    
    // Actually, "Rewind" usually implies we want to *continue* from that point.
    // So let's open the Fork Modal which allows "Continue" (Branch).
    handleBranch(index);
}

// onConfirmFork matches handleConfirmFork in template?
// Template says `@fork="handleConfirmFork"`
async function handleConfirmFork(option: TurnOption) {
    if (forkTargetIndex.value === -1) return;
    
    try {
        const newSid = await store.forkStory(forkTargetIndex.value);
        if (newSid) {
            const oldSnapshot = forkTargetTurn.value?.snapshot;
            const newSnapshot = oldSnapshot ? {
                ...oldSnapshot,
                selected: option.id
            } : undefined;

            await store.appendTurn({
                text: option.full_text || option.preview,
                author: 'ai',
                snapshot: newSnapshot
            });
            
            // await store.fetchAllStories(); // Update Tree (Handled by Watcher in StoryStructure)
            
            showForkModal.value = false;
            scrollToBottom();
            
            socket?.disconnect();
            socket = new SocketService(newSid);
            socket.connect();
        }
    } catch (e) {
        console.error(e);
        alert("Fork failed");
    }
}
</script>

<template>
  <div class="h-screen w-full flex flex-col overflow-hidden text-slate-200">
    <!-- Header -->
    <header class="h-14 glass-panel flex items-center px-6 justify-between shrink-0 z-30 relative">
      <!-- Left: Branding & Context -->
      <div class="flex items-center gap-3 w-1/3">
         <span class="text-2xl filter drop-shadow-[0_0_8px_rgba(246,211,101,0.5)]">🌌</span>
         <h1 class="font-bold text-lg tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-amber-200 to-cyan-200 hidden md:block">
            MULTIVERSE
         </h1>
         <span class="text-[10px] text-cyan-500/80 font-mono border border-cyan-900/50 px-1 rounded bg-cyan-950/30">
            {{ store.currentStoryId?.slice(0, 8) }}
         </span>
      </div>

      <!-- Center: Navigation (Spread out) -->
      <div class="flex items-center justify-center gap-6 w-1/3">
         <button 
            @click="router.push('/')"
            class="glass-btn px-4 py-1.5 text-xs rounded-full hover:bg-white/10 transition-all flex items-center gap-2 text-slate-300 group"
            title="Return to Main Menu"
         >
            <span class="group-hover:scale-110 transition-transform">🏠</span>
            <span class="tracking-wide">HOME</span>
         </button>
         <div class="h-4 w-px bg-white/10"></div>
         <button 
           @click="router.push('/multiverse')"
           class="glass-btn px-4 py-1.5 text-xs rounded-full hover:bg-white/10 transition-all flex items-center gap-2 text-violet-300 group"
           title="Multiverse Map"
         >
            <span class="group-hover:scale-110 transition-transform">🪐</span>
            <span class="tracking-wide">MAP</span>
         </button>
      </div>

      <!-- Right: Tools & Status -->
      <div class="flex items-center justify-end gap-3 w-1/3">
         <button 
           @click="showHud = !showHud" 
           class="glass-btn px-3 py-1 text-xs rounded-full hover:bg-white/10 transition-all flex items-center gap-2 text-cyan-300"
         >
            <span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            STATUS
         </button>
      </div>
    </header>

    <!-- Main Workspace -->
    <div class="flex-grow flex overflow-hidden relative justify-center gap-4">
        
        <!-- Left: Story Structure -->
        <StoryStructure />

        <!-- Center: Story Stream -->
        <main class="flex-1 flex flex-col relative max-w-4xl h-full">
            
            <!-- Scrollable Stream -->
            <!-- Adjusted padding to avoid covering the bottom input -->
            <div class="flex-1 overflow-y-auto px-4 md:px-8 scroll-smooth pb-48 pt-8">
                <!-- 3x3 Grid Container -->
                <div class="max-w-5xl mx-auto w-full grid grid-cols-1 md:grid-cols-3 gap-4">
                    <template v-if="store.turns.length">
                        <TurnNode 
                            v-for="(turn, idx) in store.turns" 
                            :key="`${turn.story_id}_${turn.turn}`"
                            :turn="turn"
                            :index="idx"
                            @branch="handleBranch"
                            @restore="handleRestore"
                            class="transition-all duration-500 ease-out"
                        />
                    </template>
                    <!-- Empty State for Grid -->
                    <div v-if="store.turns.length === 0" class="col-span-3 h-96 flex items-center justify-center">
                         <div class="text-center space-y-4">
                            <div class="text-6xl opacity-20 animate-pulse">💠</div>
                            <div class="text-slate-500 font-light tracking-widest text-sm uppercase">
                                Grid Empty<br>Initialize Sequence
                            </div>
                        </div>
                    </div>
                    <div ref="bottomRef" class="h-8 col-span-3"></div>
                </div>
            </div>
            
            <!-- Plot Selector Overlay (Glass Modal) -->
            <transition 
              enter-active-class="transform transition duration-500 cubic-bezier(0.34, 1.56, 0.64, 1)" 
              enter-from-class="translate-y-full opacity-0 scale-95" 
              enter-to-class="translate-y-0 opacity-100 scale-100"
              leave-active-class="transform transition duration-300 ease-in" 
              leave-from-class="translate-y-0 opacity-100 scale-100" 
              leave-to-class="translate-y-full opacity-0 scale-95"
            >
                <div v-if="showSelector" class="absolute inset-x-0 bottom-0 z-40 p-4 pb-0 flex justify-center">
                    <div class="w-full max-w-4xl">
                        <PlotSelector 
                            :options="suggestionOptions"
                            :is-generating="isGenerating"
                            @select="handleSnapshotSelect"
                            @cancel="showSelector = false"
                        />
                    </div>
                </div>
            </transition>

            <!-- Fork Modal -->
            <ForkModal 
                v-if="showForkModal && forkTargetTurn"
                :turn="forkTargetTurn"
                :index="forkTargetIndex"
                @branch="handleConfirmFork"
                @close="showForkModal = false"
            />

            <!-- Command Deck (Input Console) -->
            <div 
                class="absolute bottom-6 left-0 right-0 z-30 transition-all duration-500 flex justify-center px-4"
                :class="{ 'opacity-0 translate-y-10 pointer-events-none': showSelector }"
            >
                <div class="w-full max-w-3xl glass-panel-heavy rounded-2xl p-4 shadow-2xl border border-white/10 backdrop-blur-xl">
                    
                    <!-- AI Controls Row -->
                    <div class="flex items-center gap-3 mb-3">
                        <IntentDeck v-model="selectedIntent" />
                        
                        <div class="h-8 w-px bg-white/10"></div>
                        
                        <SeedBubbles v-model="selectedSeed" />

                        <div class="flex-grow"></div>
                        
                        <button 
                            @click="handleAiSuggest"
                            class="group relative px-6 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-bold shadow-lg hover:shadow-indigo-500/50 transition-all hover:-translate-y-0.5"
                            :disabled="isGenerating"
                        >
                            <span class="relative z-10 flex items-center gap-2">
                                <span class="text-lg">✨</span> 
                                <span v-if="isGenerating">TRANSMITTING...</span>
                                <span v-else>AI CONTINUE</span>
                            </span>
                            <!-- Glow effect -->
                            <div class="absolute inset-0 rounded-xl bg-white/20 blur opacity-0 group-hover:opacity-100 transition duration-500"></div>
                        </button>
                    </div>

                    <!-- Manual Input Row -->
                    <div class="relative">
                        <input 
                            v-model="userText"
                            @keydown.enter="handleManualInput"
                            class="w-full bg-black/20 border border-white/5 rounded-xl px-5 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500/30 focus:bg-black/40 transition-all font-serif tracking-wide"
                            placeholder="Transmit your narrative intervention..."
                        />
                        <button 
                            @click="handleManualInput"
                            class="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-slate-400 hover:text-cyan-300 transition-colors"
                        >
                            ⏎
                        </button>
                    </div>
                </div>
            </div>

        </main>
        
        <!-- Right: Floating HUD Panel -->
        <transition 
            enter-active-class="transform transition duration-500 cubic-bezier(0.25, 1, 0.5, 1)" 
            enter-from-class="translate-x-full opacity-0" 
            enter-to-class="translate-x-0 opacity-100"
            leave-active-class="transform transition duration-300 ease-in" 
            leave-from-class="translate-x-0 opacity-100" 
            leave-to-class="translate-x-full opacity-0"
        >
            <aside v-if="showHud" class="w-80 glass-panel border-l-0 shadow-2xl z-20 flex flex-col p-6 gap-8 shrink-0 h-[calc(100vh-2rem)] my-4 mr-4 rounded-3xl overflow-y-auto overflow-x-hidden backdrop-blur-2xl absolute right-0 md:relative">
               
               <!-- HUD Header -->
               <div class="flex items-center justify-between">
                  <div class="font-bold text-cyan-500/80 text-[10px] uppercase tracking-[0.2em]">Omniscient HUD</div>
                  <button 
                     @click="router.push('/guide')"
                     class="text-[10px] glass-btn px-2 py-1 rounded text-slate-400 hover:text-cyan-300 transition border border-white/5 hover:border-cyan-500/30"
                     title="Metrics Guide"
                  >
                     📖 GUIDE
                  </button>
               </div>
               
               <!-- 1. Tension Chart -->
               <div class="relative group">
                   <div class="absolute -inset-2 bg-gradient-to-r from-amber-500/10 to-transparent blur-xl opacity-0 group-hover:opacity-100 transition duration-700"></div>
                   <TensionChart :turns="store.turns" />
               </div>
               
               <!-- 2. Drift Gauge -->
               <div class="grid grid-cols-1 gap-6">
                   <SemanticDrift 
                     v-if="store.turns.length"
                     :last-turn="store.turns[store.turns.length-1]" 
                   />
                   <DialogueRatio :turns="store.turns" />
               </div>

               <!-- 3. Style Monitor -->
               <StyleMonitor :turns="store.turns" />
               
               <!-- 4. Pulse (Pacing) -->
               <div class="glass-card p-5 rounded-xl border border-white/5">
                  <div class="text-[10px] text-slate-500 uppercase tracking-wider mb-4">Narrative Pacing</div>
                  <div class="grid grid-cols-3 gap-2 text-center">
                     <div>
                        <div class="font-bold text-slate-200 text-lg">{{ pacingStats.avgLen }}</div>
                        <div class="text-[9px] text-slate-500 uppercase">Avg Len</div>
                     </div>
                     <div>
                        <div class="font-bold text-emerald-400 text-lg">{{ pacingStats.short }}%</div>
                        <div class="text-[9px] text-slate-500 uppercase">Short</div>
                     </div>
                     <div>
                        <div class="font-bold text-amber-400 text-lg">{{ pacingStats.long }}%</div>
                        <div class="text-[9px] text-slate-500 uppercase">Long</div>
                     </div>
                  </div>
               </div>

            </aside>
        </transition>
    </div>
  </div>
</template>

<style scoped>
.glass-panel {
    background: rgba(15, 23, 42, 0.4);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.glass-panel-heavy {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.glass-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.glass-btn {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    transition: all 0.2s ease;
}
.glass-btn:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.1);
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
}
</style>
