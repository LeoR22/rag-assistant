import asyncio
from typing import List
from loguru import logger
from domain.entities.page import Page
from domain.repositories.crawler_repository import CrawlerRepository
import os
from dotenv import load_dotenv

load_dotenv()

class CrawlWebsiteUseCase:
    """
    Crawling autónomo sin límite de búsqueda.
    Para ÚNICAMENTE cuando tiene MIN_PAGES páginas válidas
    o cuando el sitio no tiene más URLs por descubrir.
    """

    MIN_PAGES = int(os.getenv("MIN_PAGES", 60))
    MAX_RETRIES = 2
    RETRY_DELAY = 2
    DISCOVERY_BATCH = int(os.getenv("DISCOVERY_BATCH", 30))

    def __init__(self, crawler_repository: CrawlerRepository):
        self._crawler = crawler_repository

    async def execute(self, base_url: str) -> List[Page]:
        logger.info(f"Crawling sin límite — para solo al llegar a {self.MIN_PAGES} páginas válidas")

        pages: List[Page] = []
        failed: List[str] = []
        skipped: List[str] = []
        visited: set = set()
        pending: List[str] = []
        discovery_offset = self.DISCOVERY_BATCH

        while len(pages) < self.MIN_PAGES:

            # Siempre que queden pocas URLs pendientes, descubre más
            if len(pending) < 10:
                discovered = await self._crawler.discover_links(
                    base_url, discovery_offset
                )
                new_urls = [u for u in discovered if u not in visited]
                discovery_offset += self.DISCOVERY_BATCH

                if new_urls:
                    pending.extend(new_urls)
                    logger.info(
                        f"URLs nuevas: {len(new_urls)} | "
                        f"Pendientes: {len(pending)} | "
                        f"Válidas: {len(pages)}/{self.MIN_PAGES}"
                    )
                else:
                    # El sitio no tiene más URLs — entrega lo que tiene
                    logger.warning(
                        f"Sitio agotado. No hay más URLs por descubrir. "
                        f"Finalizando con {len(pages)} páginas válidas."
                    )
                    break

            url = pending.pop(0)

            if url in visited:
                continue

            visited.add(url)

            # Robots.txt
            try:
                if not await self._crawler.is_allowed_by_robots(url):
                    skipped.append(url)
                    continue
            except Exception:
                skipped.append(url)
                continue

            # Fetch con reintentos
            page = await self._fetch_with_retry(url)

            if page and page.is_valid():
                pages.append(page)
                logger.success(f"✓ [{len(pages)}/{self.MIN_PAGES}] {url}")
            else:
                failed.append(url)

        self._log_summary(pages, failed, skipped)
        return pages

    async def _fetch_with_retry(self, url: str) -> Page | None:
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                return await self._crawler.fetch_page(url)
            except asyncio.TimeoutError:
                logger.debug(f"Timeout intento {attempt}/{self.MAX_RETRIES}: {url}")
            except Exception as e:
                logger.debug(f"Error intento {attempt}/{self.MAX_RETRIES}: {url} — {str(e)[:80]}")
            if attempt < self.MAX_RETRIES:
                await asyncio.sleep(self.RETRY_DELAY)
        return None

    def _log_summary(self, pages, failed, skipped):
        logger.info("=" * 50)
        logger.success(f"Páginas válidas:  {len(pages)}")
        logger.info(f"Páginas fallidas: {len(failed)}")
        logger.info(f"Omitidas robots: {len(skipped)}")
        if len(pages) >= self.MIN_PAGES:
            logger.success(f"Meta de {self.MIN_PAGES} páginas alcanzada")
        else:
            logger.warning(f"Solo {len(pages)} páginas — sitio sin más URLs disponibles")
        logger.info("=" * 50)