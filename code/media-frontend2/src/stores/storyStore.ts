// src/stores/storyStore.ts

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { Story, Turn, Snapshot } from "@/types";
import axios from "axios";

export const useStoryStore = defineStore("story", () => {
  // --- State ---
  const currentStoryId = ref<string>("");
  const turns = ref<Turn[]>([]);
  
  // Time Travel: History & Future stacks for Undo/Redo (Linear edits)
  // Note: "Forking" is different from Undo. Forking creates a NEW story.
  // Undo/Redo is for local unsaved edits or navigating the current linear stream.
  // For V3 Folded Tree, we might not need "undo" as much as "forking".
  // But let's keep basic structure.

  // The "Folded Tree" is actually managed by the Backend via parent_story_id.
  // Frontend mostly sees the "Linear Projection" of the current branch.
  // However, `turns` might contain `snapshot` data, allowing us to see "what could have been".

  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // --- Getters ---
  const turnCount = computed(() => turns.value.length);
  const lastTurn = computed(() => turns.value[turns.value.length - 1]);

  // --- Actions ---

  /**
   * Initialize or Fetch a story
   */
  async function fetchStory(storyId: string) {
    if (!storyId) return;
    isLoading.value = true;
    error.value = null;
    try {
      const resp = await axios.get<Story>(`/api/story/${storyId}`);
      currentStoryId.value = resp.data.story_id;
      turns.value = resp.data.turns;
    } catch (e: any) {
      error.value = e.message || "Failed to fetch story";
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Create a fresh story
   */
  async function createStory() {
    isLoading.value = true;
    try {
      const resp = await axios.post<{ story_id: string }>("/api/story/create");
      currentStoryId.value = resp.data.story_id;
      turns.value = [];
      return resp.data.story_id;
    } catch (e: any) {
      error.value = "Create failed";
      return null;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Append a turn (User or AI choice)
   */
  async function appendTurn(turn: { text: string; author: "human" | "ai"; snapshot?: Snapshot }) {
    if (!currentStoryId.value) return;
    try {
      // Optimistic update? Maybe risky if backend logic is complex (scoring).
      // Let's wait for backend.
      const resp = await axios.post<Story>("/api/story/append", {
        story_id: currentStoryId.value,
        text: turn.text,
        author: turn.author,
        snapshot: turn.snapshot
      });
      // Update full list to ensure scores/coords are synced
      turns.value = resp.data.turns;
    } catch (e: any) {
      error.value = "Append failed: " + e.message;
      throw e;
    }
  }

  /**
   * Fork / Branch (Time Travel)
   * @param sourceTurnIndex The 0-based index of the turn to SPLIT AFTER (or replace?)
   * Using "replace" logic: We go back to turn N, and choose a diff option.
   * So we want history 0..N-1, and append new Option.
   * The backend `api_branch_story` expects `source_turn_id` (1-based usually).
   */
  async function forkStory(sourceTurnIndex: number) {
     if (!currentStoryId.value) return;
     isLoading.value = true;
     try {
         // Backend expects 1-based "count" to keep?
         // If I want to keep turns 0, 1, 2 (User clicks fork on turn 3),
         // source_turn_id should be 3 ?
         // Let's assume backend logic: "slice upto source_turn_id".
         
         const resp = await axios.post<{ story_id: string }>("/api/story/branch", {
             parent_story_id: currentStoryId.value,
             source_turn_id: sourceTurnIndex // Verify backend logic!
         });
         
         const newId = resp.data.story_id;
         // Switch to new story
         await fetchStory(newId);
         return newId;
     } catch (e: any) {
         error.value = "Fork failed";
         throw e;
     } finally {
         isLoading.value = false;
     }
  }

  // --- Tree State ---
  const treeData = ref<{ nodes: any[], links: any[] }>({ nodes: [], links: [] });

  // --- Actions ---

  /**
   * Fetch the scoped multiverse tree for a specific story
   */
  async function fetchAllStories(storyId?: string, showAll: boolean = false) {
    try {
      const params: any = {};
      if (storyId) params.story_id = storyId;
      if (showAll) params.show_all = true;

      const resp = await axios.get("/api/story/tree", { params });
      treeData.value = resp.data;
    } catch (e) {
      console.error("Failed to fetch tree", e);
    }
  }

  return {
    currentStoryId,
    turns,
    treeData, // Export treeData
    isLoading,
    error,
    turnCount,
    lastTurn,
    fetchStory,
    fetchAllStories, // Export action
    createStory,
    appendTurn,
    forkStory
  };
});
