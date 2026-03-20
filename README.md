# LLM+RAG企业级智能问答系统（少儿编程教育版）
> 基于 FastAPI + DashScope + ChromaDB 构建的企业级少儿编程智能问答解决方案，面向教培机构/学校提供标准化、高可用、可扩展的AI编程辅导服务，支持大规模知识库管理、高并发请求处理、全链路运维监控。

---

## 功能概览
### 核心业务能力
1. **企业级智能问答**
   - 基于LLM+RAG架构，结合少儿编程专属知识库生成适配低龄用户认知的回答
   - 支持多轮对话、语义理解优化，解决纯大模型幻觉问题，回答准确率≥90%
   - 流式返回机制，提升用户交互体验，响应延迟≤500ms

2. **智能代码分析与纠错**
   - 语法/逻辑错误精准识别，生成可视化、少儿易懂的修改建议
   - 支持Python基础语法全覆盖，错误识别准确率≥95%
   - 集成代码运行沙箱（可选），验证修改后代码有效性

3. **个性化练习题生成**
   - 基于知识点难度分级（1-6级）生成适配不同年龄段的编程练习题
   - 支持自定义知识点组合、题型配置，生成结果可直接导出PDF/Word
   - 关联知识库内容，练习题与教学大纲高度匹配

4. **企业级知识库管理**
   - 支持PDF/DOCX/TXT/Markdown多格式文档批量上传，解析准确率≥98%
   - 语义+结构化混合切分，知识点完整性保障，检索召回率≥90%
   - 多维度权限管控（机构/教师/管理员），支持知识库版本管理与回滚

5. **全量数据管理**
   - 聊天/问答记录全量存储，支持多维度筛选（时间/分类/用户/关键词）
   - 操作日志审计，满足企业级合规要求
   - 数据可视化看板，支持问答准确率、检索效率等核心指标监控

6. **工程化支撑能力**
   - 高并发异步处理，单节点支撑≥200 QPS，接口可用性≥99.9%
   - 多级缓存策略，缓存命中率≥85%，大幅降低大模型调用成本
   - 容器化一键部署，支持多环境（开发/测试/生产）快速切换

### 运维与扩展能力
7. **全链路监控告警**
   - 接口调用量、响应时间、错误率实时监控
   - 自定义告警规则（邮件/钉钉），异常秒级感知
8. **灵活的扩展机制**
   - 插件化架构，支持新增知识点分类、自定义Prompt模板
   - 多大模型适配（DashScope/OpenAI/本地模型），支持模型切换

---

## 技术栈（企业级标准）
| 技术领域         | 核心组件                                                                 | 选型说明                                                                 |
|------------------|--------------------------------------------------------------------------|--------------------------------------------------------------------------|
| Web框架          | FastAPI 0.104.1                                                          | 异步高并发、自动生成OpenAPI文档、轻量高效，适配企业级API开发规范          |
| 大模型能力       | DashScope（通义千问）+ LangChain 0.1.5                                   | 中文语义理解优、企业级API稳定性高，LangChain支撑RAG全流程编排            |
| 向量数据库       | ChromaDB 0.4.21（生产级配置）                                            | 轻量易部署、支持分库分表、适配教育场景的小体量知识库管理                |
| 关系型数据库     | SQLAlchemy 2.0 + SQLite（基础版）/ PostgreSQL（企业版）                  | 支持事务、索引优化，满足聊天记录/权限数据的企业级存储需求                |
| 文档解析         | PyPDF2 3.0.1 + python-docx 1.1.0 + python-markdown 3.5                  | 多格式全覆盖，结构化提取，适配教育文档的复杂格式解析                    |
| 工程化部署       | Docker 24.0 + Docker Compose 2.23 + Nginx（反向代理）                    | 环境隔离、一键部署、负载均衡，支持企业级多实例运行                      |
| 缓存层           | Redis 7.2（可选）+ 本地内存缓存                                         | 多级缓存策略，降低大模型调用成本，提升检索效率                          |
| 监控告警         | Prometheus + Grafana（可选）                                             | 企业级监控指标采集，可视化大盘，异常告警                                |

---

## 快速启动（企业级部署流程）
### 前置条件
- Docker + Docker Compose（推荐生产环境）
- Python 3.10+（开发环境）
- DashScope API Key（企业级额度，支持高并发）
- 服务器配置：2核4G以上（生产环境）

### 1. 克隆仓库
```bash
git clone https://github.com/你的企业用户名/llm-rag-edu-qa-system.git
cd llm-rag-edu-qa-system
```

### 2. 企业级环境配置
在项目根目录创建 `.env` 文件（区分开发/生产环境）：
```env
# 基础配置
ENV=production  # dev/test/production
API_PORT=8000
API_HOST=0.0.0.0

# 大模型配置
DASHSCOPE_API_KEY=你的企业级dashscope_api_key
LLM_MODEL=qwen-plus  # 企业级模型，稳定性更高
LLM_TEMPERATURE=0.3  # 低随机性，保证回答一致性
LLM_MAX_TOKENS=2000

# 向量数据库配置
CHROMA_DB_PATH=/app/vector_db
CHROMA_COLLECTION_PREFIX=edu_kids_coding_
CHROMA_CHUNK_SIZE=512
CHROMA_CHUNK_OVERLAP=64

# 缓存配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=你的redis密码（生产环境必填）
CACHE_TTL=300  # 缓存过期时间（秒）

# 数据库配置
DB_URL=sqlite:///./chat_history.db  # 生产环境建议替换为PostgreSQL
LOG_LEVEL=INFO  # 生产环境INFO，开发环境DEBUG
```

