import os
import joblib
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine, euclidean
import numpy as np

# 全局单例模型
print("⏳ [Algo] 正在加载 Embedding 模型...")
try:
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    print("✅ [Algo] Embedding 模型加载完毕！")
except Exception as e:
    print(f"❌ [Algo] Embedding 模型加载失败: {e}")
    model = None

# 全局 PCA 模型
pca_model = None
try:
    # 尝试加载 PCA 模型
    # algo.py 在 app/utils/
    # analysis.py 保存到了 data/ (也就是 media-backend/data)
    # 所以我们要往上跳两级: utils -> app -> media-backend -> data
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    pca_path = os.path.join(current_dir, '..', '..', 'data', 'pca_model.pkl') 
    pca_path = os.path.abspath(pca_path)
    
    if os.path.exists(pca_path):
        pca_model = joblib.load(pca_path)
        print(f"✅ [Algo] PCA 模型加载完毕: {pca_path}")
    else:
        print(f"⚠️ [Algo] PCA 模型未找到: {pca_path}")
except Exception as e:
    print(f"❌ [Algo] PCA 模型加载失败: {e}")

def get_embedding(text: str) -> list:
    """获取单个文本的向量"""
    if not model or not text:
        return []
    return model.encode(text).tolist()

def calculate_metrics(current_text: str, context_vectors: list):
    """
    计算 Flow, Entropy 以及 PCA 坐标 (x, y)
    """
    if not model:
        return {
            "embedding": [], "flow_score": 0.0, "entropy_score": 0.0,
            "x": 0.0, "y": 0.0
        }

    # 1. 计算当前向量
    current_emb = model.encode(current_text).tolist()
    
    flow_score = 1.0
    entropy_score = 0.0
    
    if context_vectors and len(context_vectors) > 0:
        last_emb = context_vectors[-1]
        sim = 1 - cosine(current_emb, last_emb)
        flow_score = max(0.0, float(sim))
        
        # Entropy: Distance to the Centroid (Mean of Context)
        context_matrix = np.array(context_vectors)
        centroid = np.mean(context_matrix, axis=0)
        dist = euclidean(current_emb, centroid)
        entropy_score = min(1.0, dist / 10.0)

        # Drift: Distance from the Origin (First sentence)
        origin_emb = context_vectors[0]
        drift_dist = euclidean(current_emb, origin_emb)
        # Normalize: assumes 15.0 is max expected drift
        semantic_drift = min(1.0, drift_dist / 15.0)
    else:
        # First sentence has 0 drift
        semantic_drift = 0.0
        
    # Tension: Heuristic (Short sentences + Exclamation marks = High Tension)
    # 1. Length Factor: Shorter is higher tension. (Normalize 10-100 chars)
    length = len(current_text)
    len_score = max(0.0, 1.0 - (length / 80.0))
    
    # 2. Punctuation Factor: ! and ? add tension
    punct_count = current_text.count('！') + current_text.count('!') + current_text.count('？') + current_text.count('?')
    punct_score = min(0.5, punct_count * 0.1)
    
    tension_score = min(1.0, len_score + punct_score)

    # 2. 计算 PCA 坐标
    x, y = 0.0, 0.0
    if pca_model:
        try:
            # transform expects 2D array
            coords = pca_model.transform([current_emb])
            x = float(coords[0][0])
            y = float(coords[0][1])
        except Exception as e:
            print(f"PCA Transform error: {e}")

    return {
        "embedding": current_emb,
        "flow_score": round(flow_score, 4),
        "entropy_score": round(entropy_score, 4),
        "tension_score": round(tension_score, 4),
        "semantic_drift": round(semantic_drift, 4),
        "x": round(x, 3), 
        "y": round(y, 3)
    }
