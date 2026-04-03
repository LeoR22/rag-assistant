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
    Recibe una consulta en lenguaje natural y retorna los documentos más relevantes
    con su URL de origen, título, categoría y score de relevancia.
    Úsala cuando el usuario pregunte sobre productos, servicios o información de Bancolombia.
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
    Obtiene el contenido completo de un artículo de Bancolombia por su URL.
    Retorna todos los chunks del artículo ordenados correctamente.
    Úsala cuando necesites el contenido completo de una página específica de Bancolombia.
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
    Lista todas las categorías disponibles en la base de conocimiento de Bancolombia.
    Úsala para conocer qué tipos de productos y servicios están indexados
    antes de hacer una búsqueda filtrada por categoría.
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
            transport=transport,
            host=host,
            port=port,
        )