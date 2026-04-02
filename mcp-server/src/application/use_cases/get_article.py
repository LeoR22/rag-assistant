from typing import List
from loguru import logger
from domain.entities.document import Document
from domain.repositories.vector_repository import VectorRepository


class GetArticleByUrlUseCase:
    """Caso de uso: obtiene el contenido completo de un artículo por su URL"""

    def __init__(self, vector_repository: VectorRepository):
        self._repository = vector_repository

    def execute(self, url: str) -> List[Document]:
        if not url or not url.strip():
            raise ValueError("La URL no puede estar vacía")

        if "bancolombia.com" not in url:
            raise ValueError("Solo se aceptan URLs del dominio bancolombia.com")

        if self._repository.is_empty():
            raise RuntimeError("La base de conocimiento está vacía")

        logger.info(f"Obteniendo artículo: {url}")

        documents = self._repository.get_by_url(url)

        if not documents:
            raise ValueError(f"No se encontró contenido para la URL: {url}")

        logger.info(f"Chunks encontrados: {len(documents)}")
        return documents