from typing import Dict, List
from app.utils import algo
from app.services.storage import get_story_turns

def _clamp01(x: float) -> float:
    if x < 0: return 0.0
    if x > 1: return 1.0
    return x

def score_turns(story_id: str, new_turns: List[Dict]) -> List[Dict]:
    """
    使用 algo.py 计算真实的 Flow & Entropy
    """
    # 1. 获取该故事的所有历史 turns (为了拿到上下文向量)
    history_turns = get_story_turns(story_id) or []
    
    # 提取所有历史的 embedding (如果有的话)
    context_vectors = []
    for t in history_turns:
        if t.get("embedding"):
            context_vectors.append(t["embedding"])
    
    scored_result = []
    
    # 2. 逐条计算新生成的 turn
    for t in new_turns:
        text = (t.get("text") or "").strip()
        
        # 调用核心算法
        metrics = algo.calculate_metrics(text, context_vectors)
        
        # 调用 NLP 算法 (Phase 4.5)
        # TODO: Move import to top-level if stable
        from app.services import nlp_algo
        
        sentiment = nlp_algo.analyze_sentiment(text)
        style = nlp_algo.analyze_style(text)
        # OOC requires full history embeddings (context_vectors)
        # check_ooc_score needs List[List[float]]
        ooc = nlp_algo.check_ooc_score(metrics["embedding"], context_vectors)
        
        # 组装结果
        t2 = dict(t)
        t2["flow_score"] = metrics["flow_score"]
        t2["entropy_score"] = metrics["entropy_score"]
        t2["tension_score"] = metrics.get("tension_score", 0.0)
        t2["semantic_drift"] = metrics.get("semantic_drift", 0.0)
        t2["embedding"] = metrics["embedding"] # 存库
        
        # 新增 NLP 指标
        t2["sentiment_score"] = sentiment
        t2["show_ratio"] = style["show_ratio"]
        t2["adj_density"] = style["adj_density"]
        t2["sensory_score"] = style["sensory_score"]
        t2["ooc_score"] = round(ooc, 4)
        
        # 新增可视化坐标
        t2["x"] = metrics.get("x", 0.0)
        t2["y"] = metrics.get("y", 0.0)
        
        # [DEBUG] Log to file for verification
        try:
            import json
            import time
            # Force absolute path to avoid cwd issues
            log_path = r"d:/STUDY/SchoolLearning/level3/Interactive_media_technology/lab/media/code/media-backend/metrics.log"
            log_entry = {
                "timestamp": time.time(),
                "text": text[:20] + "...",
                "sentiment": sentiment,
                "tension": t2["tension_score"],
                "show_ratio": style["show_ratio"],
                "sensory": style["sensory_score"]
            }
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
                f.flush()
        except Exception as e:
            pass # Silent fail if still permission issue

        # 将当前向量加入上下文
        if metrics["embedding"]:
            context_vectors.append(metrics["embedding"])
            
        scored_result.append(t2)
        
    return scored_result

def recalculate_story_metrics(turns: List[Dict]) -> List[Dict]:
    """
    全量重算故事的所有指标。
    针对“编辑器”场景优化的算法：
    1. 修改句子的 Flow = (与上句相似度 + 与下句相似度) / 2 (已由前端触发修改，这里全量算)
    2. Entropy = 到历史重心的距离 (全量重算以保证准确)
    """
    from scipy.spatial.distance import cosine, euclidean
    import numpy as np
    
    if not turns:
        return []

    # 1) 首先提取/重算所有 embedding (如果文本变了)
    # 为了简化，我们假设 text 变了 embedding 就得重算
    # 这里我们直接调用 algo.get_embedding
    updated_turns = []
    context_vectors = []
    
    for t in turns:
        t2 = dict(t)
        # 重新获取 embedding
        t2["embedding"] = algo.get_embedding(t2["text"])
        updated_turns.append(t2)

    # 2) 重新计算 Flow 和 Entropy
    for i, t in enumerate(updated_turns):
        emb = t["embedding"]
        
        # --- Flow 计算 (编辑器特殊逻辑) ---
        if i == 0:
            flow_score = 1.0 # 第一句默认 1.0
        elif i == len(updated_turns) - 1:
            # 最后一句：只算跟上一句的
            prev_emb = updated_turns[i-1]["embedding"]
            flow_score = 1 - cosine(emb, prev_emb)
        else:
            # 中间句：取前后相似度的平均值 (User 要求)
            prev_emb = updated_turns[i-1]["embedding"]
            next_emb = updated_turns[i+1]["embedding"]
            sim_prev = 1 - cosine(emb, prev_emb)
            sim_next = 1 - cosine(emb, next_emb)
            flow_score = (sim_prev + sim_next) / 2
        
        # --- Entropy 计算 (对齐当前重心) ---
        entropy_score = 0.0
        if i > 0:
            # 计算到之前所有句子的重心距离
            history_matrix = np.array(context_vectors)
            centroid = np.mean(history_matrix, axis=0)
            dist = euclidean(emb, centroid)
            entropy_score = min(1.0, dist / 10.0)
        
        # --- PCA 坐标 ---
        # 也要重算坐标，保证图表点对齐
        metrics = algo.calculate_metrics(t["text"], context_vectors)
        
        # --- NLP Phase 4.5 ---
        from app.services import nlp_algo
        sentiment = nlp_algo.analyze_sentiment(t["text"])
        style = nlp_algo.analyze_style(t["text"])
        ooc = nlp_algo.check_ooc_score(emb, context_vectors)
        
        t["flow_score"] = round(float(flow_score), 4)
        t["entropy_score"] = round(float(entropy_score), 4)
        t["tension_score"] = metrics.get("tension_score", 0.0)
        t["semantic_drift"] = metrics.get("semantic_drift", 0.0)
        t["x"] = metrics.get("x", 0.0)
        t["y"] = metrics.get("y", 0.0)
        
        # NLP
        t["sentiment_score"] = sentiment
        t["show_ratio"] = style["show_ratio"]
        t["adj_density"] = style["adj_density"]
        t["sensory_score"] = style["sensory_score"]
        t["ooc_score"] = round(ooc, 4)
        
        # 加入上下文供下一句 Entropy 使用
        context_vectors.append(emb)

    return updated_turns
