import os
from loguru import logger
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langfuse.langchain import CallbackHandler

load_dotenv()


def build_agent():
    """
    Construye el grafo LangGraph con:
    - GPT-4o via GitHub Models como LLM
    - Tools del servidor MCP como capacidades de búsqueda
    - MemorySaver para memoria corto plazo entre turnos
    - Langfuse para observabilidad
    """

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("GITHUB_TOKEN no está configurado en .env")

    llm_model = os.getenv("LLM_MODEL")
    if not llm_model:
        raise EnvironmentError("LLM_MODEL no está configurado en .env")

    llm_base_url = os.getenv("LLM_BASE_URL")
    if not llm_base_url:
        raise EnvironmentError("LLM_BASE_URL no está configurado en .env")

    mcp_server_url = os.getenv("MCP_SERVER_URL")
    if not mcp_server_url:
        raise EnvironmentError("MCP_SERVER_URL no está configurado en .env")

    llm = ChatOpenAI(
        model=llm_model,
        base_url=llm_base_url,
        api_key=token,
        temperature=0.1,
    )

    mcp_config = {
        "bancolombia": {
            "url": mcp_server_url,
            "transport": "streamable_http",
        }
    }

    memory = MemorySaver()

    # Langfuse handler — opcional, solo si las keys están configuradas
    langfuse_handler = None
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if langfuse_public_key and langfuse_secret_key:
        os.environ["LANGFUSE_PUBLIC_KEY"] = langfuse_public_key
        os.environ["LANGFUSE_SECRET_KEY"] = langfuse_secret_key
        os.environ["LANGFUSE_HOST"] = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        langfuse_handler = CallbackHandler()
        logger.success("Langfuse observabilidad activada")
    else:
        logger.warning("Langfuse no configurado — observabilidad desactivada")

    return llm, mcp_config, memory, langfuse_handler


SYSTEM_PROMPT = """Eres un asistente virtual experto en productos y servicios del Grupo Bancolombia.

Tu conocimiento proviene exclusivamente de la información indexada del sitio web bancolombia.com/personas.

{memory_context}

Reglas estrictas:
1. SIEMPRE usa search_knowledge_base para preguntas sobre productos, servicios o información de Bancolombia.
2. SIEMPRE cita las URLs de las fuentes al final de tu respuesta.
3. Para saludos como "Hola", "Buenos días", "¿Cómo estás?" — responde directamente SIN usar ninguna tool.
4. Para preguntas NO relacionadas con Bancolombia como precios de divisas, tareas, clima, etc. — responde directamente SIN usar tools: "Solo puedo ayudarte con información sobre productos y servicios de Bancolombia."
5. Responde SIEMPRE en español, sin importar el idioma de la pregunta.
6. Sé conciso, claro y profesional.

Ejemplos de preguntas fuera de alcance — responde SIN tools:
- Precio del dólar, euro u otras divisas
- Preguntas de matemáticas o tareas
- Clima, noticias, política
- Preguntas sobre otras entidades bancarias
- Preguntas en inglés u otros idiomas

Formato de respuesta OBLIGATORIO:
- Respuesta clara, directa y profesional
- Usa negritas (**texto**) para nombres de productos
- Usa listas numeradas para múltiples opciones
- Máximo 3-4 líneas por producto
- SIEMPRE termina con las URLs de fuentes consultadas cuando uses search_knowledge_base
- No uses lenguaje coloquial ni informalismos

"""