<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="monitor-overlay pointer-events-none fixed inset-0 z-50"></div>
  <RouterView />
</template>

<style>
/* CRT Scanline Effect (Optional, matching retro-future vibe) */
.monitor-overlay {
    background: linear-gradient(
        to bottom,
        rgba(255, 255, 255, 0),
        rgba(255, 255, 255, 0) 50%,
        rgba(0, 0, 0, 0.1) 50%,
        rgba(0, 0, 0, 0.1)
    );
    background-size: 100% 4px;
    opacity: 0.15;
    pointer-events: none;
}
</style>
