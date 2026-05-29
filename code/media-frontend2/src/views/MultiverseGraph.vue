<script setup lang="ts">
import { onMounted, ref, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useStoryStore } from '@/stores/storyStore';
import * as d3 from 'd3';

const router = useRouter();
const store = useStoryStore();
const container = ref<HTMLElement | null>(null);

const goBack = () => {
    router.push('/workbench');
};

const showAllUniverses = ref(true); // Default true (Show full Multiverse)

const fetchData = async () => {
    if (showAllUniverses.value) {
        await store.fetchAllStories(undefined, true);
    } else {
        await store.fetchAllStories(store.currentStoryId, false);
    }
};

const toggleFilter = async () => {
    showAllUniverses.value = !showAllUniverses.value;
    await fetchData();
    renderGraph(); // Re-render function
};

// ... inside onMounted replace initial fetch and extract render logic ...
onMounted(async () => {
    try {
        if (!d3) return;
        
        await fetchData();
        renderGraph();
        
        console.log("MultiverseMap: Mounted successfully");
    } catch (err) {
        console.error("MultiverseMap: Fatal error", err);
    }
});

function renderGraph() {
        // Defensive copy
        const nodesData = store.treeData?.nodes || [];
        const linksData = store.treeData?.links || [];

        // Clean ID mappings for D3 (it mutates objects)
        const nodes = nodesData.map(d => ({ ...d }));
        const links = linksData.map(d => ({ ...d }));

        if (!container.value) return;

        const width = window.innerWidth;
        const height = window.innerHeight;

        // Clear previous
        d3.select(container.value).selectAll("*").remove();

        const svg = d3.select(container.value)
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .style("background", "transparent");

        // Container Group for Zoom
        const mainGroup = svg.append("g");

        // Simulation
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id((d: any) => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-400))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collide", d3.forceCollide(50));

        // Links
        const link = mainGroup.append("g")
            .attr("stroke", "rgba(255,255,255,0.2)")
            .attr("stroke-width", 2)
            .selectAll("line")
            .data(links)
            .join("line");

        // Nodes
        const node = mainGroup.append("g")
            .selectAll("g")
            .data(nodes)
            .join("g")
            .call(d3.drag<any, any>()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        // Node Circle
        node.append("circle")
            .attr("r", (d: any) => d.id === store.currentStoryId ? 35 : (d.parent ? 20 : 30)) // Larger for current
            .attr("fill", (d: any) => d.id === store.currentStoryId ? "#10b981" : (d.parent ? "#302b63" : "#f6d365")) // Green for current
            .attr("stroke", (d: any) => d.id === store.currentStoryId ? "#fff" : (d.parent ? "#6366f1" : "#f6d365"))
            .attr("stroke-width", (d: any) => d.id === store.currentStoryId ? 4 : 2)
            .attr("class", "cursor-pointer transition-all duration-300")
            .style("filter", (d: any) => d.id === store.currentStoryId ? "drop-shadow(0 0 15px rgba(16, 185, 129, 0.6))" : "drop-shadow(0 0 10px rgba(99,102,241,0.5))");
        
        // Icons/Text inside
        node.append("text")
            .text((d: any) => d.id === store.currentStoryId ? "📍" : (d.parent ? "🪐" : "☀️"))
            .attr("dy", 6)
            .attr("text-anchor", "middle")
            .attr("font-size", (d: any) => d.parent ? 20 : 28)
            .style("pointer-events", "none"); 

        // Label
        node.append("text")
            .text((d: any) => d.label)
            .attr("dy", 45)
            .attr("text-anchor", "middle")
            .attr("fill", "#e2e8f0")
            .attr("font-size", 12)
            .style("pointer-events", "none")
            .style("opacity", 0.8);

        // Functions
        function dragstarted(event: any, d: any) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event: any, d: any) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event: any, d: any) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        // Tick
        simulation.on("tick", () => {
            link
                .attr("x1", (d: any) => d.source.x)
                .attr("y1", (d: any) => d.source.y)
                .attr("x2", (d: any) => d.target.x)
                .attr("y2", (d: any) => d.target.y);

            node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
        });

        // Click
        node.on("click", async (event, d: any) => {
             if (d.id !== store.currentStoryId) {
                  await store.fetchStory(d.id);
             }
             router.push('/workbench');
        });

        // Zoom
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {
                mainGroup.attr("transform", event.transform);
            });
        svg.call(zoom as any);
}
</script>

<template>
    <div class="fixed inset-0 z-50 overflow-hidden bg-gradient-to-br from-[#0f0c29] via-[#302b63] to-[#24243e]">
        <!-- Stars layer -->
        <div ref="container" class="w-full h-full"></div>

        <!-- UI Overlay -->
        <div class="absolute top-6 left-6 z-50 flex flex-col gap-4">
            <button @click="goBack" class="glass-btn px-6 py-3 rounded-full text-slate-200 hover:text-white flex items-center gap-2 w-fit">
                ← Back to Work
            </button>
            
            <!-- Filter Toggle -->
            <button @click="toggleFilter" 
                class="glass-btn px-4 py-2 rounded-full text-sm flex items-center gap-2 w-fit"
                :class="showAllUniverses ? 'border-emerald-500/50 text-emerald-100' : 'text-slate-400'"
            >
                <span class="w-3 h-3 rounded-full" :class="showAllUniverses ? 'bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.8)]' : 'bg-slate-600'"></span>
                {{ showAllUniverses ? 'Showing All Universes' : 'Focus: Related Timeline' }}
            </button>
        </div>

        <div class="absolute bottom-6 left-6 z-50 text-slate-500 text-sm max-w-md pointer-events-none">
            <h3 class="text-slate-300 font-bold mb-1">Multiverse Map</h3>
            <p>Each node represents a parallel story universe. Click to time-travel to that reality.</p>
        </div>
    </div>
</template>

<style scoped>
.glass-btn {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}
.glass-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.3);
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
}
</style>
