<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import UniverseCanvas from '@/components/game/UniverseCanvas.vue';
import StartEndNode from '@/components/game/StartEndNode.vue';
import { ForceController, type GameNode } from '@/controllers/ForceController';
import { llmService } from '@/services/llm';

// Game State
const isPlaying = ref(false);
const isLoading = ref(false);
const startText = ref("");
const endText = ref("");

// Physics
const controller = new ForceController(window.innerWidth, window.innerHeight);

// Settings State
const showSettings = ref(false);
const settings = reactive({
    provider: 'deepseek',
    apiKey: '',
    baseUrl: '',
    model: ''
});

onMounted(() => {
    // Load Settings
    const saved = llmService.getSettings();
    if (saved) {
        settings.provider = saved.provider || 'deepseek';
        settings.apiKey = saved.apiKey || '';
        settings.baseUrl = saved.baseUrl || '';
        settings.model = saved.model || '';
    }

    // Auto-Resume Session
    // Auto-Resume Session
    if (controller.loadSession()) {
        const startNode = controller.nodes.find(n => n.type === 'start');
        const endNode = controller.nodes.find(n => n.type === 'end');
        if (startNode && endNode) {
            startText.value = startNode.text;
            endText.value = endNode.text;
            isPlaying.value = true;
            console.log("Resumed previous session from localStorage");
            
            // Re-expose tools on resume
            (window as any).gameController = controller;
            (window as any).gameDebug = {
                getRoundCount: () => controller.nodes.filter(n => n.type === 'guess').length,
                forceWin: (reason: string) => {
                    winContent.value = reason || "人工降神，强制结案。";
                    showWin.value = true;
                    controller.addGuess("★ [ADMIN] 强制还原: " + winContent.value);
                }
            };
        }
    }
});

// Game Logic
async function onGameStart(start: string, end: string) {
    // Clear old session if starting explicitly new
    controller.clearSession();
    
    startText.value = start;
    endText.value = end;
    isPlaying.value = true;
    
    controller.init(start, end);
    
    // Expose for manual intervention
    (window as any).gameController = controller;
    
    // Expose Debug Tools
    (window as any).gameDebug = {
        getRoundCount: () => controller.nodes.filter(n => n.type === 'guess').length,
        forceWin: (reason: string) => {
            winContent.value = reason || "人工降神，强制结案。";
            showWin.value = true;
            controller.addGuess("★ [ADMIN] 强制还原: " + winContent.value);
        }
    };
    
    console.log("Game Debug Tools exposed as window.gameDebug");
    
    // First Detective Turn
    await nextTurn();
}

// Reset Game Logic
function resetGame() {
    controller.clearSession();
    isPlaying.value = false;
    startText.value = "";
    endText.value = "";
    showWin.value = false;
    console.log("Game reset to input screen");
}

function saveSettings() {
    llmService.saveSettings({
        provider: settings.provider as 'deepseek' | 'gemini',
        apiKey: settings.apiKey,
        baseUrl: settings.baseUrl,
        model: settings.model
    });
    showSettings.value = false;
    alert("设置已保存 ✨");
}

// Win State
const showWin = ref(false);
const winContent = ref("");

async function nextTurn() {
    if (isLoading.value) return;
    isLoading.value = true;
    
    // Collect History from Nodes
    const history = controller.nodes
        .filter(n => n.type === 'guess')
        .map(n => ({
            text: n.text,
            status: n.status, // Keep for legacy
            score: n.score || 0.5 // New continuous feedback (0-1)
        }));
        
    try {
        const rawResponse = await llmService.detectiveTurn(startText.value, endText.value, history);
        console.log("[Game] Received AI Response:", rawResponse);

        // Check for Solved Signal
        if (rawResponse.startsWith("[SOLVED]")) {
            const cleanContent = rawResponse.replace("[SOLVED]", "").trim();
            winContent.value = cleanContent;
            showWin.value = true;
            // Optionally still add a node for record
            controller.addGuess("★ 还原真相: " + cleanContent);
        } else {
             // Clean up any accidental strict prefixes if LLM fails instruction
            const cleanGuess = rawResponse.replace(/^【.*?】/, "").trim();
            controller.addGuess(cleanGuess);
        }
        
        // Auto-update visuals based on status if needed (e.g. show colors)
        controller.nodes.forEach(n => {
            if (n.type === 'guess') n.status = getNodeStatus(n);
        });
        
        // SAVE STATE
        controller.saveSession();
        
    } catch (e) {
        console.error(e);
        alert("侦探罢工了");
    } finally {
        isLoading.value = false;
    }
}


