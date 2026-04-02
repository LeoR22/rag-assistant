import os
from typing import List
from loguru import logger
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()


class ShortTermMemory:
    """
    Memoria corto plazo — historial de la sesión actual.
    Vive en el estado del grafo LangGraph (RAM).
    Se limpia al terminar la sesión.
    """

    def __init__(self):
        self._max_messages = int(os.getenv("SHORT_TERM_MAX_MESSAGES", 20))
        self._messages: List[BaseMessage] = []
        logger.success(f"ShortTermMemory inicializado — max mensajes: {self._max_messages}")

    def add_user_message(self, content: str) -> None:
        self._messages.append(HumanMessage(content=content))
        self._trim()

    def add_assistant_message(self, content: str) -> None:
        self._messages.append(AIMessage(content=content))
        self._trim()

    def get_messages(self) -> List[BaseMessage]:
        return self._messages.copy()

    def clear(self) -> None:
        self._messages = []
        logger.debug("ShortTermMemory limpiada")

    def _trim(self) -> None:
        """Mantiene solo los últimos N mensajes"""
        if len(self._messages) > self._max_messages:
            self._messages = self._messages[-self._max_messages:]
            logger.debug(f"Historial recortado a {self._max_messages} mensajes")

    @property
    def message_count(self) -> int:
        return len(self._messages)