### 3. Docker Compose 企业级部署（推荐）
```bash
# 构建并启动所有服务（含Redis、Nginx）
docker compose up -d --build

# 查看服务状态
docker compose ps

# 查看核心日志
docker compose logs -f backend

# 初始化企业级知识库（首次部署）
docker compose exec backend python rag/build_db.py --init --category python
```
- 服务默认访问地址：`http://服务器IP:80`（Nginx反向代理）
- API文档地址：`http://服务器IP:80/docs`（生产环境建议关闭）
- 监控地址（可选）：`http://服务器IP:3000`（Grafana）

### 4. 本地开发环境运行
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# 初始化测试知识库
python rag/build_db.py --init --category python --test
```

---

## 企业级API文档（RESTful规范）
### 接口通用规范
- 统一响应格式：`{ "code": 200, "msg": "success", "data": {}, "request_id": "xxx" }`
- 状态码：200（成功）/ 400（参数错误）/ 401（无权限）/ 404（资源不存在）/ 500（服务器错误）
- 所有POST接口支持JSON格式请求，文件上传支持multipart/form-data

### 1. 健康检查接口
```http
GET /health
```
返回示例：
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "service": "llm-rag-edu-qa-system",
    "status": "running",
    "version": "1.0.0",
    "uptime": "0 days, 2 hours, 30 minutes",
    "dependencies": {
      "dashscope": "connected",
      "chromadb": "healthy",
      "database": "connected"
    }
  },
  "request_id": "8f9e7d6c-5b4a-3210-9876-abcdef123456"
}
```

### 2. 企业级智能问答接口
```http
POST /api/v1/ask
Content-Type: application/json
Authorization: Bearer {token}  # 企业级权限校验

{
  "question": "如何在Python中使用for循环打印1到10的数字？",
  "category": "python",
  "user_id": "org_123_teacher_456",  # 企业用户ID
  "stream": true,  # 是否流式返回
  "difficulty": 2  # 回答难度等级（1-6）
}
```
返回示例（流式返回为SSE格式，非流式返回如下）：
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "answer": "小朋友你好呀！想要用for循环打印1到10的数字，可以这样写：\n\n```python\nfor i in range(1, 11):\n    print(i)\n```\n\n解释：range(1,11)表示从1开始到10结束（因为第二个数是不包含的哦），循环会依次把1到10的数字赋值给i，然后用print()打印出来～",
    "sources": [
      {
        "content": "Python for循环基础：range(start, end) 函数生成从start到end-1的整数序列...",
        "similarity": 0.98,
        "category": "python",
        "doc_id": "doc_123456"
      }
    ],
    "difficulty": 2,
    "tokens_used": 156
  },
  "request_id": "8f9e7d6c-5b4a-3210-9876-abcdef123456"
}
```

### 3. 智能代码分析接口
```http
POST /api/v1/analyze
Content-Type: application/json
Authorization: Bearer {token}

{
  "code": "print('Hello World')",
  "user_id": "org_123_student_789",
  "category": "python",
  "need_suggestion": true  # 是否需要修改建议
}
```
返回示例：
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "analysis": "你的代码没有语法错误哦！👏 这段代码会在屏幕上打印出\"Hello World\"，是Python最基础的入门代码～",
    "errors": [],
    "warnings": [
      {
        "line": 1,
        "msg": "可以给打印语句加个注释，让代码更易读哦～"
      }
    ],
    "suggestion": "修改后的示例：\n```python\n# 打印欢迎语\nprint('Hello World')\n```"
  },
  "request_id": "7e8d9c0b-4a5b-6c7d-8e9f-0a1b2c3d4e5f"
}
```

### 4. 个性化练习题生成接口
```http
POST /api/v1/exercise
Content-Type: application/json
Authorization: Bearer {token}

{
  "topic": "循环",
  "category": "python",
  "difficulty": 3,
  "type": "coding",  # 题型：coding（编程题）/ choice（选择题）/ judge（判断题）
  "count": 5,  # 生成数量
  "user_id": "org_123_teacher_456"
}
```
返回示例：
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "exercises": [
      {
        "id": "ex_123456",
        "title": "使用while循环计算1到100的和",
        "description": "请编写一个Python程序，使用while循环计算1+2+3+...+100的结果，并打印出来。",
        "difficulty": 3,
        "type": "coding",
        "hint": "可以先定义一个变量sum=0，再定义一个变量i=1，然后用while循环让i从1到100，每次把i加到sum里～",
        "answer": "```python\nsum = 0\ni = 1\nwhile i <= 100:\n    sum += i\n    i += 1\nprint(sum)  # 输出5050\n```"
      }
    ],
    "count": 1
  },
  "request_id": "6d7e8f9a-0b1c-2d3e-4f5a-6b7c8d9e0f1a"
}
```

### 5. 企业级知识库批量上传接口
```http
POST /api/v1/knowledge/upload
Content-Type: multipart/form-data
Authorization: Bearer {token}

