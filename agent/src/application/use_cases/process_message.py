import os
import uuid
from loguru import logger
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from infrastructure.graph.builder import build_agent, SYSTEM_PROMPT
from infrastructure.memory.long_term import LongTermMemory
from infrastructure.memory.short_term import ShortTermMemory
from domain.entities.message import Message, MessageRole, Source
from domain.entities.conversation import Conversation
from application.use_cases.manage_memory import ManageMemoryUseCase

load_dotenv()

MAX_MESSAGES = 8  # Últimos 4 turnos para no superar token limit de GitHub Models


class ProcessMessageUseCase:
    """
    Caso de uso principal — procesa un mensaje del usuario.
    Orquesta: MCP tools → LangGraph → memoria → respuesta con fuentes
    """

    def __init__(self):
        self._long_term = LongTermMemory()
        self._llm, self._mcp_config, self._memory, self._langfuse = build_agent()
        # ShortTermMemory se crea por conversación, no aquí

    async def execute(self, query: str, conversation_id: str) -> dict:
        logger.info(f"Procesando mensaje — conversación: {conversation_id}")

        conversation = self._long_term.get_conversation(conversation_id)
        if not conversation:
            conversation = self._long_term.create_conversation(conversation_id)

        user_message = Message.user(
            content=query,
            conversation_id=conversation_id,
        )
        self._long_term.save_message(user_message)

        # ShortTermMemory por conversación — evita mezclar historiales
        short_term = ShortTermMemory()
        conversation = self._long_term.get_conversation(conversation_id)
        if conversation:
            for msg in conversation.messages[-MAX_MESSAGES:]:
                if msg.role == MessageRole.USER:
                    short_term.add_user_message(msg.content)
                elif msg.role == MessageRole.ASSISTANT:
                    short_term.add_assistant_message(msg.content)

        # Historial ya viene trimado desde long_term (últimos MAX_MESSAGES)
        history = short_term.get_messages()

        manage_memory = ManageMemoryUseCase()
        memory_context = manage_memory.get_context_from_history(conversation_id)
        prompt = SYSTEM_PROMPT
        if memory_context:
            prompt = SYSTEM_PROMPT + f"\n\n{memory_context}"

        client = MultiServerMCPClient(self._mcp_config)
        tools = await client.get_tools()

        agent = create_react_agent(
            model=self._llm,
            tools=tools,
            prompt=prompt,
            checkpointer=self._memory,
        )

        callbacks = [self._langfuse] if self._langfuse else []
        config = {
            "configurable": {"thread_id": conversation_id},
            "callbacks": callbacks,
        }

        try:
            result = await agent.ainvoke(
                {"messages": history},
                config=config,
            )
        except Exception as llm_error:
            logger.error(f"LLM invocation failed: {llm_error}")
            error_msg = str(llm_error).lower()

            if "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
                response_content = (
                    "Lo siento, estoy recibiendo muchas consultas en este momento. "
                    "Por favor intenta de nuevo en unos segundos."
                )
            elif "timeout" in error_msg or "connection" in error_msg:
                response_content = (
                    "Estoy teniendo problemas para conectarme. "
                    "Por favor intenta de nuevo en unos minutos."
                )
            else:
                response_content = (
                    "Ocurrió un error inesperado. El incidente ha sido registrado."
                )

            return {
                "conversation_id": conversation_id,
                "response": response_content,
                "sources": [],
            }
        last_message = result["messages"][-1]
        response_content = last_message.content

        sources = self._extract_sources(result["messages"])

        assistant_message = Message.assistant(
            content=response_content,
            conversation_id=conversation_id,
            sources=sources,
        )
        self._long_term.save_message(assistant_message)

        # Genera resumen si la conversación supera 10 mensajes
        conversation = self._long_term.get_conversation(conversation_id)
        if conversation and len(conversation.messages) >= 10:
            manage_memory = ManageMemoryUseCase()
            await manage_memory.summarize_conversation(conversation_id)

        logger.success(f"Respuesta generada — fuentes: {len(sources)}")
        return {
            "conversation_id": conversation_id,
            "response": response_content,
            "sources": [
                {
                    "url": s.url,
                    "title": s.title,
                    "category": s.category,
                    "relevance_score": s.relevance_score,
                }
                for s in sources
            ],
        }

    def _extract_sources(self, messages: list) -> list[Source]:
        """Extrae las fuentes de los resultados de las tools MCP"""
        import json
        sources = []
        seen_urls = set()

        for message in messages:
            content = message.content if hasattr(message, "content") else ""

            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        content = block.get("text", "")
                        break

            if not isinstance(content, str):
                continue

            try:
                data = json.loads(content)
                if "results" in data:
                    for result in data["results"]:
                        url = result.get("url", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            sources.append(Source(
                                url=url,
                                title=result.get("title", ""),
                                category=result.get("category", ""),
                                relevance_score=result.get("relevance_score", 0.0),
                            ))
            except Exception:
                continue

        return sources