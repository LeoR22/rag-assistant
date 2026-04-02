from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from .message import Message


@dataclass
class Conversation:
    """Entidad del dominio que representa una conversación completa"""
    id: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, message: Message) -> None:
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def get_history(self, max_messages: int = 20) -> List[Message]:
        """Retorna los últimos N mensajes — memoria corto plazo"""
        return self.messages[-max_messages:]

    def is_empty(self) -> bool:
        return len(self.messages) == 0