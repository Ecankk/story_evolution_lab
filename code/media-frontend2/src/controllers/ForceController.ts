import * as d3 from 'd3-force';

// Simple EventEmitter replacement for browser
class SimpleEventEmitter {
    private events: Record<string, Function[]> = {};

    on(event: string, listener: Function) {
        if (!this.events[event]) this.events[event] = [];
        this.events[event].push(listener);
        return this;
    }

    emit(event: string, ...args: any[]) {
        if (!this.events[event]) return false;
        this.events[event].forEach(listener => listener(...args));
        return true;
    }
}

export interface GameNode {
    id: string;
    text: string;
    type: 'start' | 'end' | 'guess';
    x?: number;
    y?: number;
    fx?: number | null;
    fy?: number | null;
    status?: 'confirmed' | 'rejected' | 'uncertain';
    score?: number; // 0-1 continuous score
}

export interface GameLink {
    source: string | GameNode;
    target: string | GameNode;
    value: number;
}

export class ForceController extends SimpleEventEmitter {
    simulation: d3.Simulation<GameNode, GameLink>;
    nodes: GameNode[] = [];
    links: GameLink[] = [];
    width: number = 800;
    height: number = 600;

    constructor(w: number, h: number) {
        super();
        this.width = w;
        this.height = h;

        this.simulation = d3.forceSimulation<GameNode>(this.nodes)
            .force("link", d3.forceLink<GameNode, GameLink>(this.links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(w / 2, h / 2))
            .force("collide", d3.forceCollide().radius(40));

        this.simulation.on("tick", () => {
            this.emit("tick", this.nodes, this.links);
        });
    }

    init(startText: string, endText: string) {
        this.nodes = [
            { id: "start", text: startText, type: 'start', fx: this.width * 0.2, fy: this.height / 2 },
            { id: "end", text: endText, type: 'end', fx: this.width * 0.8, fy: this.height / 2 }
        ];
        this.links = []; // No direct link initially? Or maybe a weak one.
        this.restart();
    }

    addGuess(text: string) {
        const id = `guess_${Date.now()}`;
        const newNode: GameNode = { 
            id, 
            text, 
            type: 'guess', 
            x: this.width / 2, 
            y: this.height / 2,
            fx: this.width / 2, // Fix position immediately
            fy: this.height / 2
        };
        this.nodes.push(newNode);
        this.restart();
        return newNode;
    }

    updateFeedback(nodeId: string, status: 'confirmed' | 'rejected' | 'uncertain') {
        const node = this.nodes.find(n => n.id === nodeId);
        if (node) {
            node.status = status;
            // Update visual or physics based on status?
            // E.g. confirmed nodes might be linked to End?
        }
    }

    restart() {
        this.simulation.nodes(this.nodes);
        (this.simulation.force("link") as d3.ForceLink<GameNode, GameLink>).links(this.links);
        this.simulation.alpha(1).restart();
    }

    // Interaction Helpers
    dragStart(node: GameNode) {
        this.simulation.alphaTarget(0.3).restart();
        node.fx = node.x;
        node.fy = node.y;
    }

    drag(node: GameNode, x: number, y: number) {
        node.fx = x;
        node.fy = y;
    }

    dragEnd(node: GameNode) {
        this.simulation.alphaTarget(0);
        // Leave fixed if we want manual positioning to persist
        // node.fx = null; 
        // node.fy = null;
        this.emit("nodeDragEnd", node);
    }
    
    resize(w: number, h: number) {
        this.width = w;
        this.height = h;
        this.simulation.force("center", d3.forceCenter(w / 2, h / 2));
        
        // Re-fix start/end
        const start = this.nodes.find(n => n.type === 'start');
        if (start) { start.fx = w * 0.2; start.fy = h / 2; }
        
        const end = this.nodes.find(n => n.type === 'end');
        if (end) { end.fx = w * 0.8; end.fy = h / 2; }
        
        this.simulation.alpha(1).restart();
    }

    // --- Persistence ---
    private STORAGE_KEY = 'turtle_soup_session';

    saveSession() {
        try {
            const data = {
                nodes: this.nodes.map(n => ({
                    ...n,
                    fx: n.fx, // Keep fixed positions
                    fy: n.fy
                })),
                timestamp: Date.now()
            };
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
        } catch (e) {
            console.error("Failed to save session", e);
        }
    }

    loadSession(): boolean {
        try {
            const raw = localStorage.getItem(this.STORAGE_KEY);
            if (!raw) return false;
            const data = JSON.parse(raw);
            if (!data.nodes || !Array.isArray(data.nodes)) return false;

            // Restore nodes
            this.nodes = data.nodes;
            this.links = []; // Rebuild links if we tracked them, currently we don't strictly track structural links for soup
            
            // Restart simulation
            this.restart();
            return true;
        } catch (e) {
            console.error("Failed to load session", e);
            return false;
        }
    }

    clearSession() {
        localStorage.removeItem(this.STORAGE_KEY);
    }
}
