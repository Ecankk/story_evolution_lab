# Story Evolution Lab

基于大语言模型的互动叙事演化实验平台。支持人机协同故事接龙、语义流/创意熵实时可视化、海龟汤推理游戏、以及群体演化与遗传算法实验。

## 功能说明

### 1. 多维工作台 (Workbench)

实时人机共创故事，可视化叙事指标：

- **语义流 (Semantic Flow)**：衡量故事连贯性（当前句与前句的语义相似度）
- **创意熵 (Creative Entropy)**：衡量故事跳跃性/创新度（当前句偏离历史语义重心的距离）
- **语义空间轨迹图**：通过 PCA 降维展示叙事在语义空间中的移动路径
- **WebSocket 实时流式**：AI 生成内容逐字推送，图表实时更新

### 2. 海龟汤游戏 (Turtle Soup)

AI 扮演侦探，通过封闭式提问推理故事真相：

- 玩家提供故事的【起因】和【结果】
- AI 侦探提出封闭式问题（是/否）验证猜想
- 系统根据语义相似度自动判定答案反馈
- 侦探掌握全貌后以 `[SOLVED]` 标记还原真相

### 3. 群体与遗传实验 (Group / Genetic Evolution)

支持多种故事演化实验模式：

- **单体演化**：单句反复改写，观察语义漂移
- **群体演化**：多路径并行演化，对比不同走向
- **遗传算法**：选择-交叉-变异，迭代优化故事

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + Python 3.11 |
| 前端 | Vue 3 + Vite + TypeScript + Tailwind CSS |
| 状态管理 | Pinia |
| 可视化 | ECharts + D3.js |
| LLM | DeepSeek / Gemini（通过 OpenAI 协议兼容）|
| 算法 | Sentence-Transformers + scikit-learn (PCA) |

## 快速启动

### 前置要求

- Python 3.11+
- Node.js 20+
- Git

### 1. 克隆仓库

```bash
git clone https://github.com/Ecankk/story_evolution_lab.git
cd story_evolution_lab
```

### 2. 配置环境变量

```bash
cp code/media-backend/.env.example code/media-backend/.env
```

编辑 `.env`，填入你的 API Key：

```ini
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite

# 或 DeepSeek
# LLM_PROVIDER=deepseek
# DEEPSEEK_API_KEY=your_deepseek_api_key_here
# DEEPSEEK_MODEL=deepseek-chat
```

> 没有 API Key 也能跑，系统会自动使用 Mock 数据。

### 3. 启动后端

```bash
cd code/media-backend

# 创建并激活虚拟环境（如未创建）
python -m venv ../../.venv
../../.venv/Scripts/activate  # Windows
# source ../../.venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt

# 启动服务（默认端口 8000）
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

如果端口 8000 被占用，换用其他端口：

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

同时修改前端代理配置 `code/media-frontend2/vite.config.ts` 中的端口。

### 4. 启动前端

新终端窗口：

```bash
cd code/media-frontend2

# 安装依赖（首次）
npm install

# 启动开发服务器
npm run dev
```

### 5. 访问

| 地址 | 说明 |
|------|------|
| http://localhost:5173/workbench | 多维工作台 |
| http://localhost:5173/game | 海龟汤游戏 |
| http://localhost:5173/analysis | 数据分析 |
| http://127.0.0.1:8000/docs | API 文档 (Swagger) |

## 项目结构

```
story_evolution_lab/
├── code/
│   ├── media-backend/          # FastAPI 后端
│   │   ├── app/
│   │   │   ├── main.py         # 应用入口
│   │   │   ├── routes/         # API 路由
│   │   │   ├── services/       # LLM 代理、打分引擎、存储
│   │   │   └── utils/          # 算法实现 (Embedding, PCA)
│   │   ├── data/               # 运行时数据存储（空目录，启动后自动生成）
│   │   ├── .env.example        # 环境变量模板
│   │   └── requirements.txt
│   └── media-frontend2/        # Vue 3 前端
│       ├── src/
│       │   ├── api/            # HTTP / WebSocket 封装
│       │   ├── components/     # 图表、聊天面板、游戏组件
│       │   ├── stores/         # Pinia 状态管理
│       │   ├── views/          # 页面级组件
│       │   └── services/       # 业务逻辑服务
│       ├── package.json
│       └── vite.config.ts
├── materials/                  # 调研文档与方案设计
└── README.md
```

## 核心指标定义

### Semantic Flow（语义流）

```
Flow = 1 - CosineDistance(Current_Embedding, Previous_Embedding)
```

衡量故事连贯性。值越接近 1，上下文衔接越紧密。

### Creative Entropy（创意熵）

```
Entropy = EuclideanDistance(Current_Embedding, Centroid(History_Embeddings))
```

衡量故事跳跃性/创新度。距离历史语义重心越远，创意性越强。

## 许可证

MIT
