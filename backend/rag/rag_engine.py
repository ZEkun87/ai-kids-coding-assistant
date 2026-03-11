# backend/rag/rag_engine.py
import logging
import uuid
from functools import lru_cache
from typing import List, Optional, Dict, Any

from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatTongyi

from .vector_store import get_vector_store

logger = logging.getLogger(__name__)
MAX_QUERY_LENGTH = 1000

# ------------------ 工具函数 ------------------
def validate_query(query: str) -> str:
    """
    校验用户输入
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f"Query too long, max {MAX_QUERY_LENGTH} characters")
    return query.strip()

@lru_cache(maxsize=1)
def get_db():
    """
    单例加载向量数据库
    """
    logger.info("Loading vector database...")
    return get_vector_store()

@lru_cache(maxsize=2)
def get_llm(model_name: str, temperature: float):
    """
    单例 LLM 获取
    """
    return ChatTongyi(model=model_name, temperature=temperature)

# ------------------ 核心 RAG 查询 ------------------
def ask_knowledge(
    question: str,
    model_name: str = "qwen-turbo",
    temperature: float = 0.1,
    search_k: int = 3,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    RAG 查询核心函数

    Args:
        question: 用户提问
        model_name: LLM 模型名称
        temperature: 回答随机性
        search_k: 向量数据库 Top K
        category: 知识库分类，可选

    Returns:
        dict: {
            code: 0/500,
            message: "success"/error message,
            data: {
                answer: str,
                sources: List[str]
            }
        }
    """
    request_id = str(uuid.uuid4())
    try:
        question = validate_query(question)
        vectordb = get_db()

        # 支持按 category 查询
        retriever_kwargs = {"search_kwargs": {"k": search_k}}
        if category:
            retriever_kwargs["search_kwargs"]["filter"] = {"category": category}

        retriever = vectordb.as_retriever(**retriever_kwargs)
        llm = get_llm(model_name, temperature)

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )

        logger.info(f"[{request_id}] question: {question}, category: {category}, model: {model_name}")

        response = qa_chain({"query": question})
        answer = response.get("result", "")
        sources = [
            doc.page_content
            for doc in response.get("source_documents", [])
        ]

        logger.info(f"[{request_id}] RAG success, answer length: {len(answer)}")

        return {
            "code": 0,
            "message": "success",
            "data": {
                "answer": answer,
                "sources": sources
            }
        }

    except Exception as e:
        logger.exception(f"[{request_id}] RAG error")
        return {
            "code": 500,
            "message": str(e),
            "data": None
        }