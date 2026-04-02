from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.message import Message
from ..entities.conversation import Conversation


class MemoryRepository(ABC):
    """Puerto del dominio — contrato para el manejo de memoria del agente"""

    @abstractmethod
    def save_message(self, message: Message) -> None:
        """Guarda un mensaje en memoria largo plazo"""
        pass

    @abstractmethod
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Obtiene una conversación completa por su ID"""
        pass

    @abstractmethod
    def get_recent_conversations(self, limit: int = 5) -> List[Conversation]:
        """Obtiene las conversaciones más recientes — memoria mediano plazo"""
        pass

    @abstractmethod
    def create_conversation(self, conversation_id: str) -> Conversation:
        """Crea una nueva conversación"""
        pass

    @abstractmethod
    def get_conversation_summary(self, conversation_id: str) -> Optional[str]:
        """Obtiene el resumen de una conversación anterior"""
        pass

    @abstractmethod
    def save_conversation_summary(self, conversation_id: str, summary: str) -> None:
        """Guarda el resumen de una conversación"""
        pass