from abc import ABC, abstractmethod
from typing import List
from ..entities.page import Page


class CrawlerRepository(ABC):
    """Puerto del dominio — define el contrato que debe cumplir cualquier crawler"""

    @abstractmethod
    async def fetch_page(self, url: str) -> Page:
        """Obtiene el contenido de una página"""
        pass

    @abstractmethod
    async def discover_links(self, base_url: str, max_pages: int) -> List[str]:
        """Descubre links internos desde una URL base"""
        pass

    @abstractmethod
    async def is_allowed_by_robots(self, url: str) -> bool:
        """Verifica si la URL está permitida por robots.txt"""
        pass