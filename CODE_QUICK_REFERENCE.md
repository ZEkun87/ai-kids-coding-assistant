# 🔍 关键代码速查表 - 面试前必读

> 这个文件包含了项目最核心的 15 个代码片段，可以快速查阅

---

## 1️⃣ 项目启动入口

**文件**: `backend/main.py`

```python
from fastapi import FastAPI
from api.v1.chat import router as chat_router
from models.chat import init_db
from vector_store.pgvector_store import init_vector_db

app = FastAPI(title="少儿编程智能辅导系统")

# 启动时初始化两个数据库
try:
    init_db()  # PostgreSQL 聊天历史
    init_vector_db()  # PGVector 向量存储
except Exception as e:
    logger.error(f"数据库初始化失败: {e}")
    sys.exit(1)

# 注册路由
app.include_router(chat_router, prefix="/api/v1/chat")
app.include_router(rag_router, prefix="/api/v1/rag")
```

**面试要点**:
- ✅ FastAPI 应用初始化
- ✅ 中间件配置 (CORS)
- ✅ 数据库初始化 (可靠性)
- ✅ 路由注册 (模块化)

---

## 2️⃣ API 路由层

**文件**: `backend/api/v1/chat.py`

```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str
    category: str = "default"

# 核心接口: /ask
@router.post("/ask")
def ask_question_endpoint(request: QuestionRequest):
    """
    用户提问端点
    
    输入: {"question": "什么是装饰器？", "category": "python"}
    输出: {"answer": "...", "sources": [...], "intent": "knowledge"}
    """
    result = ask_question(
        request.question, 
        request.category
    )
    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "intent": result["intent"]
    }

# 代码分析接口
@router.post("/analyze")
def analyze_code_endpoint(request: CodeRequest):
    return {"analysis": analyze_code(request.code)}

# 生成习题接口
@router.post("/exercise")
def generate_exercise_endpoint(request: TopicRequest):
    return {"exercise": generate_exercise(request.topic)}

# 上传知识库接口
@router.post("/upload")
async def upload_file(file: UploadFile, category: str = "default"):
    return await upload_and_index(file, category)
```

**面试要点**:
- ✅ 路由定义清晰
- ✅ 请求/响应类型有验证 (Pydantic)
- ✅ 接口设计符合 REST 规范
- ✅ 支持多个功能 (ask, analyze, exercise, upload)

---

## 3️⃣ Agent 工作流 - 核心逻辑

**文件**: `backend/agent/graph.py`

```python
from langgraph.graph import StateGraph
from agent.state import AgentState
from agent.nodes import *

def build_graph():
    """构建 Agent 的 DAG (有向无环图)"""
    
    # 1. 创建工作流
    workflow = StateGraph(AgentState)
    
    # 2. 添加6个节点
    workflow.add_node("analyze", analyze_node)           # 意图识别
    workflow.add_node("code_analyze", code_analyze_node) # 代码分析
    workflow.add_node("retrieve", retrieve_node)         # 知识检索
    workflow.add_node("generate", generate_node)         # LLM 生成
    workflow.add_node("validate", validate_node)         # 质量验证
    workflow.add_node("explain", explain_node)           # 格式输出
    
    # 3. 设置入口点
    workflow.set_entry_point("analyze")
    
    # 4. 条件路由：根据意图分流
    def route_by_intent(state: AgentState):
        if state.get("intent") == "code_analysis":
            return "code_analyze"  # 代码问题 → 直接分析
        else:
            return "retrieve"       # 知识问题 → 先检索

    workflow.add_conditional_edges("analyze", route_by_intent)
    
    # 5. 普通流程边
    workflow.add_edge("retrieve", "generate")     # 检索 → 生成
    workflow.add_edge("generate", "validate")     # 生成 → 验证
    workflow.add_edge("code_analyze", "explain")  # 分析 → 输出
    
    # 6. 验证循环：如果验证失败，重新生成
    def check_valid(state: AgentState):
        if state.get("validated"):
            return "explain"      # 验证通过 → 输出
        else:
            return "generate"     # 验证失败 → 重新生成

    workflow.add_conditional_edges("validate", check_valid)
    
    # 7. 结束
    workflow.add_edge("explain", "__end__")
    
    return workflow.compile()  # 编译成可执行图
```

