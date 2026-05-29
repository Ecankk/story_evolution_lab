<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { ForceController, type GameNode, type GameLink } from '@/controllers/ForceController';

const props = defineProps<{
  controller: ForceController;
}>();

const svgRef = ref<SVGSVGElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const nodes = ref<GameNode[]>([]);
const links = ref<GameLink[]>([]);

// Manual Drag Implementation for Vue (avoiding heavy d3-drag integration issues)
let draggingNode: GameNode | null = null;
let animationFrameId: number;
let resizeObserver: ResizeObserver | null = null;

onMounted(() => {
    props.controller.on('tick', (n: GameNode[], l: GameLink[]) => {
        nodes.value = [...n];
        links.value = [...l];
    });
    
    props.controller.on('nodeDragEnd', (node: GameNode) => {
        // Emit feedback logic up?
    });
    
    // Robust Resizing with ResizeObserver
    if (svgRef.value && canvasRef.value) {
        // Initial setup only if dimensions exist, else observer will catch it
        const rect = svgRef.value.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
            updateDimensions(rect.width, rect.height);
            startParticleSystem(rect.width, rect.height);
        }
        
        resizeObserver = new ResizeObserver(entries => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect;
                if (width > 0 && height > 0) {
                    updateDimensions(width, height);
                    // If particles haven't started (0 size init), start them now
                    if (particles.length === 0) {
                        startParticleSystem(width, height);
                    }
                }
            }
        });
        
        resizeObserver.observe(svgRef.value);
    }
    
    // Also window listener as backup for controller logic
    window.addEventListener('resize', handleWindowResize);
    // Force one update tick later to ensure layout
    setTimeout(handleWindowResize, 100);
});

onUnmounted(() => {
    window.removeEventListener('resize', handleWindowResize);
    window.removeEventListener('mousemove', onWindowMouseMove);
    window.removeEventListener('mouseup', onWindowMouseUp);
    cancelAnimationFrame(animationFrameId);
    resizeObserver?.disconnect();
});

function updateDimensions(w: number, h: number) {
    if (!canvasRef.value) return;
    
    props.controller.resize(w, h);
    
    // Check if we need to resize canvas (avoid clearing if size is same)
    if (canvasRef.value.width !== w || canvasRef.value.height !== h) {
        canvasRef.value.width = w;
        canvasRef.value.height = h;
    }
}

function handleWindowResize() {
    if (svgRef.value) {
        const rect = svgRef.value.getBoundingClientRect();
        updateDimensions(rect.width, rect.height);
    }
}

// --- Particle System ---
class Particle {
    x: number;
    y: number;
    vx: number;
    vy: number;
    life: number;
    maxLife: number;

    constructor(w: number, h: number) {
        this.x = Math.random() * w;
        this.y = Math.random() * h;
        this.vx = (Math.random() - 0.5) * 0.2;
        this.vy = (Math.random() - 0.5) * 0.2;
        this.life = Math.random() * 200;
        this.maxLife = 200 + Math.random() * 200;
    }

    respawn(w: number, h: number) {
        // Random spawn full screen
        this.x = Math.random() * w;
        this.y = Math.random() * h;
        this.life = 0;
        this.vx = (Math.random() - 0.5) * 0.2;
        this.vy = (Math.random() - 0.5) * 0.2;
    }
}

const particles: Particle[] = [];
// Increased density for full screen effect
const PARTICLE_COUNT = 300; 

function startParticleSystem(w?: number, h?: number) {
    if (!canvasRef.value) return;
    const width = w ?? canvasRef.value.clientWidth;
    const height = h ?? canvasRef.value.clientHeight;
    
    // Ensure canvas resolution matches display size
    if (canvasRef.value.width !== width || canvasRef.value.height !== height) {
        canvasRef.value.width = width;
        canvasRef.value.height = height;
    }

    // Reset particles
    particles.length = 0;
    for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push(new Particle(width, height));
    }
    
    // Cancel existing loop to avoid duplicates
    cancelAnimationFrame(animationFrameId);
    animateParticles();
}

