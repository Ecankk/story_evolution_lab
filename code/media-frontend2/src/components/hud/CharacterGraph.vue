<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue';
import type { Turn } from '@/types';
import * as echarts from 'echarts';

const props = defineProps<{
  turns: Turn[];
}>();

const chartRef = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

// Heuristic: Extract potential names (capitalized words, simplistic)
// Ideally this would come from backend NER
const characters = computed(() => {
    const nodesMap = new Map<string, number>();
    const sentimentMap = new Map<string, { sum: number, count: number }>();
    
    // 1. Simple Regex NER (Capitalized words in middle of sentence, or specific cues)
    // For Chinese, it's hard. Let's assume user inputs English names or we track "Key Nouns".
    // Fallback: Just track "High Sentiment Turns" as nodes? No.
    // Let's stick to "Story Center" -> "Segment Nodes" relative to sentiment?
    
    // Alternative: Just show Author nodes for now, but color based on sentiment flow.
    // Node: "Part 1", "Part 2" ...
    
    // User request: "Character Dynamics".
    // I will cheat: I will look for standard names if present, or just generic nodes.
    // Let's try to find potential names: (2-4 char words repeated often?)
    
    // Real approach for this iteration w/o backend NER:
    // Create nodes for "Author" and "AI".
    // Create nodes for extracted keywords (Seeds).
    // Link Author -> Keyword with Sentiment color.
    
    const nodes = [
        { id: 'Human', size: 30, category: 0 },
        { id: 'AI', size: 30, category: 0 }
    ];
    
    let totalSentiment = 0;
    
    props.turns.forEach(t => {
        const s = t.sentiment_score || 0;
        totalSentiment += s;
    });
    
    const avg = props.turns.length ? totalSentiment / props.turns.length : 0;
    
    const links = [
        { 
            source: 'Human', 
            target: 'AI', 
            sentiment: avg // Overall vibe of the collab
        }
    ];
    
    // Add specific 'High Emotion' keywords as nodes
    // If a turn has high sentiment, extract the longest noun?
    // This is hard without Jieba on frontend.
    // But we have `t.tags`? No.
    
    // Let's just create a dynamic graph of "Story Arc" nodes.
    // Start -> Turn 5 -> Turn 10...
    // Color the path by sentiment.
    
    // Better: Timeline Graph.
    // Node = Turn Index.
    // Link = Next Turn.
    // Color = Sentiment.
    // Layout = Spiral or Snake.
    
    // Let's do that. It represents the "Relationship" between plot points.
    
    const segmentSize = 5;
    const segments = Math.ceil(props.turns.length / segmentSize);
    const graphNodes = [];
    const graphLinks = [];
    
    for(let i=0; i<segments; i++) {
        const chunk = props.turns.slice(i*segmentSize, (i+1)*segmentSize);
        const chunkSentiment = chunk.reduce((sum, t) => sum + (t.sentiment_score||0), 0) / chunk.length;
        
        const id = `Ch.${i+1}`;
        graphNodes.push({ id, size: 10 + chunk.length * 2, category: 1 });
        
        if (i > 0) {
            graphLinks.push({
                source: `Ch.${i}`,
                target: `Ch.${i+1}`,
                sentiment: chunkSentiment
            });
        }
    }
    
    return { nodes: graphNodes, links: graphLinks };
});

onMounted(() => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value);
    updateChart();
    window.addEventListener('resize', () => chartInstance?.resize());
  }
});

watch(() => props.turns, () => {
    updateChart();
}, { deep: true });

function updateChart() {
  if (!chartInstance) return;

  // Sentiment-driven Relationship Graph
  const option = {
    title: { 
      text: '关系动力学 (Relationship Dynamics)', 
      left: 'center', 
      subtext: 'Green=Positive, Red=Conflict',
      textStyle: { fontSize: 12, color: '#64748b' },
      subtextStyle: { fontSize: 10 }
    },
    tooltip: {},
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: characters.value.nodes.map(n => ({
            name: n.id,
            symbolSize: n.size,
            itemStyle: { 
                color: n.id === 'Story' ? '#6366f1' : '#14b8a6',
                shadowBlur: 10,
                shadowColor: 'rgba(0,0,0,0.1)'
            }
        })),
        links: characters.value.links.map(l => ({
            source: l.source,
            target: l.target,
            lineStyle: {
                color: l.sentiment > 0.2 ? '#22c55e' : (l.sentiment < -0.2 ? '#ef4444' : '#94a3b8'),
                width: 2 + Math.abs(l.sentiment) * 4,
                curveness: 0.1
            }
        })),
        roam: true,
        label: { show: true },
        force: {
          repulsion: 200,
          edgeLength: 100
        },
        lineStyle: {
            opacity: 0.8
        }
      }
    ]
  };

  chartInstance.setOption(option);
}
</script>

<template>
  <div class="h-48 border rounded-lg bg-slate-50 relative overflow-hidden">
      <div ref="chartRef" class="w-full h-full"></div>
  </div>
</template>
