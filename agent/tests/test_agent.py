import pytest
from unittest.mock import MagicMock
from datetime import datetime
from src.domain.entities.message import Message, MessageRole, Source
from src.domain.entities.conversation import Conversation


def test_message_user_creation():
    msg = Message.user(content="¿Qué créditos tiene Bancolombia?", conversation_id="conv-001")
    assert msg.role == MessageRole.USER
    assert msg.content == "¿Qué créditos tiene Bancolombia?"
    assert msg.conversation_id == "conv-001"
    assert msg.id is not None


def test_message_assistant_creation():
    sources = [Source(url="https://bancolombia.com", title="Test", category="General", relevance_score=0.9)]
    msg = Message.assistant(
        content="Bancolombia ofrece varios créditos",
        conversation_id="conv-001",
        sources=sources,
    )
    assert msg.role == MessageRole.ASSISTANT
    assert len(msg.sources) == 1


def test_conversation_add_message():
    conv = Conversation(id="conv-001")
    msg = Message.user(content="Hola", conversation_id="conv-001")
    conv.add_message(msg)
    assert len(conv.messages) == 1
    assert conv.is_empty() is False


def test_conversation_get_history_limit():
    conv = Conversation(id="conv-001")
    for i in range(25):
        msg = Message.user(content=f"Pregunta {i}", conversation_id="conv-001")
        conv.add_message(msg)
    history = conv.get_history(max_messages=10)
    assert len(history) == 10


def test_conversation_is_empty():
    conv = Conversation(id="conv-001")
    assert conv.is_empty() is True