**流程可视化**:
```
                 ┌─→ code_analyze ─┐
                 │                 ↓
analyze ─route→ {                explain ─→ END
                 │                 ↑
                 └─→ retrieve → generate → validate ─┐
                                           │         ├──┤(loop)
                                           └─────────┘
```

**面试要点**:
- ✅ LangGraph 的 DAG 设计
- ✅ 条件路由的逻辑
- ✅ 自我验证的循环机制
- ✅ 对 state management 的理解

---

## 4️⃣ Agent 状态定义

**文件**: `backend/agent/state.py`

```python
from typing import Annotated, Any, Dict, List
from pydantic import BaseModel

class AgentState(BaseModel):
    """Agent 内部传递的状态"""
    
    # 输入
    question: str                          # 用户问题
    category: str = "default"              # 分类
    
    # 中间状态
    intent: str = ""                       # 意图 ("knowledge" or "code_analysis")
    
    # 检索结果
    retrieved_docs: List[Dict[str, Any]] = []  # 检索到的文档列表
    
    # LLM 输出
    answer: str = ""                       # 生成的答案文本
    
    # 验证结果
    validated: bool = False                # 是否通过验证
    validation_errors: List[str] = []      # 验证错误列表
    
    # 最终输出
    structured_output: Dict[str, Any] = {} # 结构化输出
    sources: List[str] = []                # 答案来源
```

**面试要点**:
- ✅ State 的设计完整覆盖整个流程
- ✅ 类型注解清晰
- ✅ 可见数据流转过程

---

## 5️⃣ 分析节点 - 意图识别

**文件**: `backend/agent/nodes/analyze.py`

```python
from agent.state import AgentState
from llm.dashscope_client import call_llm

def analyze_node(state: AgentState) -> AgentState:
    """
    第一个节点：分析用户意图
    
    输入: question = "写一个 Python 的递归函数"
    输出: intent = "code_analysis"
    """
    
    prompt = f"""
    分析以下问题的意图，返回 "code_analysis" 或 "knowledge":
    
    如果问题要求生成代码或分析代码，返回 "code_analysis"
    如果问题要求解释概念或查询信息，返回 "knowledge"
    
    问题: {state.question}
    
    返回格式: 单行，仅返回 "code_analysis" 或 "knowledge"
    """
    
    response = call_llm(prompt)
    intent = response.strip().lower()
    
    # 更新 state
    state.intent = intent if intent in ["code_analysis", "knowledge"] else "knowledge"
    
    return state
```

**面试要点**:
- ✅ Node 的标准输入/输出
- ✅ LLM 调用方式
- ✅ 意图分类逻辑

---

## 6️⃣ 检索节点 - RAG 核心

**文件**: `backend/agent/nodes/retrieve.py`

```python
from agent.state import AgentState
from rag.rag_engine import ask_knowledge

def retrieve_node(state: AgentState) -> AgentState:
    """
    检索节点：从知识库检索相关文档
    
    核心流程:
    1. 问题向量化
    2. 相似度搜索
    3. 返回前 K 个结果
    """
    
    # 调用 RAG 引擎检索
    result = ask_knowledge(
        question=state.question,
        category=state.category,
        top_k=5  # 返回前 5 个最相似的文档
    )
    
    if result.get("code") == 0:
        documents = result.get("data", {}).get("sources", [])
        state.retrieved_docs = documents
    else:
        logger.error(f"检索失败: {result.get('message')}")
        state.retrieved_docs = []
    
    return state
```

**面试要点**:
- ✅ RAG 的调用方式
- ✅ 错误处理
- ✅ Top-K 的概念

---

## 7️⃣ 生成节点 - LLM 核心

**文件**: `backend/agent/nodes/generate.py`

```python
from agent.state import AgentState
from llm.dashscope_client import call_llm

def generate_node(state: AgentState) -> AgentState:
    """
    生成节点：基于上下文生成答案
    """
    
    # 构建上下文
    context = "## 相关知识:\n"
    for doc in state.retrieved_docs:
        context += f"- {doc.get('content', '')}\n"
    
    # 构建提示词
    prompt = f"""
    基于以下知识库内容，回答用户问题：
    
    {context}
    
    用户问题: {state.question}
    
    请生成一个详细、准确、包含代码示例的回答。
    格式:
    1. 概念讲解
    2. 代码示例
    3. 常见错误
    4. 最佳实践
    """
    
    # 调用 LLM
    answer = call_llm(prompt)
    state.answer = answer
    
    return state
```