// Reveal Truth Logic
async function triggerReveal() {
    if (isLoading.value) return;
    if (!confirm("确定要直接还原真相吗？这将结合当前线索给出最终故事。")) return;
    
    isLoading.value = true;
    try {
        const history = controller.nodes
            .filter(n => n.type === 'guess')
            .map(n => ({
                text: n.text,
                status: n.status, 
                score: n.score || 0.5 
            }));
            
        const rawResponse = await llmService.revealTruth(startText.value, endText.value, history);
        
        const cleanContent = rawResponse.replace("[SOLVED]", "").trim();
        winContent.value = cleanContent;
        showWin.value = true;
        
        // Per user request: Do NOT add as a node, just show result.
        // controller.addGuess("★ [终极还原]: " + cleanContent);
        // controller.saveSession();
        
    } catch (e) {
        console.error(e);
        alert("还原失败，请重试");
    } finally {
        isLoading.value = false;
    }
}

// Controller Event Handling
controller.on('nodeDragEnd', (node: GameNode) => {
    // Status is now derived from the continuous score
    node.score = getNodeScore(node);
    
    // Visual Thresholds for UI (Gradient would be better in Phase 6)
    if (node.score > 0.65) node.status = 'confirmed';
    else if (node.score < 0.35) node.status = 'rejected';
    else node.status = 'uncertain';
    
    // Save position changes
    controller.saveSession();
});

// Real-time Feedback Loop
controller.on('tick', () => {
   controller.nodes.forEach(n => {
       if (n.type === 'guess') {
            n.score = getNodeScore(n);
            // Dynamic thresholds
            if (n.score > 0.65) n.status = 'confirmed';
            else if (n.score < 0.35) n.status = 'rejected';
            else n.status = 'uncertain';
       }
   });
});

function getNodeScore(node: GameNode): number {
    if (node.type !== 'guess') return 0.5;
    
    const startNode = controller.nodes.find(n => n.type === 'start');
    const endNode = controller.nodes.find(n => n.type === 'end');
    
    if (!startNode || !endNode || !node.x || !startNode.x || !endNode.x) return 0.5;
    
    // Distance to Start
    const dxS = node.x - startNode.x;
    const dyS = node.y - startNode.y;
    const distS = Math.sqrt(dxS*dxS + dyS*dyS);
    
    // Distance to End
    const dxE = node.x - endNode.x;
    const dyE = node.y - endNode.y;
    const distE = Math.sqrt(dxE*dxE + dyE*dyE);
    
    // Formula: Score = dS / (dS + dE)
    // Close to Start -> dS small -> Score -> 0
    // Close to End -> dE small -> Score -> 1
    const total = distS + distE;
    if (total === 0) return 0.5;
    
    return distS / total;
}

// Legacy wrapper if needed, but we used direct assignment above
function getNodeStatus(node: GameNode): 'confirmed' | 'rejected' | 'uncertain' {
    const score = getNodeScore(node);
    if (score > 0.65) return 'confirmed';
    if (score < 0.35) return 'rejected';
    return 'uncertain';
}

</script>

