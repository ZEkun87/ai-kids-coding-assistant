import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# PostgreSQL connection URL
# Format: postgresql://user:password@host:port/database
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ai_coding_tutor"
)

# Create engine with PostgreSQL-optimized settings
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Connection pool size
    max_overflow=40,  # Max overflow connections
    pool_pre_ping=True,  # Test connection before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_reset_on_return="rollback",  # Reset connection state
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()


class ChatRecord(Base):
    """Chat conversation history records"""

    __tablename__ = "chat_records"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False, index=True)
    answer = Column(String, nullable=False)
    category = Column(String, default="default", index=True)
    date = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )


def init_db() -> None:
    """Initialize database and create tables"""
    Base.metadata.create_all(engine)


def save_chat(question: str, answer: str, category: str = "default") -> ChatRecord:
    """Save chat record to database"""
    session = SessionLocal()
    try:
        record = ChatRecord(question=question, answer=answer, category=category)
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_history(category: Optional[str] = None, limit: int = 20) -> list[dict]:
    """Get chat history from database"""
    session = SessionLocal()
    try:
        query = session.query(ChatRecord)
        if category:
            query = query.filter(ChatRecord.category == category)
        records = query.order_by(ChatRecord.date.desc()).limit(limit).all()
        return [
            {
                "id": item.id,
                "question": item.question,
                "answer": item.answer,
                "category": item.category,
                "date": item.date.isoformat(),
            }
            for item in records
        ]
    finally:
        session.close()


def delete_old_records(days: int = 30) -> int:
    """Delete records older than specified days"""
    from sqlalchemy import and_

    session = SessionLocal()
    try:
        cutoff_date = datetime.now(timezone.utc)
        from datetime import timedelta

        cutoff_date = cutoff_date - timedelta(days=days)

        deleted = (
            session.query(ChatRecord).filter(ChatRecord.date < cutoff_date).delete()
        )
        session.commit()
        return deleted
    finally:
        session.close()