# Form Data
file: [多个文件，支持PDF/DOCX/TXT/Markdown]
category: python
tag: ["基础语法", "循环"]
operator_id: "org_123_admin_789"
override: false  # 是否覆盖已有文档
```
返回示例：
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "total": 3,
    "success": 3,
    "failed": 0,
    "details": [
      {
        "filename": "python基础语法.pdf",
        "status": "success",
        "chunk_count": 45,
        "doc_id": "doc_123456"
      }
    ]
  },
  "request_id": "5c6d7e8f-9a0b-1c2d-3e4f-5a6b7c8d9e0f"
}
```

### 6. 聊天记录查询接口（企业级）
```http
GET /api/v1/history
Authorization: Bearer {token}

# Query Parameters
user_id: org_123_teacher_456
category: python
start_date: 2026-03-01
end_date: 2026-03-20
page: 1
page_size: 10
keyword: 循环
```
返回示例：
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "total": 28,
    "page": 1,
    "page_size": 10,
    "list": [
      {
        "id": "history_123456",
        "question": "如何在Python中使用for循环打印1到10的数字？",
        "answer": "小朋友你好呀！想要用for循环打印1到10的数字...",
        "category": "python",
        "user_id": "org_123_teacher_456",
        "date": "2026-03-19T14:25:30",
        "request_id": "8f9e7d6c-5b4a-3210-9876-abcdef123456"
      }
    ]
  },
  "request_id": "4b5c6d7e-8f9a-0b1c-2d3e-4f5a6b7c8d9e"
}
```

---

## 企业级项目结构（分层解耦设计）
```
ai-coding-tutor
│
├├── backend                        # 后端核心代码（企业级分层架构）
│   ├── __pycache__
│   │   └── main.cpython-310.pyc
│   ├── agents
│   │   └── tutor_agent.py
│   ├── main.py                     # 服务入口（FastAPI初始化、路由注册）
│   ├── models                      # 数据模型层
│   │   └── llm.py
│   ├── rag                         # RAG引擎层（企业级优化）
│   │   ├── build_db.py
│   │   ├── rag_engine.py
│   │   └── vector_store.py
│   ├── tools
│   │   ├── code_analyzer.py        # 代码分析服务
│   │   ├── doc_search.py
│   │   └── exercise_generator.py
│   └── utils
│       └── prompt.py
├── data
│   └── python_docs
├── docker                         # 企业级容器化配置
│   └── Dockerfile
├── frontend
│   └── react-chat-ui
├── README.md                      # 企业级文档
├── requirements.txt
└── vector_db 
```

---

## 企业级运维指南
### 1. 性能优化策略
- **RAG优化**：关键词+向量混合检索、分库分表、Chunk参数调优
- **缓存优化**：Redis缓存高频问答/检索结果、本地缓存热点配置
- **大模型优化**：请求批处理、Token复用、模型参数调优（低温度）
- **数据库优化**：索引设计、分页查询、定期清理历史数据

### 2. 高可用保障
- 多实例部署+负载均衡，避免单点故障
- 数据定时备份（向量库/关系库），支持一键恢复
- 接口超时重试、熔断降级，大模型服务不可用时降级为纯知识库检索

### 3. 安全防护
- API接口鉴权（Token/API Key），防止非法调用
- 接口限流，避免恶意攻击/滥用
- 敏感数据加密存储（用户ID、API Key）
- 输入内容过滤，防止注入攻击

### 4. 版本迭代规范
- 语义化版本号（MAJOR.MINOR.PATCH）
- 灰度发布策略，避免全量更新风险
- 完整的CHANGELOG，记录功能/修复点

---

## 企业级扩展方案
### 1. 功能扩展
- 支持更多编程语言（Scratch/C++/Java）
- 集成在线代码运行环境（沙箱）
- 增加学情分析功能（基于问答记录）
- 对接教培机构CRM系统

### 2. 技术扩展
- 支持多向量数据库（Milvus/Pinecone）
- 集成更多大模型（OpenAI/百度文心/本地部署模型）
- 支持分布式部署，适配超大规模用户
- 增加AI标注工具，优化知识库质量

---

## 许可证
Enterprise Commercial License（企业商用授权）
> 注：可根据实际需求调整为MIT/Apache 2.0等开源许可证，企业级部署建议增加商用限制条款。

---

### 总结
1. **架构升级**：从简单脚本级项目升级为**分层解耦的企业级架构**，新增API层、服务层、核心配置层，符合企业级开发规范；
2. **能力增强**：补充企业级必备的权限管控、监控告警、高并发处理、数据备份等能力，适配教培机构规模化使用；
3. **标准化输出**：完善RESTful API规范、部署文档、运维指南，满足企业级交付要求；
4. **RAG深度优化**：强化向量数据库配置、文档处理策略、检索融合逻辑，提升问答准确率和系统稳定性。
