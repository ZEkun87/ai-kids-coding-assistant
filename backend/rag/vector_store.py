# vector_store.py
import os
import logging
import threading

import chromadb
from chromadb.config import Settings
from langchain_community.embeddings import DashScopeEmbeddings

# ================= 配置 =================

PERSIST_DIR = "/app/vector_db"  # Docker 中最好用绝对路径
COLLECTION_NAME = "knowledge_base"
EMBEDDING_MODEL = "text-embedding-v1"

API_KEY = os.getenv("DASHSCOPE_API_KEY")

# ================= 日志 =================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ================= 单例缓存 =================

_vector_db_client = None
_lock = threading.Lock()

# ================= Embedding =================

def get_embeddings():
    if not API_KEY:
        raise ValueError("DASHSCOPE_API_KEY 未设置")
    return DashScopeEmbeddings(
        model=EMBEDDING_MODEL,
        dashscope_api_key=API_KEY
    )

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
            logger.error(f"Vector DB initialization failed: {e}")
            raise

# ================= Retriever =================

def get_retriever(k=3):
    vectordb_client = get_vector_store()
    collection = vectordb_client.get_collection(COLLECTION_NAME)
    return collection.as_retriever(search_kwargs={"k": k})