# backend/main.py
import hashlib
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import os, io, logging, uuid, time, shutil
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
import dashscope
from dashscope import Generation, TextEmbedding
from PyPDF2 import PdfReader
from docx import Document
import chromadb
from chromadb.config import Settings
import threading

# ---------------- 初始化 ----------------
load_dotenv()
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI 少儿编程助手")

# CORS 支持前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- 数据库 / 聊天记录 ----------------
engine = create_engine("sqlite:///chat_history.db")
Session = sessionmaker(bind=engine)
Base = declarative_base()

class ChatRecord(Base):
    __tablename__ = "chat_records"
    id = Column(Integer, primary_key=True)
    question = Column(String)
    answer = Column(String)
    category = Column(String, default="default")
    date = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

def save_chat(question, answer, category="default"):
    session = Session()
    session.add(ChatRecord(question=question, answer=answer, category=category))
    session.commit()
    session.close()
# 1. 创建数据库引擎：连接当前目录下的chat_history.db（SQLite文件数据库）
#    作用：建立Python代码和SQLite数据库的通信通道
"""
engine = create_engine("sqlite:///chat_history.db")

# 2. 创建会话工厂：基于上面的引擎，生成可操作数据库的会话类
#    作用：后续用Session()创建会话，就能执行增删改查
Session = sessionmaker(bind=engine)

# 3. 创建ORM模型基类：所有数据库表模型都要继承这个基类
#    作用：让SQLAlchemy识别“哪些类是数据库表”
Base = declarative_base()

# 4. 定义ChatRecord类（继承Base）：映射数据库中的chat_records表
class ChatRecord(Base):
    # 5. 指定该类对应的数据库表名：chat_records
    __tablename__ = "chat_records"
    
    # 6. 定义字段：id（整数类型，主键，唯一标识每条记录，SQLite会自动自增）
    id = Column(Integer, primary_key=True)
    
    # 7. 定义字段：question（字符串类型，存储用户的问题）
    question = Column(String)
    
    # 8. 定义字段：answer（字符串类型，存储AI的回答）
    answer = Column(String)
    
    # 9. 定义字段：category（字符串类型，默认值"default"，存储问题分类）
    category = Column(String, default="default")
    
    # 10. 定义字段：date（时间类型，默认值为当前UTC时间，存储记录创建时间）
    date = Column(DateTime, default=datetime.utcnow)

# 11. 自动创建表：扫描所有继承Base的类（这里是ChatRecord），在数据库中创建对应的表
#     特点：如果表已存在，不会重复创建，也不会覆盖原有数据
Base.metadata.create_all(engine)

# 12. 定义函数：save_chat（封装保存聊天记录的逻辑，方便调用）
def save_chat(question, answer, category="default"):
    # 13. 创建数据库会话：相当于打开一个数据库连接
    session = Session()
    
    # 14. 创建ChatRecord实例（对应一条聊天记录），并添加到会话中
    #     作用：把要保存的数据暂存到会话里，还没真正写入数据库
    session.add(ChatRecord(question=question, answer=answer, category=category))
    
    # 15. 提交会话：把暂存的记录真正写入数据库（这一步才是“保存”的核心）
    session.commit()
    
    # 16. 关闭会话：释放数据库连接（避免资源泄露）
    session.close()
"""
# ---------------- 数据模型 ----------------
class QuestionRequest(BaseModel):
    question: str
    category: str = "default"

class CodeRequest(BaseModel):
    code: str

class TopicRequest(BaseModel):
    topic: str

# ---------------- DashScope 调用 ----------------
def call_dashscope(prompt: str, temperature=0.7, max_tokens=1000) -> str:
    try:
        response = Generation.call(
            model='qwen-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            result_format='text'
        )
        text = getattr(response.output, 'text', None)
        if text is None and hasattr(response.output, '__iter__'):
            text = ' '.join([getattr(o, 'text', '') for o in response.output])
        if text is None:
            text = str(response.output)
        return text.strip()
    except Exception as e:
        logger.error(f"DashScope API error: {e}")
        raise HTTPException(status_code=500, detail=f"通义千问调用失败：{str(e)}")

# ---------------- DashScope 嵌入函数 ----------------
def dashscope_embedding(texts: list[str]) -> list[list[float]]:
    """生成向量，若失败则用 MD5 降级"""
    if not texts:
        return []
    try:
        response = TextEmbedding.call(
            model="text-embedding-v1",
            input=texts
        )
        vectors = [item['embedding'] for item in response.output['embeddings']]
        return vectors
    except Exception as e:
        logger.error(f"Embedding 生成失败：{e}")
        vectors = []
        for t in texts:
            h = int(hashlib.md5(t.encode()).hexdigest(), 16)
            v = [(h >> (i*8)) % 256 / 255.0 for i in range(32)]
            vectors.append(v)
        return vectors

# ---------------- ChromaDB 初始化 ----------------
VECTOR_DB_PATH = "./vector_db"

VECTOR_DB_PATH = "/app/vector_db"  # Docker 中使用绝对路径
COLLECTION_NAME = "documents"

_vector_db_client = None
_lock = threading.Lock()

def get_vector_db_client():
    """初始化并返回 Chroma PersistentClient（单例，线程安全）"""
    global _vector_db_client
    if _vector_db_client is not None:
        return _vector_db_client

    with _lock:
        if _vector_db_client is not None:
            return _vector_db_client

        try:
            # 确保路径存在
            os.makedirs(VECTOR_DB_PATH, exist_ok=True)

            client = chromadb.PersistentClient(
                path=VECTOR_DB_PATH,
                settings=Settings(
                    allow_reset=False,  # 不清空已有数据
                    anonymized_telemetry=False
                )
            )

            # 创建或获取 collection
            if COLLECTION_NAME not in [c.name for c in client.list_collections()]:
                client.create_collection(COLLECTION_NAME)
                logger.info(f"Created collection: {COLLECTION_NAME}")
            else:
                logger.info(f"Collection exists: {COLLECTION_NAME}")

            _vector_db_client = client
            return client

        except Exception as e:
            logger.error(f"Chroma DB init failed: {e}")
            raise

