<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue';
import { useStoryStore } from '@/stores/storyStore';
import * as d3 from 'd3';

const store = useStoryStore();
const container = ref<HTMLElement | null>(null);
const tooltip = ref<HTMLElement | null>(null);
const tooltipContent = ref({ title: '', text: '' });

// Dimensions
const width = 300; // Fixed width for sidebar
const height = 800; // Initial height, will grow

// Computed tree data
const treeData = computed(() => store.treeData);

// Re-fetch tree when story ID changes (Scope the tree to the new story)
watch(() => store.currentStoryId, (newId) => {
    if (newId) {
        store.fetchAllStories(newId);
    }
}, { immediate: true });

// Watch for data changes to re-render
watch(() => store.treeData, (newData) => {
    if (newData.nodes.length) {
        renderTree();
    }
}, { deep: true });

function renderTree() {
    if (!container.value) return;
    
    // clear previous
    d3.select(container.value).selectAll("*").remove();

    const data = store.treeData;
    if (!data.nodes.length) return;

    // 1. Construct Hierarchy
    // We need to convert flat nodes/links to hierarchical data for d3.tree
    // Strategy: Find root (node with no parent or parent not in list)
    // Multiverse might have multiple roots if unconnected (though unlikely if all from one genesis).
    // Let's assume single root or handle multiple by adding a virtual root?
    // Or just stratify.
    
    // Strategy: Handle multiple roots by adding a virtual root if needed.
    let processedNodes = JSON.parse(JSON.stringify(data.nodes));
    const nodeMap = new Map(processedNodes.map((n: any) => [n.id, n]));
    
    // Find roots (nodes with no parent or parent not in map)
    const roots = processedNodes.filter((n: any) => !n.parent || !nodeMap.has(n.parent));
    
    if (roots.length > 1) {
        const virtualRoot = {
            id: "MV_ROOT",
            label: "ORIGIN",
            preview: "Multiverse Origin",
            parent: null,
            group: 0
        };
        processedNodes.push(virtualRoot);
        roots.forEach((n: any) => n.parent = "MV_ROOT");
    } else if (roots.length === 1) {
         if (roots[0].parent && !nodeMap.has(roots[0].parent)) roots[0].parent = null;
    }

    try {
        const root = d3.stratify<{id: string, parent: string | null}>()
            .id(d => d.id)
            .parentId(d => d.parent)
            (processedNodes);

        // 2. Compute Layout
        // Width is constrained (300px), Height depends on depth
        // We want a vertical tree? Or horizontal?
        // Sidebar is narrow (w-80 ~ 320px). Vertical tree (root at top) flows down.
        // Or Horizontal (root at left) flows right? 
        // Horizontal: depth grows to right. If depth is large, we scroll horizontal? 
        // Sidebar usually scrolls vertical. So Vertical Tree is better.
        
        // Node size: x=width, y=height
        const nodeWidth = 40;
        const nodeHeight = 80; // Vertical spacing
        
        // Dynamic height based on total nodes?
        // d3.tree size is [width, height].
        // Ideally we want fixed width, variable height.
        
        // Count leaves to estimate required width if strictly tree?
        // Actually for vertical tree, X is Main Axis (width), Y is Depth.
        // If tree gets wide, it might squeeze. 
        // Let's try simple Tree first.
        
        const treeLayout = d3.tree<any>()
            .size([width - 40, root.height * nodeHeight + 100]) // Height based on depth
            .nodeSize([60, 80]); // [width, height] per node separation

        // We use nodeSize, so we need to center the root manually
        
        const hierarchy = d3.hierarchy(root); 
        // Note: stratify returns a hierarchy, but d3.tree needs it? 
        // Actually stratify returns a Node which IS a hierarchy.
        
        const treeRoot = treeLayout(root);

        // Calculate bounds to set SVG size (Edit: Skip MV_ROOT for bounds)
        let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
        treeRoot.descendants().forEach(d => {
            if (d.data.id === "MV_ROOT") return; // Skip virtual root in bounds
            if (d.x < x0) x0 = d.x;
            if (d.x > x1) x1 = d.x;
            if (d.y < y0) y0 = d.y;
            if (d.y > y1) y1 = d.y;
        });
        
        // Add padding
        const svgHeight = (y1 - y0) + 100;
        const svgWidth = (x1 - x0) + 100;
        
        // Translate to center
        // const translateX = -x0 + 50;
        // const translateY = -y0 + 50;

        const svg = d3.select(container.value)
            .append("svg")
            .attr("width", svgWidth > width ? svgWidth : width) // Min width
            .attr("height", svgHeight)
            .attr("viewBox", `${x0 - 50} ${y0 - 50} ${svgWidth} ${svgHeight}`)
            .style("overflow", "visible"); // Allow tooltips etc

        const g = svg.append("g");

        // 3. Links (Filter out links from MV_ROOT)
        g.selectAll(".link")
            .data(treeRoot.links().filter(d => d.source.data.id !== "MV_ROOT")) 
            .enter().append("path")
            .attr("class", "link")
            .attr("d", d3.linkVertical<any, any>()
                .x(d => d.x)
                .y(d => d.y)
            )
            .attr("fill", "none")
            .attr("stroke", "#475569") // slate-600
            .attr("stroke-width", 1.5)
            .attr("opacity", 0.6);

        // 4. Nodes (Filter out MV_ROOT)
        const node = g.selectAll(".node")
            .data(treeRoot.descendants().filter(d => d.data.id !== "MV_ROOT"))
            .enter().append("g")
            .attr("class", d => `node ${d.data.id === store.currentStoryId ? 'active' : ''}`)
            .attr("transform", d => `translate(${d.x},${d.y})`)
            .style("cursor", "pointer")
            .on("click", (event, d) => {
                store.fetchStory(d.data.id);
            })
            .on("mouseover", (event, d) => {
                // Show Tooltip
                const rawNode = d.data; // d.data is original item
                tooltipContent.value = {
                    title: rawNode.label,
                    text: rawNode.preview
                };
                if (tooltip.value) {
                    tooltip.value.style.display = "block";
                    tooltip.value.style.left = `${event.pageX + 10}px`;
                    tooltip.value.style.top = `${event.pageY + 10}px`;
                }
            })
            .on("mouseout", () => {
                if (tooltip.value) tooltip.value.style.display = "none";
            });

        // Circle
        node.append("circle")
            .attr("r", 6)
            .attr("fill", d => d.data.id === store.currentStoryId ? "#22d3ee" : "#0f172a") // cyan-400 : slate-900
            .attr("stroke", d => d.data.id === store.currentStoryId ? "#22d3ee" : "#94a3b8") // cyan-400 : slate-400
            .attr("stroke-width", 2);
        
        // Labels (ID)
        node.append("text")
            .attr("dy", -10)
            .attr("x", 0)
            .style("text-anchor", "middle")
            .text(d => d.data.label)
            .style("font-size", "8px")
            .style("fill", "#cbd5e1") // slate-300
            .style("pointer-events", "none")
            .style("text-shadow", "0 1px 2px rgba(0,0,0,0.8)");

    } catch (e) {
        console.error("D3 Render Error", e);
        if (container.value) {
            container.value.innerHTML = `<div class='text-red-500 text-xs p-4'>Tree Error: ${e}</div>`;
        }
    }
}
</script>

