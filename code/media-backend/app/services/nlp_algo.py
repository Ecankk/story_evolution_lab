from typing import Dict, List, Tuple
import jieba.posseg as pseg
from snownlp import SnowNLP
from scipy.spatial.distance import cosine
import numpy as np
import re

# 预定义的五感词库 (简化版)
SENSORY_WORDS = {
    # 视觉 (Visual): 颜色、光影、动作观察
    "visual": {"看", "见", "红", "蓝", "绿", "紫", "黄", "黑", "白", "灰", "金", "银", 
               "闪", "光", "瞥", "视", "影", "亮", "暗", "漆", "彩", "斑", "驳", "耀", "晃"},
    # 听觉 (Auditory): 声音、动静
    "auditory": {"听", "响", "声", "闹", "静", "吼", "唱", "鸣", "耳", "音", "吵", "喊", "叫", 
                 "嗡", "吟", "啸", "喧", "哗", "隆", "嚓", "哑", "脆"},
    # 嗅觉 (Olfactory): 气味
    "olfactory": {"香", "臭", "味", "鼻", "嗅", "腥", "馥", "芬", "霉", "焦", "薰", "呛", "酸腐"},
    # 味觉 (Gustatory): 口感、味道
    "gustatory": {"甜", "苦", "辣", "咸", "酸", "尝", "吃", "喝", "润", "涩", "腻", "淡", "鲜"},
    # 触觉 (Tactile): 温度、质感、身体感觉 (Updated: Removed '虽然' bug, added '感', '觉', '触')
    "tactile": {"冷", "热", "痛", "痒", "硬", "软", "滑", "粗", "摸", "触", "疼", "凉", "温", 
                "糙", "腻", "湿", "干", "刺", "灼", "冰", "暖", "抚", "揉", "擦"}
}

def analyze_sentiment(text: str) -> float:
    """
    返回情感极性: -1.0 (极负面) ~ 1.0 (极正面)
    SnowNLP 默认是 0~1，我们需要映射一下并校准。
    SnowNLP 训练数据偏电商，对小说可能不准，需要后续微调。
    这里做一个简单的线性映射: (score - 0.5) * 2
    """
    if not text.strip():
        return 0.0
    try:
        s = SnowNLP(text)
        # SnowNLP output is probability 0..1
        raw = s.sentiments
        # Map 0..1 to -1..1
        return round((raw - 0.5) * 2, 4)
    except:
        return 0.0

def analyze_style(text: str) -> Dict[str, float]:
    """
    分析文笔风格指标
    1. show_dont_tell_score: (动词+名词) / (形容词+副词)。越高越好(画面感强)。
    2. sensory_density: 感官词密度
    """
    if not text:
        return {"show_ratio": 0.0, "adj_density": 0.0, "sensory_score": 0.0}

    words = pseg.cut(text)
    
    count_v = 0 # 动词
    count_n = 0 # 名词
    count_adj = 0 # 形容词 (a)
    count_adv = 0 # 副词 (d)
    
    sensory_hits = 0
    total_words = 0
    
    for w, flag in words:
        total_words += 1
        
        # 词性统计
        if flag.startswith('v'): count_v += 1
        elif flag.startswith('n'): count_n += 1
        elif flag.startswith('a'): count_adj += 1
        elif flag.startswith('d'): count_adv += 1
        
        # 感官词匹配 (简单字符匹配)
        for sense, keywords in SENSORY_WORDS.items():
            # 检查词中是否包含感官字 (heuristic)
            if any(k in w for k in keywords):
                sensory_hits += 1
                break
                
    # Calculated Metrics
    
    # 1. Show Don't Tell Ratio
    # 避免除以零
    denominator = count_adj + count_adv
    if denominator == 0:
        show_ratio = 5.0 # 极高
    else:
        show_ratio = (count_v + count_n) / denominator
        
    # 2. Adjective Density (for warning)
    adj_density = count_adj / total_words if total_words > 0 else 0
    
    # 3. Sensory Score (Scaled)
    # 原始密度通常很低 (<0.1)，我们需要扩大数值以便于 UI 展示 (0~5 range)
    # Multiply by 10 means: 5% sensory words => Score 0.5 => 50% UI Bar
    sensory_score = (sensory_hits / total_words) * 10 if total_words > 0 else 0
    
    return {
        "show_ratio": round(show_ratio, 2),
        "adj_density": round(adj_density, 3), # > 0.15 might be warning
        "sensory_score": round(sensory_score, 3)
    }

def check_ooc_score(current_emb: List[float], history_embs: List[List[float]]) -> float:
    """
    计算 OOC (Out of Character) 分数
    返回: 相似度 0~1。越低越 OOC。
    """
    if not history_embs or not current_emb:
        return 1.0 # 默认一致
        
    # 计算历史平均指纹
    matrix = np.array(history_embs)
    fingerprint = np.mean(matrix, axis=0)
    
    sim = 1 - cosine(current_emb, fingerprint)
    return float(sim)
