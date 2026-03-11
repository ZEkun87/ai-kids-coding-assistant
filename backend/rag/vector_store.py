# 通义千问 + Chroma 向量数据库封装

import os
import logging
import threading

from langchain_community.embeddings import DashScopeEmbeddings
from langchain.vectorstores import Chroma


# ================= 配置 =================

PERSIST_DIR = "vector_db"
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

_vector_db = None
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

    global _vector_db

    if _vector_db is not None:
        return _vector_db

    with _lock:

        if _vector_db is not None:
            return _vector_db

        try:

            logger.info("Initializing Chroma Vector DB")

            os.makedirs(PERSIST_DIR, exist_ok=True)

            embeddings = get_embeddings()

            vectordb = Chroma(

                collection_name=COLLECTION_NAME,
                persist_directory=PERSIST_DIR,
                embedding_function=embeddings

            )

            _vector_db = vectordb

            logger.info("Vector DB initialized successfully")

            return vectordb

        except Exception as e:

            logger.error(f"Vector DB initialization failed: {e}")

            raise


# ================= Retriever =================

def get_retriever(k=3):

    vectordb = get_vector_store()

    return vectordb.as_retriever(
        search_kwargs={"k": k}
    )