<template>
    <aside class="w-80 h-full glass-panel-left flex flex-col hidden md:flex shrink-0 z-20 my-4 ml-4 rounded-3xl relative">
        <div class="flex items-center justify-between p-4 px-6 border-b border-white/5 bg-black/20 rounded-t-3xl">
            <div class="text-[10px] font-bold text-cyan-500/80 uppercase tracking-[0.2em] flex items-center gap-2">
                <span class="text-lg">🕸️</span> Multiverse Tree
            </div>
            <div class="text-[10px] text-slate-500 font-mono">{{ store.treeData.nodes.length }} Nodes</div>
        </div>

        <!-- D3 Container Area -->
        <div class="flex-1 overflow-hidden relative"> <!-- Wrapper -->
            
            <!-- Loading State (Vue Managed) -->
             <div v-if="!store.treeData.nodes.length" class="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
                <span class="text-slate-500 text-xs">Loading structure...</span>
            </div>

            <!-- D3 Target (Pure DOM only) -->
            <div class="w-full h-full overflow-auto custom-scrollbar" ref="container"></div>
        </div>

        <!-- Tooltip Portal -->
        <div ref="tooltip" class="fixed hidden pointer-events-none z-50 max-w-xs transition-opacity duration-200">
            <div class="glass-tooltip p-3 rounded-lg shadow-xl border border-white/10 backdrop-blur-md bg-slate-900/90 text-slate-200">
                <div class="font-bold text-cyan-300 text-xs mb-1">{{ tooltipContent.title }}</div>
                <div class="text-[10px] text-slate-400 leading-tight line-clamp-4">{{ tooltipContent.text }}</div>
            </div>
        </div>
    </aside>
</template>

<style scoped>
.glass-panel-left {
    background: rgba(15, 23, 42, 0.6); 
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.glass-tooltip {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.custom-scrollbar::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
}
</style>
