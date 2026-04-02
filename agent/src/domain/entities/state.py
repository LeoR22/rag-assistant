from typing import List, Optional, Annotated
from dataclasses import dataclass, field
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(dict):
    """
    Estado del grafo LangGraph.
    Contiene toda la información que fluye entre los nodos del grafo.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    conversation_id: str
    query: str
    sources: List[dict]
    response: str
    needs_search: bool
    error: Optional[str]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setdefault("messages", [])
        self.setdefault("conversation_id", "")
        self.setdefault("query", "")
        self.setdefault("sources", [])
        self.setdefault("response", "")
        self.setdefault("needs_search", True)
        self.setdefault("error", None)