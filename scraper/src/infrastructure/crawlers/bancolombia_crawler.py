import asyncio
from typing import List
from datetime import datetime
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from loguru import logger
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from trafilatura import extract
from domain.entities.page import Page
from domain.repositories.crawler_repository import CrawlerRepository
import os
from dotenv import load_dotenv

load_dotenv()

class BancolombiaCrawler:
    """Implementación concreta del crawler para el sitio de Bancolombia"""

    BASE_URL = os.getenv("BASE_DOMAIN", "https://www.bancolombia.com")
    PAGE_TIMEOUT = int(os.getenv("PAGE_TIMEOUT", "60000"))


    CATEGORIES = {
        "creditos": "Créditos",
        "ahorro": "Ahorro",
        "inversiones": "Inversiones",
        "seguros": "Seguros",
        "pagos": "Pagos y Transferencias",
        "tarjetas": "Tarjetas",
        "hipotecario": "Crédito Hipotecario",
    }

    def __init__(self):
        self._robot_parser = RobotFileParser()
        self._robot_parser.set_url(f"{self.BASE_URL}/robots.txt")
        self._robot_parser.read()

    def _detect_category(self, url: str) -> str:
        """Detecta la categoría de una página basándose en su URL"""
        url_lower = url.lower()
        for key, category in self.CATEGORIES.items():
            if key in url_lower:
                return category
        return "General"

    async def is_allowed_by_robots(self, url: str) -> bool:
        """Verifica robots.txt"""
        return self._robot_parser.can_fetch("*", url)

    async def discover_links(self, base_url: str, max_pages: int) -> List[str]:
        """Descubre links internos del sitio de Bancolombia"""
        discovered = set()
        to_visit = [base_url]
        visited = set()

        async with AsyncWebCrawler() as crawler:
            while to_visit and len(discovered) < max_pages:
                url = to_visit.pop(0)

                if url in visited:
                    continue

                visited.add(url)

                try:
                    config = CrawlerRunConfig(
                        wait_until="networkidle",
                        page_timeout=60000,
                    )
                    result = await crawler.arun(url=url, config=config)

                    if result.success and result.links:
                        for link in result.links.get("internal", []):
                            href = link.get("href", "")
                            if href and "/personas" in href:
                                full_url = urljoin(self.BASE_URL, href)
                                if full_url not in visited:
                                    discovered.add(full_url)
                                    to_visit.append(full_url)

                    logger.info(f"Links descubiertos hasta ahora: {len(discovered)}")

                except Exception as e:
                    logger.error(f"Error descubriendo links en {url}: {e}")

        return list(discovered)[:max_pages]

    async def fetch_page(self, url: str) -> Page:
        """Obtiene y limpia el contenido de una página"""
        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(
                wait_until="networkidle",
                page_timeout=30000,
            )
            result = await crawler.arun(url=url, config=config)

            if not result.success:
                raise Exception(f"Error al obtener {url}: {result.error_message}")

            # Extrae texto limpio con trafilatura
            content = extract(result.html) or result.markdown or ""
            title = result.metadata.get("title", "") if result.metadata else ""
            category = self._detect_category(url)

            return Page.create(
                url=url,
                title=title,
                content=content,
                category=category,
            )