import os
import uuid
from typing import List, Optional
from datetime import datetime
from loguru import logger
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Session
from dotenv import load_dotenv
from domain.entities.message import Message, MessageRole, Source
from domain.entities.conversation import Conversation
from domain.repositories.memory_repository import MemoryRepository

load_dotenv()


class Base(DeclarativeBase):
    pass


class ConversationModel(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text, nullable=True)


class MessageModel(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True)
    conversation_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LongTermMemory(MemoryRepository):
    """
    Memoria largo plazo usando SQLite.
    Persiste conversaciones y mensajes entre sesiones.
    """

    def __init__(self):
        db_path = os.getenv("LONG_TERM_DB_PATH", "data/memory.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self._engine)
        logger.success(f"LongTermMemory inicializado — db: {db_path}")

    def create_conversation(self, conversation_id: str) -> Conversation:
        with Session(self._engine) as session:
            conv = ConversationModel(
                id=conversation_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(conv)
            session.commit()
        return Conversation(id=conversation_id)

    def save_message(self, message: Message) -> None:
        import json
        with Session(self._engine) as session:
            sources_json = json.dumps([
                {
                    "url": s.url,
                    "title": s.title,
                    "category": s.category,
                    "relevance_score": s.relevance_score,
                }
                for s in message.sources
            ])
            msg = MessageModel(
                id=message.id,
                conversation_id=message.conversation_id,
                role=message.role.value,
                content=message.content,
                sources=sources_json,
                created_at=message.created_at,
            )
            session.add(msg)
            # Actualiza updated_at de la conversación
            conv = session.get(ConversationModel, message.conversation_id)
            if conv:
                conv.updated_at = datetime.utcnow()
            session.commit()
        logger.debug(f"Mensaje guardado: {message.role.value} — {message.conversation_id}")

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        import json
        with Session(self._engine) as session:
            conv = session.get(ConversationModel, conversation_id)
            if not conv:
                return None

            msgs = session.query(MessageModel).filter(
                MessageModel.conversation_id == conversation_id
            ).order_by(MessageModel.created_at).all()

            messages = []
            for m in msgs:
                sources = []
                if m.sources:
                    for s in json.loads(m.sources):
                        sources.append(Source(
                            url=s["url"],
                            title=s["title"],
                            category=s["category"],
                            relevance_score=s["relevance_score"],
                        ))
                messages.append(Message(
                    id=m.id,
                    role=MessageRole(m.role),
                    content=m.content,
                    sources=sources,
                    conversation_id=m.conversation_id,
                    created_at=m.created_at,
                ))

            return Conversation(
                id=conv.id,
                messages=messages,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )

    def get_recent_conversations(self, limit: int = 5) -> List[Conversation]:
        with Session(self._engine) as session:
            convs = session.query(ConversationModel).order_by(
                ConversationModel.updated_at.desc()
            ).limit(limit).all()
            return [self.get_conversation(c.id) for c in convs]

    def get_conversation_summary(self, conversation_id: str) -> Optional[str]:
        with Session(self._engine) as session:
            conv = session.get(ConversationModel, conversation_id)
            return conv.summary if conv else None

    def save_conversation_summary(self, conversation_id: str, summary: str) -> None:
        with Session(self._engine) as session:
            conv = session.get(ConversationModel, conversation_id)
            if conv:
                conv.summary = summary
                session.commit()
        logger.debug(f"Resumen guardado para conversación: {conversation_id}")