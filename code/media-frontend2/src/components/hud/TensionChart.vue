<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import type { Turn } from '@/types';
import * as echarts from 'echarts';

const props = defineProps<{
  turns: Turn[];
}>();

const chartRef = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

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

  // Map data: x=index, y=value
  const tensionData = props.turns.map((t, i) => [i + 1, t.tension_score || 0]);
  const sentimentData = props.turns.map((t, i) => [i + 1, (t.sentiment_score || 0) * 0.5 + 0.5]); // Archive -1..1 to 0..1 for easier overlay

  const option = {
    title: { text: '叙事弧光 (Narrative Arc)', left: 'center', textStyle: { fontSize: 12, color: '#64748b' } },
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, data: ['张力 (Tension)', '情感 (Sentiment)'] },
    grid: { top: 30, bottom: 25, left: 30, right: 30 },
    xAxis: { type: 'value', show: false },
    yAxis: { type: 'value', min: 0, max: 1, splitLine: { show: false } },
    series: [
      {
        name: '张力 (Tension)',
        data: tensionData,
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3, color: '#f43f5e' }, // Rose (Suspense)
        areaStyle: {
             color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(244, 63, 94, 0.5)' },
              { offset: 1, color: 'rgba(244, 63, 94, 0)' }
            ])
        }
      },
      {
        name: '情感 (Sentiment)',
        data: sentimentData,
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color: '#06b6d4' }, // Cyan (Emotion)
        areaStyle: {
             color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(6, 182, 212, 0.3)' },
              { offset: 1, color: 'rgba(6, 182, 212, 0)' }
            ])
        }
      }
    ]
  };

  chartInstance.setOption(option);
}
</script>

<template>
  <div ref="chartRef" class="w-full h-32"></div>
</template>