function animateParticles() {
    const canvas = canvasRef.value;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    
    // Smooth trails
    ctx.fillStyle = 'rgba(15, 23, 42, 0.15)'; 
    ctx.fillRect(0, 0, w, h);

    const startNode = props.controller.nodes.find((n: GameNode) => n.type === 'start');
    const endNode = props.controller.nodes.find((n: GameNode) => n.type === 'end');

    ctx.fillStyle = 'rgba(100, 255, 218, 0.5)';

    particles.forEach(p => {
        // 1. Attraction to Truth (Gravity)
        if (endNode && endNode.x && endNode.y) {
            const dx = endNode.x - p.x;
            const dy = endNode.y - p.y;
            const dist = Math.sqrt(dx*dx + dy*dy);
            
            // Stronger pull when closer, but global drift
            const force = 500 / (dist + 100); 
            p.vx += (dx / dist) * force * 0.005;
            p.vy += (dy / dist) * force * 0.005;
        }

        // 2. Repulsion from Start (Anti-Gravity)
        // Also repel from "Bad" guesses?
        if (startNode && startNode.x && startNode.y) {
             const dx = p.x - startNode.x;
             const dy = p.y - startNode.y;
             const dist = Math.sqrt(dx*dx + dy*dy);
             
             // Strong push when very close
             if (dist < 400) {
                 const force = 300 / (dist + 50);
                 p.vx += (dx / dist) * force * 0.01;
                 p.vy += (dy / dist) * force * 0.01;
             }
        }

        // Damping
        p.vx *= 0.96;
        p.vy *= 0.96;

        p.x += p.vx;
        p.y += p.vy;
        p.life++;

        // Draw
        ctx.beginPath();
        // Size varies by life pulsating
        const size = Math.min(2.5, (Math.sin(p.life * 0.05) + 1.5));
        ctx.arc(p.x, p.y, size * 0.8, 0, Math.PI * 2);
        ctx.fill();

        // Screen Wrap / Respawn
        let reset = false;
        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;

        if (p.life > p.maxLife) reset = true;
        
        if (reset) {
            p.respawn(w, h);
        }
    });

    animationFrameId = requestAnimationFrame(animateParticles);
}

// Mouse Interactions
function onMouseDown(e: MouseEvent, node: GameNode) {
    if (node.type === 'start' || node.type === 'end') return; 
    
    draggingNode = node;
    try {
        props.controller.dragStart(node);
        // Attach window listeners for smooth drag outside canvas
        window.addEventListener('mousemove', onWindowMouseMove);
        window.addEventListener('mouseup', onWindowMouseUp);
    } catch (err) {
        console.error("DragStart Error:", err);
    }
}


function onWindowMouseMove(e: MouseEvent) {
    if (!draggingNode) return;
    
    try {
        if (svgRef.value && props.controller) {
            // Check if node still exists in simulation
            // D3 mutates objects, so ID check is safest
            const liveNode = props.controller.nodes.find(n => n.id === draggingNode?.id);
            if (!liveNode) {
                console.warn("Dragging dead node, aborting");
                draggingNode = null;
                return;
            }

            const rect = svgRef.value.getBoundingClientRect();
            // Calculate relative coordinates
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            props.controller.drag(liveNode, x, y);
        }
    } catch (err) {
        console.error("DragMove Error:", err);
    }
}

function onWindowMouseUp(e: MouseEvent) {
    if (draggingNode) {
        try {
            props.controller.dragEnd(draggingNode);
        } catch (err) {
            console.error("DragEnd Error:", err);
        }
        draggingNode = null;
    }
    // Clean up
    window.removeEventListener('mousemove', onWindowMouseMove);
    window.removeEventListener('mouseup', onWindowMouseUp);
}

// Helper for Feedback Line
function getFeedbackLineColor(node: GameNode) {
     const score = node.score || 0.5;
     // simple interpolation: Red (0) -> Green (1)
     // 0: rgb(239, 68, 68)
     // 1: rgb(16, 185, 129)
     const r = 239 + (16 - 239) * score;
     const g = 68 + (185 - 68) * score;
     const b = 68 + (129 - 68) * score;
     return `rgba(${r}, ${g}, ${b}, 0.6)`;
}

function getEndNodePosition() {
    const end = nodes.value.find(n => n.type === 'end');
    return end ? { x: end.x, y: end.y } : { x: 0, y: 0 };
}

function getStartNodePosition() {
    const start = nodes.value.find(n => n.type === 'start');
    return start ? { x: start.x, y: start.y } : { x: 0, y: 0 };
}
</script>

