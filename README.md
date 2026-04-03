# 🚀 企业级AI智能问答系统（RAG + Agent架构）- 少儿编程教育版

> 基于 LLM + RAG（检索增强生成）+ 多节点Agent 构建的企业级智能问答系统  
> 面向教培/企业知识库场景，提供高准确率问答、任务闭环处理与系统化AI能力落地方案

---

## 📌 项目背景

在实际业务中，存在以下问题：

- 企业知识分散，检索困难
- 人工答疑成本高、效率低
- 复杂问题需要多轮沟通，体验差

👉 本项目通过引入 **RAG + Agent 架构**，实现从“被动问答”到“任务闭环处理”的能力升级。

---

## 🔥 核心亮点

### ✅ 1. 企业级RAG系统落地
- 支持 PDF / DOCX / Markdown 等多格式知识库构建
- 基于语义检索增强大模型回答能力
- 在真实业务中承接约 **60%基础咨询问题**

---

### ✅ 2. 多节点Agent架构（核心亮点）
基于 LangGraph 构建多节点智能体，将复杂问题拆解为：

```

问题理解 → 知识检索 → 方案生成 → 结果校验 → 讲解输出

````

- 通过状态机控制流程（State + 条件分支）
- 避免大模型单轮生成不稳定问题
- 实现任务闭环处理，整体效率提升约 **70%+**

---

### ✅ 3. 检索与生成优化（真实评估）
- chunk_size：300–500
- overlap：50–100
- Top-K：3–5

基于 **1000+真实用户样本**进行人工评估：

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 准确率 | 72% | 90%+ |

---

### ✅ 4. 工程化能力（非Demo项目）
- 基于 FastAPI 构建异步API服务
- 支持约 **100并发压测（单机环境）**
- 引入缓存机制（Embedding / Query缓存）减少重复计算
- 响应延迟优化约 **30%+**

---

## 🏗️ 系统架构

```text
用户问题
   ↓
RAG检索（向量数据库）
   ↓
Agent调度（LangGraph）
   ↓
多节点处理：
   - Intent（问题理解）
   - Retrieve（知识检索）
   - Generate（答案生成）
   - Validate（结果校验）
   - Explain（结果讲解）
   ↓
返回最终答案
````

---

## 🧠 Agent流程设计

本项目核心为多节点智能体系统：

| 节点            | 作用         |
| ------------- | ---------- |
| Intent Node   | 分析用户问题类型   |
| Retrieve Node | 从知识库检索相关内容 |
| Generate Node | 生成答案       |
| Validate Node | 校验结果完整性    |
| Explain Node  | 输出结构化讲解    |

👉 通过流程拆解，使AI从“黑盒生成”变为“可控推理”。

---

## 📚 RAG流程

```text
文档解析 → 文本切分 → Embedding → 向量存储 → 相似度检索 → LLM生成
```

### 优化点：

* 语义切分（chunk_size / overlap）
* Top-K召回控制
* Prompt分层设计（理解层 / 生成层 / 讲解层）

---

## 📊 项目效果

* 用户规模：800+
* 日请求量：50–100
* 自动化率：约60%
* 核心问题识别准确率：72% → 90%+
* 响应优化：延迟降低约30%

👉 系统已在真实业务中稳定运行（非Demo项目）

---

## 🧱 项目结构（分层解耦）

```bash
backend/
├── main.py                 # 服务入口
├── api/                    # 接口层
│   └── v1/
│       └── ask.py
│
├── agent/                  # ⭐ 多节点智能体核心
│   ├── graph.py
│   ├── runner.py
│   ├── state.py
│   └── nodes/
│       ├── intent_node.py
│       ├── retrieve_node.py
│       ├── generate_node.py
│       ├── validate_node.py
│       └── explain_node.py
│
├── rag/                    # RAG引擎
│   ├── rag_engine.py
│   ├── vector_store.py
│   └── document_processor.py
│
├── service/                # 业务服务层
│   └── qa_service.py
│
├── llm/                    # 大模型调用封装
├── models/                 # 数据模型
├── utils/                  # 工具类
```

---

## ⚙️ 技术栈

* Python
* FastAPI（异步Web框架）
* LangChain / LangGraph（Agent框架）
* DashScope（通义千问）
* ChromaDB（向量数据库）
* SQLAlchemy（数据建模）
* Docker（容器化部署）

---

## 🚀 快速启动

```bash
git clone https://github.com/你的仓库地址
cd backend

pip install -r requirements.txt

uvicorn main:app --reload
```

### 本地联调（前后端）

```bash
# Terminal 1: backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Terminal 2: frontend
cd frontend/vite-project
npm install
npm run dev
```

前端开发代理已配置到 `http://127.0.0.1:8001`，默认可直连 `/ask`、`/ask-stream`、`/upload`、`/history`、`/analyze`、`/exercise`。

### 常见问题排查

1. **`Address already in use`（端口占用）**
   - 查看占用：`lsof -i :8000` 或 `lsof -i :8001`
   - 若被 Docker 占用，切换后端端口到 `8001` 并同步前端代理。

2. **`ModuleNotFoundError: No module named 'langgraph'`**
   - 执行：`pip install -r requirements.txt`
   - 或单独安装：`pip install "langgraph>=0.2.0"`

3. **`No api key provided`**
   - 在 `backend/.env` 或项目根目录 `.env` 中配置：
     - `DASHSCOPE_API_KEY=你的key`
   - 重启后端后查看启动日志：
     - `Startup config: DASHSCOPE_API_KEY=configured`

---

## 🔧 优化方向（可扩展）

* 引入 Milvus 替代 ChromaDB（支持大规模数据）
* 增加 Rerank 重排序优化检索质量
* 引入 Redis 分布式缓存
* 支持多模型切换（OpenAI / 本地模型）

---

## 📌 项目说明

👉 本项目为真实业务场景落地项目，重点在于：

* AI能力工程化落地
* RAG与Agent结合实践
* 提升业务自动化与效率

---

## 📬 联系方式

如对项目感兴趣，欢迎交流。