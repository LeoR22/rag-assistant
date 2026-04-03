import os
import sys
from pathlib import Path
from typing import Optional
from loguru import logger
from dotenv import load_dotenv
import fastmcp
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request

sys.path.insert(0, str(Path(__file__).parent))

from application.use_cases.search_knowledge import SearchKnowledgeUseCase
from application.use_cases.get_article import GetArticleByUrlUseCase
from application.use_cases.list_categories import ListCategoriesUseCase
from infrastructure.vector_store.chroma_repository import ChromaRepository

load_dotenv()

# ── Inicialización ──────────────────────────────────────────
mcp = fastmcp.FastMCP(
    name=os.getenv("MCP_SERVER_NAME", "bancolombia-knowledge-base"),
    instructions="""
    Servidor MCP de conocimiento de Bancolombia.
    Contiene información sobre productos y servicios de bancolombia.com/personas.
    Usa search_knowledge_base para buscar información relevante.
    Usa get_article_by_url para obtener el contenido completo de un artículo.
    Usa list_categories para ver las categorías disponibles.
    """,
)

# ── Repositorio compartido ──────────────────────────────────
def get_repository() -> ChromaRepository:
    return ChromaRepository()


# ── Health check ────────────────────────────────────────────
@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({
        "status": "healthy",
        "server": os.getenv("MCP_SERVER_NAME", "bancolombia-knowledge-base"),
        "transport": "streamable-http",
        "version": "1.0.0",
    })


# ══════════════════════════════════════════════════════════════
# TOOLS
# ══════════════════════════════════════════════════════════════

@mcp.tool(
    description="""
    Busca información relevante en la base de conocimiento de Bancolombia.

    USA ESTA TOOL CUANDO:
    - El usuario pregunte sobre productos bancarios: cuentas, créditos, tarjetas, seguros, inversiones, pagos
    - El usuario pregunte sobre requisitos, tasas, plazos o condiciones de productos
    - El usuario pregunte sobre servicios digitales, canales de atención o sucursales
    - Necesites información actualizada sobre Bancolombia para responder

    NO USES ESTA TOOL CUANDO:
    - El usuario salude o haga preguntas generales de conversación
    - La pregunta no tenga relación con Bancolombia

    Retorna documentos con URL, título, categoría y score de relevancia.
    SIEMPRE cita las URLs retornadas al final de tu respuesta.
    """
)
def search_knowledge_base(
    query: str,
    top_k: int = 5,
    category: Optional[str] = None,
) -> dict:
    """
    Args:
        query: Consulta en lenguaje natural sobre productos o servicios de Bancolombia
        top_k: Número de resultados a retornar (1-10, default 5)
        category: Filtrar por categoría opcional (Créditos, Ahorro, Inversiones, Seguros, Tarjetas, Pagos y Transferencias, General)
    """
    try:
        repository = get_repository()
        use_case = SearchKnowledgeUseCase(vector_repository=repository)
        results = use_case.execute(query=query, top_k=top_k, category=category)

        return {
            "query": query,
            "total_results": len(results),
            "results": [
                {
                    "url": doc.url,
                    "title": doc.title,
                    "category": doc.category,
                    "content": doc.content,
                    "relevance_score": doc.relevance_score,
                    "chunk_index": doc.chunk_index,
                    "total_chunks": doc.total_chunks,
                }
                for doc in results
            ],
        }

    except ValueError as e:
        logger.warning(f"Parámetro inválido en search_knowledge_base: {e}")
        return {"error": str(e), "results": []}
    except RuntimeError as e:
        logger.error(f"Base vectorial no disponible: {e}")
        return {"error": str(e), "results": []}
    except Exception as e:
        logger.error(f"Error inesperado en search_knowledge_base: {e}")
        return {"error": "Error interno del servidor", "results": []}


@mcp.tool(
    description="""
    Obtiene el contenido COMPLETO de un artículo específico de Bancolombia por su URL.

    USA ESTA TOOL CUANDO:
    - Ya tienes una URL de bancolombia.com y necesitas más detalles del artículo
    - El usuario pide información detallada sobre una página específica
    - Los resultados de search_knowledge_base no tienen suficiente detalle
    - Necesitas el contenido completo de un artículo para responder correctamente

    Retorna todos los chunks del artículo ordenados con el contenido completo.
    """
)
def get_article_by_url(url: str) -> dict:
    """
    Args:
        url: URL completa del artículo de bancolombia.com a recuperar
    """
    try:
        repository = get_repository()
        use_case = GetArticleByUrlUseCase(vector_repository=repository)
        documents = use_case.execute(url=url)
        full_content = "\n\n".join([doc.content for doc in documents])

        return {
            "url": url,
            "title": documents[0].title if documents else "",
            "category": documents[0].category if documents else "",
            "total_chunks": len(documents),
            "content": full_content,
        }

    except ValueError as e:
        logger.warning(f"URL inválida en get_article_by_url: {e}")
        return {"error": str(e), "content": ""}
    except RuntimeError as e:
        logger.error(f"Base vectorial no disponible: {e}")
        return {"error": str(e), "content": ""}
    except Exception as e:
        logger.error(f"Error inesperado en get_article_by_url: {e}")
        return {"error": "Error interno del servidor", "content": ""}


@mcp.tool(
    description="""
    Lista todas las categorías de productos y servicios disponibles en la base de conocimiento.

    USA ESTA TOOL CUANDO:
    - El usuario pregunte qué tipos de productos tiene Bancolombia
    - Quieras filtrar búsquedas por categoría antes de usar search_knowledge_base
    - El usuario pregunte por categorías generales

    Categorías disponibles: Créditos, Ahorro, Inversiones, Seguros, Tarjetas, Pagos y Transferencias, General.
    """
)
def list_categories() -> dict:
    """Retorna las categorías disponibles en la base de conocimiento"""
    try:
        repository = get_repository()
        use_case = ListCategoriesUseCase(vector_repository=repository)
        categories = use_case.execute()

        return {
            "total_categories": len(categories),
            "categories": categories,
        }

    except RuntimeError as e:
        logger.error(f"Base vectorial no disponible: {e}")
        return {"error": str(e), "categories": []}
    except Exception as e:
        logger.error(f"Error inesperado en list_categories: {e}")
        return {"error": "Error interno del servidor", "categories": []}


# ══════════════════════════════════════════════════════════════
# RESOURCE
# ══════════════════════════════════════════════════════════════
@mcp.resource(
    uri="knowledgebase://stats",
    name="knowledge_base_stats",
    description="Estadísticas de la base de conocimiento: documentos indexados, categorías, modelo de embeddings y fecha de actualización",
    mime_type="application/json",
)
def get_knowledge_base_stats() -> str:
    """Expone estadísticas de la base de conocimiento"""
    import json
    try:
        repository = get_repository()
        stats = repository.get_stats()
        return json.dumps(stats, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error obteniendo stats: {e}")
        return json.dumps({"error": str(e)})


# ══════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_SERVER_PORT", 8000))

    logger.info(f"🚀 Iniciando servidor MCP")
    logger.info(f"   Transporte: {transport}")

    if transport == "stdio":
        logger.info(f"   Modo: stdio")
        mcp.run(transport="stdio")
    else:
        logger.info(f"   Host:    {host}:{port}")
        logger.info(f"   MCP URL: http://{host}:{port}/mcp")
        logger.info(f"   Health:  http://{host}:{port}/health")
        mcp.run(
            host=host,
            port=port,
        )