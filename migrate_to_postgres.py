#!/usr/bin/env python3
"""
从SQLite + Chroma迁移到PostgreSQL + PGVector的迁移脚本
"""

import logging
import sys
import os
from pathlib import Path

# 添加backend路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_chat_history():
    """迁移聊天历史记录"""
    try:
        from models.chat import SessionLocal as NewSession, ChatRecord as NewChatRecord
        from datetime import datetime, timezone

        logger.info("🔄 开始迁移聊天历史...")

        # 检查旧SQLite数据库
        old_db_path = Path(__file__).parent / "backend" / "chat_history.db"
        if not old_db_path.exists():
            logger.info("⚠️  未找到旧SQLite数据库，跳过迁移")
            return 0

        # 连接旧数据库并迁移
        from sqlalchemy import create_engine, Column, Integer, String, DateTime, inspect
        from sqlalchemy.orm import sessionmaker, declarative_base

        old_db_url = f"sqlite:///{old_db_path}"
        old_engine = create_engine(
            old_db_url, connect_args={"check_same_thread": False}
        )
        OldSession = sessionmaker(bind=old_engine)
        old_session = OldSession()

        # 检查旧表是否存在
        inspector = inspect(old_engine)
        if "chat_records" not in inspector.get_table_names():
            logger.info("⚠️  旧数据库中未找到chat_records表")
            return 0

        # 读取旧记录
        Base = declarative_base()

        class OldChatRecord(Base):
            __tablename__ = "chat_records"
            id = Column(Integer, primary_key=True)
            question = Column(String)
            answer = Column(String)
            category = Column(String, default="default")
            date = Column(DateTime)

        Base.metadata.reflect(bind=old_engine)
        old_records = old_session.query(OldChatRecord).all()

        logger.info(f"📋 找到 {len(old_records)} 条旧记录")

        # 迁移到新数据库
        new_session = NewSession()
        migrated = 0

        for old_record in old_records:
            try:
                new_record = NewChatRecord(
                    question=old_record.question,
                    answer=old_record.answer,
                    category=old_record.category,
                    date=old_record.date or datetime.now(timezone.utc),
                )
                new_session.add(new_record)
                migrated += 1
            except Exception as e:
                logger.warning(f"⚠️  迁移记录失败: {e}")
                continue

        new_session.commit()
        new_session.close()
        old_session.close()

        logger.info(f"✅ 成功迁移 {migrated} 条聊天记录")
        return migrated

    except Exception as e:
        logger.error(f"❌ 聊天历史迁移失败: {e}")
        return 0


def migrate_vector_store():
    """迁移向量存储"""
    try:
        from vector_store.pgvector_store import add_document
        from langchain_community.embeddings import DashScopeEmbeddings
        import os

        logger.info("🔄 开始迁移向量存储...")

        # 检查旧Chroma数据库
        chroma_path = Path(__file__).parent / "backend" / "chroma_db"
        if not chroma_path.exists():
            logger.info("⚠️  未找到旧Chroma数据库，跳过迁移")
            return 0

        try:
            import chromadb
        except ImportError:
            logger.warning("⚠️  未安装chromadb，跳过向量存储迁移")
            return 0

        # 连接旧Chroma数据库
        try:
            client = chromadb.PersistentClient(path=str(chroma_path))
            collections = client.list_collections()
            logger.info(f"📦 找到 {len(collections)} 个集合")
        except Exception as e:
            logger.warning(f"⚠️  无法读取Chroma数据库: {e}")
            return 0

        # 初始化embedding模型
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            logger.warning("⚠️  未设置DASHSCOPE_API_KEY，跳过向量迁移")
            return 0

        embeddings = DashScopeEmbeddings(
            model="text-embedding-v1", dashscope_api_key=api_key
        )
        migrated = 0

        # 迁移每个集合
        for collection in collections:
            try:
                coll = client.get_collection(name=collection.name)
                documents = coll.get(include=["embeddings", "documents", "metadatas"])

                logger.info(
                    f"🔄 迁移集合 '{collection.name}': {len(documents['documents'])} 条文档"
                )

                for idx, doc in enumerate(documents["documents"]):
                    try:
                        embedding = (
                            documents["embeddings"][idx]
                            if documents["embeddings"]
                            else None
                        )
                        metadata = (
                            documents["metadatas"][idx]
                            if documents["metadatas"]
                            else {}
                        )

                        # 如果没有embedding则重新计算
                        if not embedding:
                            embedding = embeddings.embed_query(doc)

                        add_document(
                            content=doc,
                            embedding=embedding,
                            category=metadata.get("category", collection.name),
                            source=metadata.get("source", "chroma"),
                            metadata=metadata,
                        )
                        migrated += 1
                    except Exception as e:
                        logger.warning(f"⚠️  迁移文档失败: {e}")
                        continue
            except Exception as e:
                logger.warning(f"⚠️  迁移集合 '{collection.name}' 失败: {e}")
                continue

        logger.info(f"✅ 成功迁移 {migrated} 个向量文档")
        return migrated

    except Exception as e:
        logger.error(f"❌ 向量存储迁移失败: {e}")
        return 0


def main():
    """主迁移函数"""
    logger.info("=" * 50)
    logger.info("🚀 从SQLite+Chroma迁移到PostgreSQL+PGVector")
    logger.info("=" * 50)

    # 检查PostgreSQL连接
    try:
        from models.chat import engine

        with engine.connect() as conn:
            logger.info("✅ PostgreSQL连接成功")
    except Exception as e:
        logger.error(f"❌ PostgreSQL连接失败: {e}")
        logger.error("请确保PostgreSQL已启动和.env配置正确")
        return False

    # 执行迁移
    chat_count = migrate_chat_history()
    vector_count = migrate_vector_store()

    logger.info("=" * 50)
    logger.info(f"📊 迁移摘要:")
    logger.info(f"  • 聊天历史: {chat_count} 条记录")
    logger.info(f"  • 向量文档: {vector_count} 个文档")
    logger.info("=" * 50)

    if chat_count > 0 or vector_count > 0:
        logger.info("✅ 迁移完成!")
        logger.info("💡 建议: 迁移完成后可以删除旧的SQLite和Chroma数据库")
        return True
    else:
        logger.info("⚠️  未找到可迁移的数据")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
