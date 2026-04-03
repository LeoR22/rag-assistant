import os
from loguru import logger
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from infrastructure.memory.long_term import LongTermMemory

load_dotenv()


class ManageMemoryUseCase:
    """
    Caso de uso: gestiona la memoria mediano/largo plazo.
    Genera resúmenes de conversaciones anteriores para contexto futuro.
    """

    def __init__(self):
        self._memory = LongTermMemory()
        self._llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL"),
            base_url=os.getenv("LLM_BASE_URL"),
            api_key=os.getenv("GITHUB_TOKEN"),
            temperature=0,
        )

    async def summarize_conversation(self, conversation_id: str) -> str:
        """
        Genera un resumen de la conversación para memoria mediano plazo.
        Se ejecuta cuando una conversación supera el límite de mensajes.
        """
        conversation = self._memory.get_conversation(conversation_id)
        if not conversation or conversation.is_empty():
            return ""

        messages_text = "\n".join([
            f"{m.role.value}: {m.content}"
            for m in conversation.messages
        ])

        prompt = f"""Resume esta conversación en máximo 3 oraciones, 
        destacando los temas consultados y productos de Bancolombia mencionados:
        
        {messages_text}
        
        Resumen:"""

        response = await self._llm.ainvoke(prompt)
        summary = response.content

        self._memory.save_conversation_summary(conversation_id, summary)
        logger.info(f"Resumen generado para conversación: {conversation_id}")

        return summary

    def get_context_from_history(self, conversation_id: str) -> str:
        """
        Obtiene contexto de conversaciones anteriores.
        Combina resúmenes para dar contexto al agente.
        """
        recent = self._memory.get_recent_conversations(limit=3)
        if not recent:
            return ""

        context_parts = []
        for conv in recent:
            if conv.id == conversation_id:
                continue
            summary = self._memory.get_conversation_summary(conv.id)
            if summary:
                context_parts.append(f"- {summary}")

        if not context_parts:
            return ""

        return "Contexto de conversaciones anteriores:\n" + "\n".join(context_parts)