from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.document import Document


class VectorRepository(ABC):
    """Puerto del dominio — contrato que debe cumplir cualquier base vectorial"""

    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        """Indexa una lista de documentos con sus embeddings"""
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> List[Document]:
        """Búsqueda semántica por query en lenguaje natural"""
        pass

    @abstractmethod
    def get_by_url(self, url: str) -> List[Document]:
        """Retorna todos los chunks de un documento por su URL"""
        pass

    @abstractmethod
    def list_categories(self) -> List[str]:
        """Retorna las categorías disponibles en la base de conocimiento"""
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        """Retorna estadísticas de la base de conocimiento"""
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        """Verifica si la base vectorial está vacía"""
        pass