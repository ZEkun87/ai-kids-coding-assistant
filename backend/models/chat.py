from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = "sqlite:///chat_history.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ChatRecord(Base):
    __tablename__ = "chat_records"

    id = Column(Integer, primary_key=True)
    question = Column(String)
    answer = Column(String)
    category = Column(String, default="default")
    date = Column(DateTime, default=datetime.utcnow)


def init_db() -> None:
    Base.metadata.create_all(engine)


def save_chat(question: str, answer: str, category: str = "default") -> None:
    session = SessionLocal()
    try:
        session.add(ChatRecord(question=question, answer=answer, category=category))
        session.commit()
    finally:
        session.close()


def get_history(category: str | None = None, limit: int = 20) -> list[dict]:
    session = SessionLocal()
    try:
        query = session.query(ChatRecord)
        if category:
            query = query.filter(ChatRecord.category == category)
        records = query.order_by(ChatRecord.date.desc()).limit(limit).all()
        return [
            {
                "question": item.question,
                "answer": item.answer,
                "category": item.category,
                "date": item.date.isoformat(),
            }
            for item in records
        ]
    finally:
        session.close()
