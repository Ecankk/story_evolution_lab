from fastapi import APIRouter, HTTPException
import json
import numpy as np  # ⚠️ 这里目前没用到，可以删（不影响功能）
from pathlib import Path
from sklearn.decomposition import PCA

router = APIRouter()

@router.get("/all-data")
def get_analysis_data():
    """
    动态获取所有实验数据（用于分析/可视化）

    主要流程：
    1) 扫描 data 目录下所有 *.json 文件（跳过 stories.json）
    2) 合并每个文件里的 content["data"] 到 merged_data["data"]
    3) 从 merged_data["data"] 里抽取 embedding 向量列表 all_vectors
    4) 实时运行 PCA 把 embedding 降到 2 维 -> coords
    5) 将 coords 回填到对应 round 里，写入 x/y
    6) 返回 merged_data（包含所有故事/回合以及它们的 x/y）
    """

    # data_dir 指向项目根目录的 data 文件夹：
    # Path(__file__).resolve() -> 当前文件绝对路径
    # parent.parent.parent -> 往上 3 层（routes -> app -> backend? 视目录结构）
    # / "data" -> 拼成 data 目录
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"

    # merged_data 最终返回的数据结构：
    # {
    #   "experiment_name": "Merged Analysis",
    #   "data": {
    #       "<story_id>": { ...story_obj... },
    #       ...
    #   }
    # }
    merged_data = {
        "experiment_name": "Merged Analysis",
        "data": {}
    }

    # 如果 data 目录不存在，直接 404
    if not data_dir.exists():
         raise HTTPException(status_code=404, detail="Data directory not found")

    # 1) 扫描 data 目录里所有 json 文件
    # 注意：这里是 *.json 全扫，所以只要 data 目录里有其它 json 也会读进来
    json_files = list(data_dir.glob("*.json"))

    for jf in json_files:
        # 跳过 stories.json（这通常是“主故事库”）
        if jf.name == "stories.json":
            continue

        try:
            # 读取 json 文件内容
            with open(jf, "r", encoding="utf-8") as f:
                content = json.load(f)

                # 只合并 content["data"]，并且必须是 dict
                # update() 会覆盖同 key 的数据（后读到的覆盖先读到的）
                if "data" in content and isinstance(content["data"], dict):
                    merged_data["data"].update(content["data"])
        except Exception as e:
            # 读取某个文件失败不会中断整体，只打印警告
            print(f"⚠️ Failed to load {jf}: {e}")

    # 2) 准备 PCA 输入数据
    all_vectors = []   # 用于 PCA 的 embedding 向量列表
    vector_map = []    # 用于把 PCA 输出 coords 映射回原数据的位置 (story_id, round_idx)

    # has_data 用来确保真的有 embedding 才跑 PCA
    has_data = False

    # merged_data["data"] 的预期结构：
    # merged_data["data"][sid] = story_obj
    # story_obj 里应该有 "rounds": [turn0, turn1, ...]
    for sid, story_obj in merged_data["data"].items():
        if "rounds" not in story_obj:
            continue

        for idx, turn in enumerate(story_obj["rounds"]):
            # 每个 turn 预计是 dict
            # turn.get("embedding") 是一个向量（list[float]）
            emb = turn.get("embedding")

            # 只要 emb 存在且长度>0，就加入 PCA 输入
            if emb and len(emb) > 0:
                all_vectors.append(emb)
                vector_map.append((sid, idx))
                has_data = True

    # 3) 运行 PCA
    # 需要至少 3 条向量才有意义（你这里是 >2）
    if has_data and len(all_vectors) > 2:
        try:
            # PCA 降到 2 维
            pca = PCA(n_components=2)
            coords = pca.fit_transform(all_vectors)  # coords shape: (N, 2)

            # --- 关键修改：保存 PCA 模型 ---
            # 目的是：让后续坐标系一致（否则每次重新 fit 坐标系都会变）
            import joblib
            pca_save_path = data_dir / "pca_model.pkl"
            joblib.dump(pca, pca_save_path)
            print(f"✅ PCA Model updated and saved to: {pca_save_path}")

            # 4) 回填坐标
            # coords 的第 i 行对应 all_vectors[i]
            # vector_map[i] 记录它来自哪个 story_id 的哪个 round_idx
            for i, (x, y) in enumerate(coords):
                sid, ridx = vector_map[i]

                # 把 x/y 写回 merged_data 的对应 round 中
                merged_data["data"][sid]["rounds"][ridx]["x"] = round(float(x), 3)
                merged_data["data"][sid]["rounds"][ridx]["y"] = round(float(y), 3)

                # 可选：为了减少 payload，不把 embedding 发给前端
                # merged_data["data"][sid]["rounds"][ridx].pop("embedding", None)

        except Exception as e:
            print(f"❌ PCA Analysis Failed: {e}")

    # 返回给前端（包含 merged 的所有数据 + x/y）
    return merged_data
