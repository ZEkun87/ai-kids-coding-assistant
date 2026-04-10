# vector_store.py
import os
import logging
import threading
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain_community.embeddings import DashScopeEmbeddings

# ================= 配置 =================

# Use environment variable if set, otherwise use relative path for local dev
# Docker containers should set PERSIST_DIR env var
if os.getenv("PERSIST_DIR"):
    PERSIST_DIR = os.getenv("PERSIST_DIR")
else:
    # Local development: store in backend/vector_db
    BASE_DIR = Path(__file__).resolve().parent.parent
    PERSIST_DIR = str(BASE_DIR / "vector_db")

COLLECTION_NAME = "knowledge_base"
EMBEDDING_MODEL = "text-embedding-v1"

API_KEY = os.getenv("DASHSCOPE_API_KEY")

# ================= Logging Setup (Don't override app-level config) =================
# Get logger without basicConfig - let FastAPI/app handle loggingogger = logging.getLogger(__name__)

# ================= 单例缓存 =================

_vector_db_client = None
_lock = threading.Lock()

# ================= Embedding =================


def get_embeddings():
    if not API_KEY:
        raise ValueError("DASHSCOPE_API_KEY 未设置")
    return DashScopeEmbeddings(model=EMBEDDING_MODEL, dashscope_api_key=API_KEY)


# ================= Vector Store =================


def get_vector_store():
    global _vector_db_client
    if _vector_db_client is not None:
        return _vector_db_client

    with _lock:
        if _vector_db_client is not None:
            return _vector_db_client

        try:
            logger.info("Initializing Chroma Vector DB")

            # Docker 容器中确保目录存在且可写
            os.makedirs(PERSIST_DIR, exist_ok=True)

            # 使用 PersistentClient，避免多次初始化冲突
            client = chromadb.PersistentClient(
                path=PERSIST_DIR,
                settings=Settings(
                    allow_reset=False,  # False 表示不会重置已有数据
                    anonymized_telemetry=False,
                ),
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
            logger.error(f"Vector DB initialization failed: {e}")
            raise


# ================= Retriever =================


def get_retriever(k=3):
    vectordb_client = get_vector_store()
    collection = vectordb_client.get_collection(COLLECTION_NAME)
    return collection.as_retriever(search_kwargs={"k": k})


"""
if __name__ == "__main__":
    # 1. 测试 Embedding 生成
    embeddings = get_embeddings()
    text = "Python 循环的用法"
    vector = embeddings.embed_query(text)
    print(f"文本「{text}」的向量长度：{len(vector)}")  # 输出 768（text-embedding-v1 维度）

    # 2. 测试向量库初始化
    client = get_vector_store()
    print(f"向量库集合列表：{[c.name for c in client.list_collections()]}")  # 输出 ['knowledge_base']

    # 3. 测试检索器
    retriever = get_retriever(k=2)
    # 先向集合中添加测试数据
    collection = client.get_collection(COLLECTION_NAME)
    collection.add(
        documents=["Python for 循环语法：for i in range(10): print(i)", 
                   "Python while 循环语法：while 条件: 执行代码"],
        ids=["doc1", "doc2"],
        embeddings=[embeddings.embed_query("Python for 循环"), 
                    embeddings.embed_query("Python while 循环")]
    )
    # 检索相似文本
    results = retriever.get_relevant_documents("Python 循环怎么写")
    print("检索结果：")
    for doc in results:
        print(f"- {doc.page_content}")  # 输出最相似的 2 条文本
"""