def get_collection():
    client = get_vector_db_client()
    return client.get_collection(COLLECTION_NAME)


# ---------------- Vector DB 操作 ----------------
def save_documents_to_vector_db(texts, category="default"):
    """将文本存入 Chroma 向量数据库"""
    if not texts:
        return
    texts = [t.strip() for t in texts if t.strip()]
    if not texts:
        return
    vectors = dashscope_embedding(texts)
    ids = [f"doc_{uuid.uuid4()}" for _ in texts]
    metadatas = [{"category": category} for _ in texts]
    collection = get_collection()
    collection.add(
        documents=texts,
        embeddings=vectors,
        metadatas=metadatas,
        ids=ids
    )

def query_vector_db(query_text, top_k=3):
    """查询 Chroma 向量数据库"""
    if not query_text.strip():
        return []
    query_vector = dashscope_embedding([query_text])[0]
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
    )
    return [d for d in results['documents'][0]] if results['documents'] else []


def save_documents_to_vector_db(texts, category="default"):
    if not texts:
        return
    texts = [t.strip() for t in texts if t.strip()]
    if not texts:
        return
    vectors = dashscope_embedding(texts)
    ids = [f"doc_{uuid.uuid4()}" for _ in texts]
    metadatas = [{"category": category} for _ in texts]
    collection.add(
        documents=texts,
        embeddings=vectors,
        metadatas=metadatas,
        ids=ids
    )

def query_vector_db(query_text, top_k=3):
    if not query_text.strip():
        return []
    query_vector = dashscope_embedding([query_text])[0]
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
    )
    return [d for d in results['documents'][0]] if results['documents'] else []

# ---------------- 核心接口 ----------------
@app.get("/")
def read_root():
    return {"message": "AI 少儿编程助手运行中"}

@app.post("/ask")
def ask_question(request: QuestionRequest):
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Ask question: {request.question}, category: {request.category}")
    docs = query_vector_db(request.question, top_k=3)
    context = "\n".join(docs) if docs else "无参考文档"
    prompt = f"""
你是少儿编程辅导老师，用简单语言回答以下问题：{request.question}
参考文档：
{context}

要求：1. 适合小学生/初中生理解；2. 语气友好；3. 引导思考而非直接给答案。
"""
    answer = call_dashscope(prompt, temperature=0.7)
    save_chat(request.question, answer, request.category)
    return {"answer": answer, "request_id": request_id, "sources": docs}

@app.post("/analyze")
def analyze_code_endpoint(request: CodeRequest):
    prompt = f"""
分析以下少儿Python代码：{request.code}
要求：1. 指出语法错误/逻辑问题；2. 给出简单修改建议；3. 用少儿能懂的语言解释。
"""
    result = call_dashscope(prompt, temperature=0.5)
    return {"analysis": result}

@app.post("/exercise")
def generate_exercise_endpoint(request: TopicRequest):
    prompt = f"""
为少儿编程初学者生成关于「{request.topic}」的练习题：
要求：1. 难度适合小学生；2. 包含题目描述+简单提示；3. 不要给出答案。
"""
    result = call_dashscope(prompt, temperature=0.8)
    return {"exercise": result}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), category: str = Query("default")):
    try:
        content = await file.read()
        filename = file.filename.lower()
        texts = []
        if filename.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(content))
            texts = [p.extract_text() for p in reader.pages if p.extract_text()]
        elif filename.endswith(".docx"):
            doc = Document(io.BytesIO(content))
            texts = [p.text for p in doc.paragraphs if p.text.strip()]
        else:
            texts = content.decode(errors="ignore").split("\n")
        texts = [t.strip() for t in texts if t.strip()]
        save_documents_to_vector_db(texts, category)
        logger.info(f"Uploaded {len(texts)} docs to category: {category}")
        return {
            "status": "success", 
            "count": len(texts), 
            "category": category,
            "msg": "文档已成功入库 RAG 知识库"
        }
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=f"文件处理失败：{str(e)}")

@app.get("/history")
def get_history(category: str = None, limit: int = 20):
    session = Session()
    query = session.query(ChatRecord)
    if category:
        query = query.filter(ChatRecord.category == category)
    records = query.order_by(ChatRecord.date.desc()).limit(limit).all()
    session.close()
    return [
        {"question": r.question, "answer": r.answer, "category": r.category, "date": r.date.isoformat()}
        for r in records
    ]

@app.post("/ask-stream")
def ask_stream(request: QuestionRequest):
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Stream question: {request.question}, category: {request.category}")

    def generator():
        try:
            docs = query_vector_db(request.question, top_k=3)
            context = "\n".join(docs) if docs else "无参考文档"
            prompt = f"""
你是少儿编程辅导老师，用简单语言回答以下问题：{request.question}
参考文档：
{context}

要求：1. 适合小学生/初中生理解；2. 语气友好；3. 引导思考而非直接给答案。
"""
            answer = call_dashscope(prompt)
            for line in answer.split("\n"):
                if line.strip():
                    yield line + "\n"
                    time.sleep(0.05)
        except Exception as e:
            logger.error(f"流式回答失败：{e}")
            yield "抱歉，回答生成失败，请稍后再试～\n"

    return StreamingResponse(generator(), media_type="text/event-stream")


# ---------------- 启动 ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)