from typing import List
from loguru import logger
from ...domain.repositories.vector_repository import VectorRepository


class ListCategoriesUseCase:
    """Caso de uso: lista las categorías disponibles en la base de conocimiento"""

    def __init__(self, vector_repository: VectorRepository):
        self._repository = vector_repository

    def execute(self) -> List[str]:
        if self._repository.is_empty():
            raise RuntimeError("La base de conocimiento está vacía")

        logger.info("Listando categorías disponibles")

        categories = self._repository.list_categories()

        logger.info(f"Categorías encontradas: {len(categories)}")
        return categories