"""
PostgreSQL + PGVector 向量存储实现
替代 Chroma，用于知识库的向量相似度搜索
"""

import logging
import os
from typing import Dict, List, Optional, Any
import numpy as np

from sqlalchemy import Column, String, Integer, Text, Float, create_engine, func, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pgvector.sqlalchemy import Vector

# PostgreSQL连接URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ai_coding_tutor"
)

# 创建引擎和会话
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

logger = logging.getLogger(__name__)

# 向量维度（DashScope embedding model: text-embedding-v1 输出维度为1536）
EMBEDDING_DIMENSION = 1536


class VectorDocument(Base):
    """向量文档存储表"""

    __tablename__ = "vector_documents"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), unique=True, index=True)  # 文档唯一标识
    content = Column(Text, nullable=False)  # 文档内容
    embedding = Column(Vector(EMBEDDING_DIMENSION), nullable=False)  # 向量
    category = Column(String(100), default="default", index=True)  # 分类
    source = Column(String(255), default="unknown")  # 来源
    metadata_json = Column(Text, default="{}")  # 元数据JSON

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "content": self.content,
            "category": self.category,
            "source": self.source,
        }


def init_vector_db() -> None:
    return
    """初始化向量数据库"""
    try:
        # 创建表
        Base.metadata.create_all(engine)

        # 启用pgvector扩展
        session = SessionLocal()
        try:
            session.execute("CREATE EXTENSION IF NOT EXISTS vector")
            session.commit()
            logger.info("✅ PGVector扩展已启用")
        except Exception as e:
            session.rollback()
            logger.warning(f"⚠️ PGVector扩展状态: {e}")
        finally:
            session.close()

        logger.info("✅ 向量数据库初始化完成")
    except Exception as e:
        logger.error(f"❌ 向量数据库初始化失败: {e}")
        raise


def add_document(
    content: str,
    embedding: List[float],
    category: str = "default",
    source: str = "unknown",
    document_id: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> VectorDocument:
    """添加文档到向量库"""
    session = SessionLocal()
    try:
        import json

        # 生成document_id（如果未提供）
        if not document_id:
            import hashlib

            document_id = hashlib.md5(content.encode()).hexdigest()

        # 检查是否已存在
        existing = (
            session.query(VectorDocument)
            .filter(VectorDocument.document_id == document_id)
            .first()
        )

        if existing:
            # 更新现有文档
            existing.content = content
            existing.embedding = embedding
            existing.category = category
            existing.source = source
            existing.metadata_json = json.dumps(metadata or {})
            session.commit()
            return existing

        # 创建新文档
        doc = VectorDocument(
            document_id=document_id,
            content=content,
            embedding=embedding,
            category=category,
            source=source,
            metadata_json=json.dumps(metadata or {}),
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        return doc
    except Exception as e:
        session.rollback()
        logger.error(f"❌ 添加文档失败: {e}")
        raise
    finally:
        session.close()


def search_similar(
    query_embedding: List[float],
    category: Optional[str] = None,
    limit: int = 5,
    threshold: float = 0.0,
) -> List[Dict[str, Any]]:
    """相似度搜索"""
    session = SessionLocal()
    try:
        query_vec = query_embedding

        # 构建查询
        q = session.query(
            VectorDocument,
            VectorDocument.embedding.cosine_distance(query_vec).label("similarity"),
        )

        if category:
            q = q.filter(VectorDocument.category == category)

        # 按相似度排序并限制结果
        results = q.order_by("similarity").limit(limit).all()

        return [
            {
                "document_id": r[0].document_id,
                "content": r[0].content,
                "category": r[0].category,
                "source": r[0].source,
                "similarity": float(1.0 - r[1]),  # 转换距离为相似度
            }
            for r in results
            if (1.0 - r[1]) >= threshold  # 过滤低于阈值的结果
        ]
    except Exception as e:
        logger.error(f"❌ 搜索失败: {e}")
        return []
    finally:
        session.close()


def delete_document(document_id: str) -> bool:
    """删除文档"""
    session = SessionLocal()
    try:
        session.query(VectorDocument).filter(
            VectorDocument.document_id == document_id
        ).delete()
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"❌ 删除文档失败: {e}")
        return False
    finally:
        session.close()


def delete_by_category(category: str) -> int:
    """删除某分类的所有文档"""
    session = SessionLocal()
    try:
        count = (
            session.query(VectorDocument)
            .filter(VectorDocument.category == category)
            .delete()
        )
        session.commit()
        return count
    except Exception as e:
        session.rollback()
        logger.error(f"❌ 删除分类文档失败: {e}")
        return 0
    finally:
        session.close()


def list_documents(category: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """列出文档"""
    session = SessionLocal()
    try:
        query = session.query(VectorDocument)
        if category:
            query = query.filter(VectorDocument.category == category)

        docs = query.limit(limit).all()
        return [doc.to_dict() for doc in docs]
    finally:
        session.close()


def get_document_count(category: Optional[str] = None) -> int:
    """获取文档数量"""
    session = SessionLocal()
    try:
        query = session.query(func.count(VectorDocument.id))
        if category:
            query = query.filter(VectorDocument.category == category)
        return query.scalar() or 0
    finally:
        session.close()


def clear_all() -> int:
    """清空所有文档"""
    session = SessionLocal()
    try:
        count = session.query(VectorDocument).delete()
        session.commit()
        return count
    except Exception as e:
        session.rollback()
        logger.error(f"❌ 清空数据库失败: {e}")
        return 0
    finally:
        session.close()
