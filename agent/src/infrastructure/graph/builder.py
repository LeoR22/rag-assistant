import os
from loguru import logger
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()


def build_agent():
    """
    Construye el grafo LangGraph con:
    - GPT-4o via GitHub Models como LLM
    - Tools del servidor MCP como capacidades de búsqueda
    - MemorySaver para memoria corto plazo entre turnos
    """

    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4o"),
        base_url=os.getenv("LLM_BASE_URL", "https://models.inference.ai.azure.com"),
        api_key=os.getenv("GITHUB_TOKEN"),
        temperature=0.1,
    )

    mcp_config = {
        "bancolombia": {
            "url": os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp"),
            "transport": "streamable_http",
        }
    }

    memory = MemorySaver()

    logger.success("Agente LangGraph construido exitosamente")

    return llm, mcp_config, memory


SYSTEM_PROMPT = """Eres un asistente virtual experto en productos y servicios del Grupo Bancolombia.

Tu conocimiento proviene exclusivamente de la información indexada del sitio web bancolombia.com/personas.

Reglas:
1. SIEMPRE usa la tool search_knowledge_base para buscar información antes de responder preguntas sobre Bancolombia.
2. SIEMPRE cita las URLs de las fuentes al final de tu respuesta.
3. Si el usuario saluda o hace preguntas generales, responde directamente sin buscar.
4. Si la pregunta no está relacionada con Bancolombia, indica amablemente que solo puedes ayudar con temas de Bancolombia.
5. Responde siempre en español.
6. Sé conciso, claro y profesional.

Formato de respuesta:
- Respuesta clara y directa
- Fuentes consultadas (URLs) al final
"""