from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any

# Author 是一个类型别名：只允许 "human" 或 "ai"
Author = Literal["human", "ai"]

class TurnOption(BaseModel):
    id: str  # unique option id
    title: str
    preview: str
    full_text: Optional[str] = None
    tags: List[str] = []

class Turn(BaseModel):
    """
    表示“单个回合/单条 turn”的完整数据结构。
    """
    story_id: str
    turn: int
    author: Author
    text: str
    
    # 指标
    flow_score: float = 0.0
    entropy_score: float = 0.0
    
    # 情感/张力 (V3 Pulse Tab)
    tension_score: float = 0.0
    sentiment_score: float = 0.0 # Added

    # 深度文学分析 (V4.5)
    show_ratio: float = 0.0
    adj_density: float = 0.0
    sensory_score: float = 0.0
    ooc_score: float = 0.0
    semantic_drift: float = 0.0

    # PCA 语义空间坐标
    x: Optional[float] = None
    y: Optional[float] = None
    
    content_html: Optional[str] = None

    # V3 Multiverse: Snapshot of rejected options
    # { "intent": str, "seed": str, "choices": [Option...], "selected": str }
    snapshot: Optional[Dict[str, Any]] = None
    
    # V3 Turtle Soup: Gravity weight
    weight: float = 1.0


class CreateStoryResp(BaseModel):
    story_id: str

class ContinueReq(BaseModel):
    story_id: str
    user_text: str = ""
    rounds: int = Field(default=1, ge=1, le=10)
    mode: str = "human_ai"

class ContinueResp(BaseModel):
    story_id: str
    new_turns: List[Turn]

class StoryResp(BaseModel):
    story_id: str
    turns: List[Turn]
    metadata: Optional[Dict[str, Any]] = {} # e.g. parent_id, source_turn_id

class CompareResp(BaseModel):
    story_id: str
    points: List[Turn]

class UpdateReq(BaseModel):
    story_id: str
    turn_index: int
    new_text: str

class DeleteReq(BaseModel):
    story_id: str
    turn_index: int

class AnalyzeReq(BaseModel):
    text: str

class AnalyzeResp(BaseModel):
    segments: List[Turn]

class RefineReq(BaseModel):
    text: str
    context_pre: Optional[str] = ""
    context_post: Optional[str] = ""
    type: str # 'polish' | 'elevate'

class RefineResp(BaseModel):
    new_text: str

class SyncTurn(BaseModel):
    text: str
    author: Author
    content_html: Optional[str] = None

class SyncReq(BaseModel):
    story_id: str
    turns: List[SyncTurn]

# V3 New Schemas
class SuggestReq(BaseModel):
    story_id: str
    context_text: str # explicit context or use backend history
    intent: str
    seed: str

class SuggestResp(BaseModel):
    options: List[TurnOption]

class BranchReq(BaseModel):
    parent_story_id: str
    source_turn_id: int # split after this turn index
    selected_option_index: Optional[int] = None # if branching from a specific option choice

class AppendReq(BaseModel):
    story_id: str
    text: str
    author: Author = "ai"
    snapshot: Optional[Dict[str, Any]] = None

class TreeNode(BaseModel):
    id: str
    label: str
    group: int = 1
    parent: Optional[str] = None
    preview: str = ""

class TreeLink(BaseModel):
    source: str
    target: str

class TreeResp(BaseModel):
    nodes: List[TreeNode]
    links: List[TreeLink]
