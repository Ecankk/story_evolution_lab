# StoryFlow Data Schema Reference

本文档总结了项目中的核心数据格式，分为 **原始处理数据 (Raw Processed Data)** 和 **前端可视化数据 (Web Visualization Data)** 两部分。

## 1. 原始处理数据 (`experiment_embeddings.json`)

**用途**: 存储完整的实验记录、文本内容以及高维 Embedding 向量。这是数据的"源头"，包含了所有细节。

**文件路径示例**: `data/1/experiment_embeddings.json`

```json
{
  "experiment_name": "实验1a-修改-优化",
  "embeddings_provider": "sentence-transformers/...", // 使用的模型名称
  "embeddings_dimension": 384, // 向量维度
  "experiment_data": {
    "GroupID_01": { // Key: 组号或唯一标识
      "student_id": "123456",
      "name": "张三",
      
      // --- 起点 (Root) ---
      "original_sentence": "这里是原始的输入文本...",
      "original_embedding": [0.123, -0.456, ...], // 384维向量

      // --- 过程 (Trajectory) ---
      "modification_rounds": [
        {
          "round": 1, // 轮次
          "random_modification": "AI生成的随机扰动文本...",
          "optimized_result": "人类或AI优化后的结果文本...",
          
          // 核心数据：用于计算位置
          "random_mod_embedding": [...], 
          "optimized_embedding": [...],

          // 预计算指标 (当前定义：与"原句"的对比)
          "smoothness_metrics": {
            "cosine_similarity": 0.85, // 语义相似度 (越高越像原句)
            "euclidean_distance": 1.23, // 欧氏距离
            "semantic_deviation": 0.15  // 偏差度 (1 - similarity)
          }
        },
        // ... 更多轮次
      ]
    }
  }
}
```

### 字段解析
- **Embedding (`[...]`)**: 核心资产。这些高维向量是计算"语义距离"和"降维坐标"的基础。只要有这些向量，前端/后端可以随时重新计算 Flow 或 Entropy，而无需依赖预计算的 `smoothness_metrics`。
- **Smoothness Metrics**: 目前计算的是 **当前轮 vs 原句** 的相似度。如果需要计算 **相邻轮次 (Step N vs Step N-1)** 的连贯性 (Flow)，建议在读取时实时计算，或直接用坐标距离近似。

---

## 2. 前端可视化数据 (`web_visualization_data.json`)

**用途**: 经过 PCA 降维后的轻量级数据，专门用于前端 ECharts 绘制"语义河流图" (Semantic River)。

**文件路径示例**: `data/1/web_visualization_data.json` (或 `story/web_visualization_data.json`)

```json
{
  "GroupID_01": [ // 一个ID对应一条完整的时间线/折线
    {
      "step": 0,
      "text": "原始文本...",
      "x": 0.12,  // PCA 降维后的 X 坐标
      "y": -0.56, // PCA 降维后的 Y 坐标
      "flow": 1.0, // 初始节点的 Flow 默认为 1
      "type": "original" // 节点类型：original / optimized / ai_noise
    },
    {
      "step": 1,
      "text": "第一轮优化文本...",
      "x": 0.15,
      "y": -0.48,
      "flow": 0.85, // 这一步的"语义连贯性" (亦可表示颜色深浅或光晕大小)
      "type": "optimized"
    },
    {
      "step": 2,
      "text": "第二轮优化文本...",
      "x": 0.22,
      "y": -0.40,
      "flow": 0.82,
      "type": "optimized"
    }
    // ... 形成一条连续的轨迹
  ],
  "GroupID_02": [ ... ]
}
```

### 字段意义与可视化映射
| 字段 | 意义 | 前端可视化建议 (Cyberpunk 风格) |
| :--- | :--- | :--- |
| **Key (GroupID)** | 唯一的故事线标识 | **Series**: 每一个 Key 对应 ECharts 里的一条 `line` 系列。 |
| **x, y** | 语义空间坐标 | **Position**: 点在二维平面上的位置。相近的点表示语义相似。 |
| **step** | 时间/逻辑顺序 | **Sequence**: 连接点的顺序。必须按 Step 0 -> 1 -> 2 连接。 |
| **flow** | 连贯性/相似度 | **Visual Cue**: 可映射为**线条的透明度**、**发光强度**或**点的半径**。Flow 越高，光越强。 |
| **type** | 节点类型 | **Symbol**: 可映射为不同的形状 (如：原句=实心圆，优化=空心圆，变异=三角形)。 |

---

## 3. 分析与结论

1.  **结构合理性**:
    *   当前的 JSON 结构清晰地区分了"重数据"(Embedding)和"轻数据"(XY坐标)，非常适合 Web 开发。后端负责繁重的 PCA 计算，前端直接使用渲染好的 XY 坐标，性能最优。

2.  **对"连续性"的支持**:
    *   `web_visualization_data.json` 的 `List` 结构天然就是有序的。
    *   前端 ECharts 的 `line` 图表接收的就是这种数组格式，因此你可以直接画出一条条"在语义空间中游走的折线"。

3.  **对"创意熵"的潜在支持**:
    *   虽然 JSON 里没有直接叫 `entropy` 的字段，但 `x, y` 本身就代表了位置。
    *   **创意熵 (Creativity Entropy)** 可以理解为**轨迹的跳跃幅度**。如果不希望仅仅展示一条平滑的线，可以通过计算相邻两点 `(x, y)` 的距离，如果距离突然变大，说明"创意跳跃/熵增"，可以在视觉上表现为线条颜色的突变（如：由蓝变红）。

**总结**: 这套数据格式完全满足"语义空间折线图"的需求，无需修改结构，直接开始前端可视化开发即可。