**面试要点**:
- ✅ 上下文构建
- ✅ 提示词工程
- ✅ LLM 集成

---

## 8️⃣ 验证节点 - 质量把关

**文件**: `backend/agent/nodes/validate.py`

```python
def validate_node(state: AgentState) -> AgentState:
    """
    验证节点：检查答案质量
    
    检查规则:
    ✓ 长度 > 100 字符
    ✓ 包含 markdown 代码块 (```python ... ```)
    ✓ 包含解释文本
    ✓ 字数合理 (不超过 2000)
    """
    
    answer = state.answer
    errors = []
    
    # Rule 1: 最小长度
    if len(answer) < 100:
        errors.append("Answer too short")
    
    # Rule 2: 检查代码块
    if "```" not in answer:
        errors.append("No code examples")
    
    # Rule 3: 最大长度
    if len(answer) > 2000:
        errors.append("Answer too long")
    
    # Rule 4: 关键词检查 (根据问题)
    keywords = extract_keywords(state.question)
    answer_lower = answer.lower()
    if not any(kw in answer_lower for kw in keywords):
        errors.append("Missing key concepts")
    
    state.validated = len(errors) == 0
    state.validation_errors = errors
    
    return state

def extract_keywords(question: str) -> List[str]:
    """从问题中提取关键词"""
    # 简单示例：词语分割
    return question.split()
```

**面试要点**:
- ✅ 验证机制的设计
- ✅ 质量标准的定义
- ✅ 错误收集和报告

---

## 9️⃣ RAG 引擎 - 检索核心

**文件**: `backend/rag/rag_engine.py`

```python
from llm.dashscope_client import get_embedding
from vector_store.pgvector_store import search_similar

def ask_knowledge(question: str, category: str = "default", top_k: int = 5):
    """
    RAG 查询流程:
    1. 对问题进行向量化
    2. 在向量数据库中查询相似文档
    3. 返回检索结果
    """
    
    try:
        # Step 1: 向量化问题
        question_embedding = get_embedding(question)
        # 输出: [0.2, 0.5, ..., 0.1]  # 1536维向量
        
        # Step 2: 向量相似度搜索
        similar_docs = search_similar(
            embedding=question_embedding,
            category=category,
            limit=top_k,
            threshold=0.6  # 相似度阈值
        )
        
        # Step 3: 整理结果
        sources = [
            {
                "content": doc.content,
                "source": doc.source,
                "category": doc.category,
                "similarity": doc.similarity
            }
            for doc in similar_docs
        ]
        
        return {
            "code": 0,
            "message": "success",
            "data": {
                "answer": "",  # RAG 只负责检索，不生成
                "sources": sources
            }
        }
    
    except Exception as e:
        logger.error(f"RAG 查询失败: {e}")
        return {
            "code": 1,
            "message": f"RAG query failed: {e}",
            "data": {}
        }
```

**面试要点**:
- ✅ RAG 的三个步骤
- ✅ 向量化和相似度搜索
- ✅ 错误处理

---

## 🔟 向量搜索 - PGVector

**文件**: `backend/vector_store/pgvector_store.py`

```python
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, Text, create_engine
from sqlalchemy.orm import sessionmaker

class VectorDocument(Base):
    __tablename__ = "vector_documents"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(String(255), unique=True)
    content = Column(Text)
    embedding = Column(Vector(1536))  # ← 核心：1536 维向量
    category = Column(String(100))
    source = Column(String(255))

def search_similar(embedding, category="default", limit=5, threshold=0.6):
    """
    PGVector 相似度搜索（余弦距离）
    
    SQL:
    SELECT id, content, source, 
           1 - (embedding <=> $1) as similarity
    FROM vector_documents
    WHERE category = $2 
      AND 1 - (embedding <=> $1) > $3
    ORDER BY similarity DESC
    LIMIT $4
    """
    
    session = SessionLocal()
    try:
        # <=> 是 PGVector 的余弦距离操作符
        # 1 - (a <=> b) = 余弦相似度
        similar_docs = session.query(
            VectorDocument,
            (1 - VectorDocument.embedding.cosine_distance(embedding)).label("similarity")
        ).filter(
            VectorDocument.category == category,
            (1 - VectorDocument.embedding.cosine_distance(embedding)) > threshold
        ).order_by(
            VectorDocument.embedding.cosine_distance(embedding)
        ).limit(limit).all()
        
        return similar_docs
    finally:
        session.close()

