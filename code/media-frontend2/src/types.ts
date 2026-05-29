// src/types.ts

export type Author = "human" | "ai";

export interface TurnOption {
  id: string; // unique option id
  title: string;
  preview: string;
  full_text?: string;
  tags: string[];
}

export interface Snapshot {
    intent: string;
    seed: string;
    choices: TurnOption[]; // All generated options at this point
    selected: string; // The ID of the option that was actually chosen (lead to the current turn)
}

export interface Turn {
    story_id: string;
    turn: number; // 1-based index
    author: Author;
    text: string;
    
    // Metrics
    flow_score: number;
    entropy_score: number;
    tension_score?: number;
    semantic_drift?: number;
    
    // NLP Analysis
    sentiment_score?: number;
    show_ratio?: number;
    adj_density?: number;
    sensory_score?: number;
    ooc_score?: number;

    // Visual Coords (PCA)
    x?: number;
    y?: number;
    
    // Editor visual rendering
    content_html?: string;

    // Multiverse Metadata
    snapshot?: Snapshot; // If this turn was chosen from a set of options
    
    // Turtle Soup
    weight: number; // Default 1.0
}

export interface Story {
    story_id: string;
    turns: Turn[];
    metadata?: {
        parent_story_id?: string;
        source_turn_id?: number;
        [key: string]: any;
    };
}
