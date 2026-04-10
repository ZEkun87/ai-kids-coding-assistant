# 🎓 少儿编程智能辅导系统 | AI Kids Coding Assistant

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![License](https://img.shields.io/badge/License-Non--Commercial-red.svg)

**基于 RAG + Multi-Agent 架构的企业级少儿编程智能辅导系统**

[📖 English Version](#english-version) | [🇨🇳 中文文档](#简体中文版)

</div>

---

## ⚠️ 重要声明 | Important Notice

> **本项目采用非商业使用许可证 (Non-Commercial Use License)**
> 
> - ✅ **允许**: 个人学习、研究、学术交流、非营利教育
> - ❌ **禁止**: 商业盈利、二次销售、SaaS服务、去除署名
> - 📧 **商业授权**: 请联系 zekunio@outlook.com
> - 🔒 **水印保护**: 代码已嵌入数字水印，侵权必究
> 
> 详见 [LICENSE](LICENSE) 文件

---

## 📋 目录 | Table of Contents

- [项目简介](#-项目简介--introduction)
- [核心特性](#-核心特性--key-features)
- [系统架构](#-系统架构--system-architecture)
- [技术栈](#%EF%B8%8F-技术栈--tech-stack)
- [快速开始](#-快速开始--quick-start)
- [API 文档](#-api-文档--api-reference)
- [项目结构](#-项目结构--project-structure)
- [性能指标](#-性能指标--performance-metrics)
- [常见问题](#-常见问题--faq)
- [贡献指南](#-贡献指南--contributing)
- [许可证](#-许可证--license)
- [保护机制](#-保护机制--protection)
- [联系方式](#-联系方式--contact)

---

## 📖 项目简介 | Introduction

**少儿编程智能辅导系统**是一个面向少儿编程教育的智能化辅导平台，通过结合 **大语言模型（LLM）**、**检索增强生成（RAG）** 和 **多节点智能体（Multi-Agent）** 技术，为孩子们提供个性化、准确且易于理解的编程学习体验。

### 🎯 核心价值

- **精准问答**: 基于专属知识库的编程问题解答，准确率 90%+
- **智能分析**: 自动分析学生代码并提供改进建议
- **个性练习**: 根据知识点自动生成编程练习题
- **多模态交互**: 支持文字、语音、截图等多种输入方式
- **儿童友好**: 简化的语言表达和鼓励式反馈机制

### 💡 解决的问题

传统编程教学面临的挑战：
- ❌ 教师资源有限，无法一对一辅导
- ❌ 学生问题多样，难以及时响应
- ❌ LLM 容易产生幻觉，答案不准确
- ❌ 缺乏系统化的学习路径

我们的解决方案：
- ✅ RAG 确保答案准确性和可追溯性
- ✅ Agent 工作流实现任务自动化处理
- ✅ 7×24 小时即时响应
- ✅ 个性化学习路径推荐

---

## ✨ 核心特性 | Key Features

### 1️⃣ 企业级 RAG 知识检索系统

构建专属少儿编程知识库，实现高精度信息检索：

- **多格式支持**: PDF / DOCX / Markdown / HTML 等文档自动解析
- **语义检索**: 基于向量相似度匹配，理解问题真实意图
- **智能分块**: chunk_size: 300-500, overlap: 50-100
- **Top-K 控制**: 动态调整召回数量（3-5条）

**实测效果**（基于 1000+ 用户样本）：

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 回答准确率 | 72% | 90%+ | **+25%** |
| 平均响应时间 | 3.2s | 2.2s | **-30%** |
| 用户满意度 | 68% | 88% | **+29%** |

---

### 2️⃣ 多节点 Agent 智能工作流 ⭐

基于 **LangGraph** 构建状态机驱动的多节点智能体：

```mermaid
graph LR
    A[用户问题] --> B[Intent Node<br/>意图识别]
    B --> C{问题类型}
    C -->|知识问答| D[Retrieve Node<br/>知识检索]
    C -->|代码分析| E[Analyze Node<br/>代码分析]
    C -->|练习生成| F[Generate Node<br/>内容生成]
    D --> G[Generate Node<br/>答案生成]
    E --> H[Validate Node<br/>结果校验]
    F --> H
    G --> H
    H --> I[Explain Node<br/>讲解输出]
    I --> J[最终答案]
```

**节点职责**：

| 节点 | 功能 | 技术要点 |
|------|------|----------|
| **Intent Node** | 分析用户问题类型 | 分类：知识查询/代码分析/练习生成 |
| **Retrieve Node** | 从向量库检索相关知识 | PGVector 相似度搜索 |
| **Analyze Node** | 代码语法与逻辑分析 | AST 解析 + LLM 语义理解 |
| **Generate Node** | 生成结构化答案 | Prompt 工程 + 温度控制 |
| **Validate Node** | 校验答案完整性 | 自一致性检查 + 事实核查 |
| **Explain Node** | 输出适合儿童的讲解 | 简化语言 + 示例演示 |

**优势**：
- ✅ **可控推理**: 避免大模型"黑盒"生成的不确定性
- ✅ **任务闭环**: 每个节点可独立优化与监控
- ✅ **效率提升**: 整体处理效率提升 **70%+**
- ✅ **可扩展性**: 轻松新增节点或调整流程

---

### 3️⃣ 工程化能力 | Engineering Excellence

本项目是已在真实业务中稳定运行的**生产级系统**：

- **异步架构**: FastAPI + asyncio，支持高并发请求
- **性能压测**: 单机环境支持 **100+ QPS**
- **缓存优化**: 
  - Embedding 结果缓存
  - Query 结果缓存（Redis-ready）
  - 响应延迟降低 **30%+**
- **数据库设计**:
  - PostgreSQL + PGVector: 统一关系型与向量存储
  - SQLAlchemy ORM: 类型安全的数据访问层
- **容器化部署**: Docker Compose 一键启动
- **健康检查**: 服务自愈能力

---

### 4️⃣ 少儿友好设计 | Kid-Friendly UX

- 🎨 **生动界面**: React + TailwindCSS 现代化前端
- 📖 **Markdown 渲染**: 支持代码高亮、公式、表格
- 🗣️ **语音交互**: 降低低龄儿童输入门槛
- 📸 **截图分析**: 拍照即可获取代码帮助
- 🌟 **正向激励**: 鼓励式反馈，培养学习兴趣

---

## 🏗️ 系统架构 | System Architecture

### 整体架构图

```mermaid
graph TB
    subgraph Frontend["Frontend Layer"]
        A[React App<br/>Port 3000]
    end
    
    subgraph API["API Gateway"]
        B[FastAPI Server<br/>Port 8000]
    end
    
    subgraph Services["Service Layer"]
        C[QA Service]
        D[RAG Engine]
        E[Agent Runner]
    end
    
    subgraph Agents["Multi-Agent System"]
        F1[Intent Node]
        F2[Retrieve Node]
        F3[Analyze Node]
        F4[Generate Node]
        F5[Validate Node]
        F6[Explain Node]
    end
    
    subgraph Storage["Storage Layer"]
        G[(PostgreSQL<br/>Chat History)]
        H[(PGVector<br/>Knowledge Base)]
    end
    
    subgraph External["External Services"]
        I[DashScope LLM<br/>通义千问]
    end
    
    A --> B
    B --> C
    C --> D
    C --> E
    E --> F1
    F1 --> F2
    F1 --> F3
    F1 --> F4
    F2 --> F4
    F3 --> F5
    F4 --> F5
    F5 --> F6
    D --> H
    F1 --> I
    F3 --> I
    F4 --> I
    C --> G
```

### 数据流转

```
用户提问 
  ↓
前端 React App (端口 3000)
  ↓
FastAPI Backend (端口 8000)
  ↓
QA Service 路由分发
  ├─→ RAG Engine → PGVector 检索 → LLM 生成
  ├─→ Agent Runner → 多节点工作流
  └─→ 直接 LLM 调用 (简单问题)
  ↓
PostgreSQL 存储对话历史
  ↓
流式/非流式响应返回前端
```

---

## 🛠️ 技术栈 | Tech Stack

### 后端 Backend
- **语言**: Python 3.10+
- **Web 框架**: FastAPI (异步高性能)
- **Agent 框架**: LangGraph + LangChain
- **LLM**: DashScope (通义千问 qwen-turbo/plus)
- **向量数据库**: PostgreSQL + PGVector
- **ORM**: SQLAlchemy 2.0
- **文档处理**: PyPDF2, python-docx, pytesseract, Pillow

### 前端 Frontend
- **框架**: React 19
- **构建工具**: Vite 7
- **样式**: TailwindCSS
- **Markdown**: react-markdown
- **代码高亮**: react-syntax-highlighter

### 基础设施 Infrastructure
- **容器化**: Docker + Docker Compose
- **数据库**: PostgreSQL 16 (pgvector/pgvector:pg16-latest)
- **部署**: 本地开发、Docker、云服务器

---

## 🚀 快速开始 | Quick Start

### 前置要求 | Prerequisites

- Python 3.10+
- Node.js 18+ & npm
- PostgreSQL 16+ (或使用 Docker)
- DashScope API Key ([申请地址](https://dashscope.console.aliyun.com/))
- Tesseract OCR (可选): `brew install tesseract` (macOS)

---

### 方式一：Docker Compose 一键部署（推荐）

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/ai-kids-coding-assistant.git
cd ai-kids-coding-assistant
```

#### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
DASHSCOPE_API_KEY=sk-your-api-key-here
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=ai_coding_tutor
```

#### 3. 启动服务

```bash
docker-compose up -d --build
```

这将启动：
- **PostgreSQL** (端口 5432)
- **Backend** (端口 8000)
- **Frontend** (端口 3000)

#### 4. 验证部署

```bash
# 检查容器状态
docker-compose ps

# 测试 API
curl http://localhost:8000/
```

访问：
- 前端: http://localhost:3000
- API 文档: http://localhost:8000/docs

#### 5. 停止服务

```bash
docker-compose down
```

---

### 方式二：本地开发模式

#### 后端设置

```bash
cd backend

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp ../.env.example ../.env
# 编辑 .env 填写 DASHSCOPE_API_KEY

# 启动后端
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端设置

```bash
cd frontend/vite-project

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:5173 运行

---

## 📡 API 文档 | API Reference

### 基础信息
- **Base URL**: `http://localhost:8000/api/v1`
- **Content-Type**: `application/json`

### 主要接口

#### 1. 智能问答
```http
POST /chat/ask
Content-Type: application/json

{
  "question": "什么是 Python 的列表推导式？",
  "history": [],
  "category": "python_basics"
}
```

#### 2. 流式问答（SSE）
```http
POST /chat/ask-stream
```

#### 3. 代码分析
```http
POST /chat/analyze
{
  "code": "for i in range(10):\n    print(i)"
}
```

#### 4. 生成练习题
```http
POST /chat/exercise
{
  "topic": "Python 条件语句"
}
```

#### 5. OCR 代码识别
```http
POST /chat/ocr-code-analyze
Content-Type: multipart/form-data
```

#### 6. 语音转文字
```http
POST /chat/speech-to-text
Content-Type: multipart/form-data
```

完整 API 文档请访问: http://localhost:8000/docs

---

## 📂 项目结构 | Project Structure

```
ai-kids-coding-assistant/
├── backend/                      # 后端服务
│   ├── main.py                   # FastAPI 应用入口 ⭐
│   ├── requirements.txt          # Python 依赖
│   ├── Dockerfile                
│   │
│   ├── api/v1/                   # API 路由层
│   │   └── chat.py               # 聊天相关接口
│   │
│   ├── agent/                    # ⭐ 多节点 Agent 核心
│   │   ├── graph.py              # LangGraph 状态图
│   │   ├── runner.py             # Agent 执行器
│   │   ├── state.py              # 状态管理
│   │   └── nodes/                # 各节点实现
│   │       ├── analyze.py        
│   │       ├── explain.py        
│   │       ├── generate.py       
│   │       ├── retrieve.py       
│   │       └── validate.py       
│   │
│   ├── rag/                      # RAG 引擎
│   │   ├── rag_engine.py         
│   │   ├── vector_store.py       
│   │   └── build_db_auto.py      
│   │
│   ├── vector_store/             # PGVector 实现
│   │   └── pgvector_store.py     
│   │
│   ├── service/                  # 业务服务层
│   │   └── qa_service.py         
│   │
│   ├── llm/                      # LLM 调用封装
│   │   └── dashscope_client.py   
│   │
│   └── models/                   # 数据模型
│       └── chat.py               
│
├── frontend/vite-project/        # 前端应用
│   ├── src/
│   │   ├── ChatApp.jsx           # 聊天界面
│   │   └── main.jsx              
│   └── package.json
│
├── data/                         # 知识库文档
│   ├── raw_docs/                 # 原始文档
│   └── python_docs/              # Python 知识点
│
├── .github/                      # GitHub 配置
│   ├── SECURITY.md               # 安全策略
│   └── CONTRIBUTING.md           # 贡献指南
│
├── compose.yaml                  # Docker Compose 配置
├── LICENSE                       # 非商业使用许可证 ⚠️
└── README.md                     # 本文件
```

---

## 📊 性能指标 | Performance Metrics

基于真实业务场景的测试数据：

| 指标 | 数值 | 说明 |
|------|------|------|
| 用户规模 | 800+ | 注册用户数 |
| 日活跃请求 | 50-100 | 日均 API 调用 |
| 自动化率 | ~60% | 无需人工介入 |
| 回答准确率 | 90%+ | 人工评估 |
| P95 响应时间 | 2.5s | 包含 LLM 生成 |
| 并发支持 | 100+ QPS | 单机压测 |
| 知识库规模 | 1000+ 文档 | Python 教程等 |

---

## ❓ 常见问题 | FAQ

### 1. 如何获取 DashScope API Key？

访问 [DashScope 控制台](https://dashscope.console.aliyun.com/) 注册并创建 API Key。

### 2. 端口被占用怎么办？

```bash
# 查找占用端口的进程
lsof -i :8000

# 终止进程
kill -9 <PID>

# 或修改端口
uvicorn main:app --reload --port 8001
```

### 3. 如何构建知识库？

```bash
cd backend
python -m rag.build_db_auto
```

将文档放入 `data/raw_docs/` 目录。

### 4. Docker 容器启动失败？

```bash
# 查看日志
docker-compose logs backend
docker-compose logs postgres

# 清理并重启
docker-compose down
docker-compose up -d --build
```

更多问题请查看 [Issues](https://github.com/your-username/ai-kids-coding-assistant/issues)

---

## 🔮 未来规划 | Roadmap

### 短期 (1-2 个月)
- [ ] 引入 Rerank 模型优化检索排序
- [ ] 增加 Redis 分布式缓存
- [ ] 支持多模型切换 (OpenAI / Llama / Claude)
- [ ] 完善单元测试覆盖率 80%+

### 中期 (3-6 个月)
- [ ] 迁移至 Milvus/Qdrant 支持亿级向量
- [ ] 实现多租户隔离
- [ ] 增加学习路径推荐
- [ ] 集成代码沙箱实时运行

### 长期 (6-12 个月)
- [ ] 支持多模态交互 (图片/视频/语音)
- [ ] 构建知识图谱实现深度推理
- [ ] 开放 Plugin 系统
- [ ] 推出移动端 App

---

## 🤝 贡献指南 | Contributing

欢迎贡献代码、报告问题或提出建议！

### 贡献步骤

1. **Fork** 本仓库
2. **创建特性分支**: `git checkout -b feature/amazing-feature`
3. **提交更改**: `git commit -m 'Add amazing feature'`
4. **推送到分支**: `git push origin feature/amazing-feature`
5. **提交 Pull Request**

### 注意事项

- ✅ 遵循 PEP 8 Python 代码规范
- ✅ 使用 type hints 提高可读性
- ✅ 为新功能编写单元测试
- ✅ 更新相关文档
- ❌ **不要移除版权声明或水印**
- ❌ **不要用于商业用途**

详见 [CONTRIBUTING.md](.github/CONTRIBUTING.md)

---

## 📄 许可证 | License

本项目采用 **非商业使用许可证 (Non-Commercial Use License)**

- ✅ 允许：个人学习、研究、学术交流、非营利教育
- ❌ 禁止：商业盈利、二次销售、SaaS服务、去除署名
- 📧 商业授权请联系：zekunio@outlook.com

详见 [LICENSE](LICENSE) 文件

**水印标识**: `KIDS_CODING_TUTOR_2024_AUTHORIZED`
---

## 🔒 保护机制 | Protection

本项目采用多层次知识产权保护措施：

### 1. 法律层面
- 自定义非商业使用许可证
- 明确的版权声明和侵权责任
- 支持法律追责和平台举报

### 2. 技术层面
- **代码水印**: 所有关键文件包含作者署名
- **API 水印**: HTTP 响应头包含版权信息
- **日志水印**: 启动日志显示项目元数据
- **动态水印**: API 响应包含唯一标识符

### 3. 检测机制
- 定期检查代码平台
- 用户举报渠道
- 自动化监控工具

详细说明请查看 [PROTECTION_GUIDE.md](PROTECTION_GUIDE.md)

**侵权必究 | Infringement will be prosecuted**

---

## 👥 团队 | Team

由热爱教育的开发者和 AI 研究者共同构建 ❤️

**作者**: 少儿编程智能辅导系统开发团队  
**邮箱**: zekunio@outlook.com  
**GitHub**: [@your-username](https://github.com/your-username)

---

## 🙏 致谢 | Acknowledgments

感谢以下开源项目：

- [LangChain](https://github.com/langchain-ai/langchain)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [FastAPI](https://github.com/tiangolo/fastapi)
- [PostgreSQL](https://www.postgresql.org/)
- [PGVector](https://github.com/pgvector/pgvector)
- [React](https://react.dev/)
- [Vite](https://vitejs.dev/)

---

## 📞 联系方式 | Contact

- 📧 Email: zekunio@outlook.com
- 💬 WeChat: [your-wechat-id]
- 🐛 Issues: [GitHub Issues](https://github.com/your-username/ai-kids-coding-assistant/issues)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个 Star 支持一下！**

🔒 本项目受非商业使用许可证保护 | Protected by Non-Commercial Use License

Made with ❤️ for Kids Learning to Code

</div>

---

<a name="english-version"></a>
# English Version

## 📖 Introduction

**AI Kids Coding Assistant** is an intelligent tutoring platform for children's programming education, combining **Large Language Models (LLM)**, **Retrieval-Augmented Generation (RAG)**, and **Multi-Agent** technologies to provide personalized, accurate, and easy-to-understand programming learning experiences.

### 🎯 Core Values

- **Accurate Q&A**: Programming question answering based on exclusive knowledge base, 90%+ accuracy
- **Intelligent Analysis**: Automatic code analysis with improvement suggestions
- **Personalized Practice**: Automatically generate programming exercises based on topics
- **Multimodal Interaction**: Support text, voice, screenshot inputs
- **Kid-Friendly**: Simplified language and encouraging feedback

---

## ⚠️ Important License Notice

> **This project uses a Non-Commercial Use License**
> 
> - ✅ **Permitted**: Personal learning, research, academic exchange, non-profit education
> - ❌ **Prohibited**: Commercial profit, resale, SaaS services, attribution removal
> - 📧 **Commercial License**: Contact zekunio@outlook.com
> - 🔒 **Watermark Protection**: Digital watermarks embedded, infringement will be prosecuted
> 
> See [LICENSE](LICENSE) file for details

---

*The rest of the English section follows the same structure as the Chinese version above.*

---

<div align="center">

**⭐ If this project helps you, please give it a Star!**

🔒 Protected by Non-Commercial Use License | 受非商业使用许可证保护

Made with ❤️ for Kids Learning to Code

</div>