<template>
  <div class="w-full h-full bg-slate-900 overflow-hidden relative">
      <!-- Particle Canvas Layer -->
      <canvas ref="canvasRef" class="absolute inset-0 pointer-events-none opacity-60"></canvas>

      <svg ref="svgRef" class="w-full h-full relative z-10">
          <!-- Links -->
          <line v-for="(link, i) in links" :key="i"
              :x1="(link.source as GameNode).x" :y1="(link.source as GameNode).y"
              :x2="(link.target as GameNode).x" :y2="(link.target as GameNode).y"
              stroke="rgba(255,255,255,0.2)" stroke-width="1.5"
          />

          <!-- Feedback Lines (Dynamics Dual: Red to Start, Green to End) -->
           <g v-for="node in nodes" :key="'fb-' + node.id">
              <template v-if="node.type === 'guess' && (node === draggingNode || node.status !== 'uncertain')">
                 <!-- Line to Truth (Green) -->
                 <line 
                     :x1="node.x" :y1="node.y"
                     :x2="getEndNodePosition().x" :y2="getEndNodePosition().y"
                     stroke="rgba(16, 185, 129, 0.4)"
                     stroke-width="2"
                     stroke-dasharray="5,5"
                     class="transition-all duration-300"
                  />
                  <!-- Line to Start (Red) -->
                 <line 
                     :x1="node.x" :y1="node.y"
                     :x2="getStartNodePosition().x" :y2="getStartNodePosition().y"
                     stroke="rgba(239, 68, 68, 0.4)"
                     stroke-width="2"
                     stroke-dasharray="2,5"
                     class="transition-all duration-300"
                  />
              </template>
           </g>
          
          <!-- Nodes -->
          <g v-for="node in nodes" :key="node.id"
             :transform="`translate(${node.x},${node.y})`"
             @mousedown.stop="onMouseDown($event, node)"
             class="cursor-grab active:cursor-grabbing hover:opacity-90"
          >
              <!-- Glow Effect -->
              <circle r="45" fill="none" 
                :stroke="node.type === 'start' ? 'rgba(99, 102, 241, 0.3)' : node.type === 'end' ? 'rgba(16, 185, 129, 0.3)' : getFeedbackLineColor(node)"
                stroke-width="0"
                class="transition-all duration-500 animate-pulse"
                :class="{'stroke-[8px] opacity-100': node.status === 'confirmed', 'opacity-30': node.status !== 'confirmed'}"
              />

              <!-- Core Circle -->
              <circle 
                r="35" 
                :fill="node.type === 'start' ? '#4f46e5' : node.type === 'end' ? '#059669' : '#d97706'"
                class="shadow-xl transition-all duration-300 backdrop-blur-md"
                :style="{ fillOpacity: 0.8 }"
                :stroke="node.status === 'confirmed' ? '#fff' : 'rgba(255,255,255,0.2)'"
                :stroke-width="node.status === 'confirmed' ? 3 : 1"
              />
              
              <!-- Icon/Type Label inside circle -->
              <text text-anchor="middle" dy=".3em" fill="white" font-weight="bold" font-size="18px" pointer-events="none" style="text-shadow: 0 2px 4px rgba(0,0,0,0.5)">
                  {{ node.type === 'start' ? 'Start' : node.type === 'end' ? 'Truth' : '?' }}
              </text>

              <!-- Text Label -->
              <foreignObject x="-75" y="-100" width="150" height="60" class="pointer-events-none overflow-visible">
                  <div xmlns="http://www.w3.org/1999/xhtml" class="flex flex-col items-center justify-end h-full">
                      <div class="text-[10px] text-slate-100 text-center bg-black/50 px-3 py-2 rounded-lg backdrop-blur-md border border-white/10 shadow-lg whitespace-pre-wrap break-words w-full leading-tight">
                          {{ node.text || '(Empty)' }}
                      </div>
                      
                      <!-- Hot/Cold Label under text -->
                      <div v-if="node.type === 'guess'" 
                        :class="(node.score || 0.5) > 0.6 ? 'text-emerald-300' : (node.score || 0.5) < 0.4 ? 'text-rose-300' : 'text-slate-400'"
                        class="text-[9px] font-mono mt-1 bg-black/60 px-1 rounded"
                      >
                         {{ Math.round((node.score || 0.5) * 100) }}% Sim
                      </div>
                  </div>
              </foreignObject>
          </g>
          
          <!-- Truth Axis / Zone Indicators (Visual Guide) -->
          <text :x="props.controller.width * 0.8" :y="props.controller.height / 2 + 80" fill="rgba(16, 185, 129, 0.1)" text-anchor="middle" font-size="80" font-weight="900" style="pointer-events: none;">TRUTH</text>
           <text :x="props.controller.width * 0.2" :y="props.controller.height / 2 + 80" fill="rgba(99, 102, 241, 0.1)" text-anchor="middle" font-size="80" font-weight="900" style="pointer-events: none;">START</text>
      </svg>
      
  </div>
</template>
