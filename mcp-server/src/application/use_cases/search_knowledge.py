from typing import List, Optional
from loguru import logger
from domain.entities.document import Document
from domain.repositories.vector_repository import VectorRepository


class SearchKnowledgeUseCase:
    """Caso de uso: búsqueda semántica en la base de conocimiento"""

    def __init__(self, vector_repository: VectorRepository):
        self._repository = vector_repository

    def execute(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> List[Document]:
        if not query or not query.strip():
            raise ValueError("La consulta no puede estar vacía")

        if top_k < 1 or top_k > 20:
            raise ValueError("top_k debe estar entre 1 y 20")

        if self._repository.is_empty():
            raise RuntimeError("La base de conocimiento está vacía — ejecuta el indexador primero")

        logger.info(f"Buscando: '{query}' | top_k={top_k} | category={category}")

        results = self._repository.search(
            query=query,
            top_k=top_k,
            category=category,
        )

        logger.info(f"Resultados encontrados: {len(results)}")
        return results