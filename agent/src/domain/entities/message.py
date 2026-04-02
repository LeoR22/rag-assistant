from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Source:
    """Fuente citada en una respuesta"""
    url: str
    title: str
    category: str
    relevance_score: float


@dataclass
class Message:
    """Entidad del dominio que representa un mensaje en la conversación"""
    id: str
    role: MessageRole
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    sources: List[Source] = field(default_factory=list)
    conversation_id: Optional[str] = None

    @classmethod
    def user(cls, content: str, conversation_id: str) -> "Message":
        import uuid
        return cls(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content=content,
            conversation_id=conversation_id,
        )

    @classmethod
    def assistant(cls, content: str, conversation_id: str, sources: List[Source] = None) -> "Message":
        import uuid
        return cls(
            id=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            content=content,
            conversation_id=conversation_id,
            sources=sources or [],
        )