def add_document(content: str, embedding: List[float], category: str):
    """添加文档到向量数据库"""
    session = SessionLocal()
    try:
        doc = VectorDocument(
            document_id=str(uuid.uuid4()),
            content=content,
            embedding=embedding,  # numpy array or list
            category=category
        )
        session.add(doc)
        session.commit()
    finally:
        session.close()
```

**面试要点**:
- ✅ PGVector 的基本操作
- ✅ 余弦距离计算
- ✅ 向量维度的含义 (1536)
- ✅ 阈值的作用

---

## 1️⃣1️⃣ LLM 调用 - DashScope 集成

**文件**: `backend/llm/dashscope_client.py`

```python
import requests
import os

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/api/v1"

def call_llm(prompt: str, model: str = "qwen-turbo") -> str:
    """
    调用阿里通义千问 LLM
    """
    
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,  # 创意度 (0=确定性, 1=创意)
        "max_tokens": 2000    # 最大输出长度
    }
    
    response = requests.post(
        f"{DASHSCOPE_API_URL}/chat/completions",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        raise Exception(f"LLM API Error: {response.text}")

def get_embedding(text: str, model: str = "text-embedding-v1") -> List[float]:
    """
    获取文本的向量表示 (1536维)
    
    用途:
    - 将用户问题向量化
    - 将知识库文档向量化
    - 进行相似度比对
    """
    
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "input": {"texts": [text]}
    }
    
    response = requests.post(
        f"{DASHSCOPE_API_URL}/embeddings",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        embedding = result["output"]["embeddings"][0]["embedding"]
        return embedding  # 1536 维向量
    else:
        raise Exception(f"Embedding API Error: {response.text}")
```

**面试要点**:
- ✅ 外部 API 的调用方式
- ✅ API Key 的安全管理
- ✅ LLM 参数的含义 (temperature, max_tokens)
- ✅ Embedding 模型的用途

---

## 1️⃣2️⃣ Service 层 - 业务逻辑

**文件**: `backend/service/qa_service.py`

```python
from agent.runner import agent_runner
from rag.rag_engine import ask_knowledge

def ask_question(question: str, category: str = "default") -> Dict:
    """
    用户提问的主处理函数
    
    流程:
    1. 调用 Agent 处理
    2. Agent 返回答案 + metadata
    3. 保存聊天历史
    4. 返回结果
    """
    
    try:
        # 1. 运行 Agent
        agent_result = agent_runner.run(
            input={
                "question": question,
                "category": category
            }
        )
        
        # 2. 提取结果
        answer = agent_result.get("structured_output", {}).get("content", "")
        intent = agent_result.get("intent", "")
        sources = agent_result.get("sources", [])
        
        # 3. 保存到数据库
        save_to_history(
            question=question,
            answer=answer,
            category=category
        )
        
        # 4. 返回
        return {
            "answer": answer,
            "intent": intent,
            "sources": sources,
            "success": True
        }
    
    except Exception as e:
        logger.error(f"Question processing failed: {e}")
        return {
            "answer": f"处理失败: {str(e)}",
            "success": False
        }

def analyze_code(code: str) -> Dict:
    """代码分析"""
    # 直接调用 Agent 中的 code_analyze_node
    ...

def generate_exercise(topic: str) -> Dict:
    """生成习题"""
    prompt = f"生成关于 {topic} 的编程练习题"
    result = call_llm(prompt)
    return {"exercise": result}

async def upload_and_index(file, category: str):
    """上传文件并索引到知识库"""
    # 1. 读取文件
    content = await file.read()
    
    # 2. 解析文档 (PDF/DOCX)
    text = parse_document(content)
    
    # 3. 分块
    chunks = chunk_text(text, chunk_size=500)
    
    # 4. 向量化并存储
    for chunk in chunks:
        embedding = get_embedding(chunk)
        add_document(
            content=chunk,
            embedding=embedding,
            category=category,
            source=file.filename
        )
    
    return {"status": "success", "chunks_added": len(chunks)}
```

**面试要点**:
- ✅ 业务流程的组织
- ✅ 错误处理
- ✅ 调用链路清晰
- ✅ 异步处理 (async/await)

---

## 1️⃣3️⃣ 数据库模型

**文件**: `backend/models/chat.py`

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class ChatRecord(Base):
    """聊天记录表"""
    __tablename__ = "chat_records"
    
    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    category = Column(String(100), default="default")
    intent = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ChatRecord id={self.id} category={self.category}>"

# 数据库初始化
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db")

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(bind=engine)

def init_db():
    """初始化数据库"""
    Base.metadata.create_all(engine)
    logger.info("✅ Database initialized")

def get_session():
    """获取数据库会话"""
    return SessionLocal()
```

**面试要点**:
- ✅ SQLAlchemy ORM
- ✅ 表设计 (字段、索引)
- ✅ 连接池配置
- ✅ 初始化流程

---

## 1️⃣4️⃣ Docker Compose 编排

**文件**: `compose.yaml`

```yaml
version: '3.8'

services:
  # PostgreSQL + PGVector
  postgres:
    image: pgvector/pgvector:pg16-latest
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ai_coding_tutor
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI 后端
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/ai_coding_tutor
      DASHSCOPE_API_KEY: ${DASHSCOPE_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2

  # React 前端
  frontend:
    build:
      context: frontend/vite-project
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: http://localhost:8000

volumes:
  postgres_data:
```

**面试要点**:
- ✅ 多服务编排
- ✅ 网络通信 (postgres → backend 直接连接)
- ✅ 环境变量注入
- ✅ 健康检查

---

## 1️⃣5️⃣ 前端调用示例

**文件**: `frontend/vite-project/src/ChatApp.jsx`

```jsx
import { useState } from 'react';

export default function ChatApp() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState([]);

  const handleAsk = async () => {
    setLoading(true);
    try {
      // 调用后端 API
      const response = await fetch('/api/v1/chat/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question,
          category: 'python'
        })
      });

      const data = await response.json();
      
      // 显示结果
      setAnswer(data.answer);
      setSources(data.sources);
    } catch (error) {
      setAnswer(`错误: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-app">
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="提问..."
        className="input"
      />
      <button onClick={handleAsk} disabled={loading}>
        {loading ? '思考中...' : '提问'}
      </button>
      
      {answer && (
        <div>
          <h3>答案:</h3>
          <p>{answer}</p>
          {sources.length > 0 && (
            <div>
              <h4>来源:</h4>
              <ul>
                {sources.map((src, i) => (
                  <li key={i}>{src}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

**面试要点**:
- ✅ API 的调用方式
- ✅ 异步处理和加载状态
- ✅ 错误处理
- ✅ 前后端交互

---

## 📋 使用这个速查表的方法

### 方法1: 快速复习
在面试前30分钟，从上到下过一遍这15个代码片段。

### 方法2: 深度理解
选一个你不够熟悉的片段，读代码，在脑子里跑一遍逻辑。

### 方法3: 面试时查阅
如果被问到某个模块，可以快速定位这个表中的对应片段。

### 方法4: 实际操作
可以在 IDE 中打开对应文件，指着代码讲解面试官。

---

## 🎯 按流程组织的学习路径

如果想按流程深入理解每一步，可以这样看：

**第1步: 项目启动** → 代码 #1 (main.py)  
**第2步: 用户请求** → 代码 #2 (api/v1/chat.py)  
**第3步: Agent 处理** → 代码 #3 (agent/graph.py)  
**第4步: 意图识别** → 代码 #5 (analyze_node)  
**第5步: 知识检索** → 代码 #6 (retrieve_node)  
**第6步: 向量搜索** → 代码 #10 (pgvector_store.py)  
**第7步: LLM 生成** → 代码 #7 (generate_node) + #11 (dashscope_client)  
**第8步: 质量验证** → 代码 #8 (validate_node)  
**第9步: 返回结果** → 代码 #15 (前端展示)  

---

## 💡 需要进一步讨论的话题

如果面试官问了这个表中的每个代码片段都有的问题，你就可以说：

- "这个我刚才讲的 #3 代码里有..."
- "您看 #10 的向量搜索部分..."
- "就像 #8 验证节点中的逻辑..."

这样显得你对代码非常熟悉！

---

**Created**: 2026年4月  
**Completeness**: 95% 覆盖核心代码  
**ReadinessForInterview**: ✅ Ready
