import pytest
from unittest.mock import MagicMock
from datetime import datetime
from src.domain.entities.message import Message, MessageRole, Source
from src.domain.entities.conversation import Conversation


# ── Tests Message ────────────────────────────────────────────

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


def test_message_user_has_no_sources():
    msg = Message.user(content="Hola", conversation_id="conv-001")
    assert msg.sources == []


def test_message_content_not_empty():
    msg = Message.user(content="¿Qué seguros ofrece Bancolombia?", conversation_id="conv-001")
    assert len(msg.content) > 0


def test_message_has_timestamp():
    msg = Message.user(content="Hola", conversation_id="conv-001")
    assert msg.created_at is not None


def test_source_creation():
    source = Source(
        url="https://www.bancolombia.com/personas/creditos",
        title="Créditos Bancolombia",
        category="Créditos",
        relevance_score=0.95,
    )
    assert source.url == "https://www.bancolombia.com/personas/creditos"
    assert source.relevance_score == 0.95
    assert source.category == "Créditos"


# ── Tests Conversation ───────────────────────────────────────

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


def test_conversation_has_correct_id():
    conv = Conversation(id="conv-123")
    assert conv.id == "conv-123"


def test_conversation_multiple_messages():
    conv = Conversation(id="conv-001")
    user_msg = Message.user(content="Hola", conversation_id="conv-001")
    assistant_msg = Message.assistant(
        content="Hola, ¿en qué puedo ayudarte?",
        conversation_id="conv-001",
        sources=[],
    )
    conv.add_message(user_msg)
    conv.add_message(assistant_msg)
    assert len(conv.messages) == 2


def test_conversation_get_history_returns_all_when_less_than_limit():
    conv = Conversation(id="conv-001")
    for i in range(5):
        msg = Message.user(content=f"Pregunta {i}", conversation_id="conv-001")
        conv.add_message(msg)
    history = conv.get_history(max_messages=10)
    assert len(history) == 5


def test_conversation_messages_order():
    conv = Conversation(id="conv-001")
    msg1 = Message.user(content="Primera pregunta", conversation_id="conv-001")
    msg2 = Message.user(content="Segunda pregunta", conversation_id="conv-001")
    conv.add_message(msg1)
    conv.add_message(msg2)
    assert conv.messages[0].content == "Primera pregunta"
    assert conv.messages[1].content == "Segunda pregunta"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])