<template>
  <div class="w-screen h-screen relative overflow-hidden">
      <!-- Intro Screen -->
      <div v-if="!isPlaying" class="absolute inset-0 flex items-center justify-center z-20 bg-black/40 backdrop-blur-sm">
          <StartEndNode @start="onGameStart" />
          
          <!-- Settings Button -->
          <button @click="showSettings = true" class="absolute top-6 right-6 p-2 rounded-full glass-btn hover:bg-white/10 text-slate-400 hover:text-white transition-colors" title="API 设置">
              ⚙️
          </button>
      </div>

      <!-- Settings Modal -->
      <div v-if="showSettings" class="absolute inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-md">
         <div class="glass-panel w-full max-w-md p-6 rounded-2xl border border-white/10 shadow-2xl">
            <h3 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
                ⚙️ API 配置
            </h3>
            
            <div class="space-y-4">
                <div>
                    <label class="block text-xs text-slate-400 mb-1">Provider</label>
                    <select v-model="settings.provider" class="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-slate-200 focus:border-emerald-500 outline-none">
                        <option value="deepseek">DeepSeek (OpenAI compatible)</option>
                        <option value="gemini">Google Gemini</option>
                    </select>
                </div>
                
                <div>
                    <label class="block text-xs text-slate-400 mb-1">API Key</label>
                    <input type="password" v-model="settings.apiKey" placeholder="sk-..." class="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-slate-200 focus:border-emerald-500 outline-none">
                </div>
                
                <div>
                    <label class="block text-xs text-slate-400 mb-1">Base URL (Optional)</label>
                    <input type="text" v-model="settings.baseUrl" placeholder="https://api.deepseek.com" class="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-slate-200 focus:border-emerald-500 outline-none">
                </div>
                
                <div>
                    <label class="block text-xs text-slate-400 mb-1">Model Name (Optional)</label>
                    <input type="text" v-model="settings.model" placeholder="deepseek-reasoner / gemini-2.0-flash" class="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-slate-200 focus:border-emerald-500 outline-none">
                </div>
            </div>
            
            <div class="mt-6 flex justify-end gap-3">
                <button @click="showSettings = false" class="px-4 py-2 text-slate-400 hover:text-white transition-colors">取消</button>
                <button @click="saveSettings" class="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg shadow-lg transition-all">保存</button>
            </div>
         </div>
      </div>

      <!-- Top Controls -->
      <div v-if="isPlaying" class="absolute top-6 right-6 z-50">
           <button @click="resetGame" class="glass-btn px-4 py-2 text-xs rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors">
               ↺ 重新开始 (New Game)
           </button>
      </div>

       <!-- Top Hint Overlay -->
      <div class="absolute top-6 left-1/2 -translate-x-1/2 z-30 pointer-events-none">
         <div class="glass-panel px-6 py-2 rounded-full border border-white/10 shadow-lg flex items-center gap-3 text-sm text-slate-300 backdrop-blur-md">
            <span>💡</span>
            <span>
                <span class="text-indigo-300 font-bold">Start (否)</span> 
                <span class="mx-2 text-slate-600">← 拖动距离 →</span>
                <span class="text-emerald-300 font-bold">Truth (是)</span>
            </span>
         </div>
         <div class="text-[10px] text-center mt-1 text-slate-500 tracking-wider uppercase opacity-70">
            Vector Field Active
         </div>
      </div>
      
      <!-- Canvas -->
      <UniverseCanvas :controller="controller" />
      
      <!-- HUD / Controls -->
      <!-- Win Card Modal -->
      <transition 
        enter-active-class="transition duration-500 ease-out"
        enter-from-class="opacity-0 scale-90 translate-y-10"
        enter-to-class="opacity-100 scale-100 translate-y-0"
        leave-active-class="transition duration-300 ease-in"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-90"
      >
        <div v-if="showWin" class="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4">
            <div class="glass-panel border border-emerald-500/50 rounded-2xl p-8 max-w-2xl w-full shadow-[0_0_50px_rgba(16,185,129,0.2)] relative overflow-hidden">
                <!-- Background Glow -->
                <div class="absolute -top-20 -right-20 w-64 h-64 bg-emerald-500/20 rounded-full blur-3xl pointer-events-none"></div>
                
                <h2 class="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-300 mb-6 flex items-center gap-3">
                    🏁 侦探已破解谜题！
                </h2>
                
                <div class="prose prose-invert max-w-none mb-8 text-lg leading-relaxed text-slate-200 max-h-[60vh] overflow-y-auto custom-scrollbar pr-4">
                    {{ winContent }}
                </div>
                
                <div class="flex justify-end gap-3">
                    <button @click="showWin = false" class="px-6 py-2 rounded-lg glass-btn hover:bg-white/10 text-slate-300 transition-colors">
                        留在现场
                    </button>
                    <button @click="isPlaying = false; showWin = false" class="px-6 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow-lg transition-transform hover:-translate-y-0.5 shadow-emerald-500/30">
                        开启新游戏
                    </button>
                </div>
            </div>
        </div>
      </transition>

      <div v-if="isPlaying" class="absolute bottom-8 left-0 right-0 flex justify-center pointer-events-none z-50">
          <button 
            @click="nextTurn"
            class="glass-panel backdrop-blur-xl border border-emerald-500/30 text-emerald-300 text-lg font-bold px-8 py-3 rounded-full shadow-lg pointer-events-auto transition-all hover:scale-105 active:scale-95 flex items-center gap-2 hover:bg-emerald-500/10 hover:shadow-[0_0_20px_rgba(16,185,129,0.4)]"
            :disabled="isLoading"
          >
              <span v-if="isLoading" class="animate-pulse">🤔 推理中...</span>
              <span v-else>🔍 下一轮推理 (Next Turn)</span>
          </button>
          
          <button 
            @click="triggerReveal"
            class="ml-4 glass-panel backdrop-blur-xl border border-indigo-500/30 text-indigo-300 text-lg font-bold px-6 py-3 rounded-full shadow-lg pointer-events-auto transition-all hover:scale-105 active:scale-95 hover:bg-indigo-500/10"
            :disabled="isLoading"
            title="直接还原故事真相"
          >
              🧩 还原真相
          </button>
      </div>
      
      <!-- Back Button -->
       <router-link to="/workbench" class="absolute top-4 left-4 glass-btn px-3 py-1 rounded text-slate-400 hover:text-white z-50 text-sm flex items-center gap-1 transition-all">
           ← 返回工作台
       </router-link>
  </div>
</template>

<style scoped>
.glass-panel {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(16px);
}
.glass-btn {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
</style>
