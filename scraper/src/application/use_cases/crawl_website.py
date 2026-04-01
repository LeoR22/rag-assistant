from typing import List
from loguru import logger
from domain.entities.page import Page
from domain.repositories.crawler_repository import CrawlerRepository


class CrawlWebsiteUseCase:
    """Caso de uso: orquesta el proceso de crawling del sitio de Bancolombia"""

    def __init__(self, crawler_repository: CrawlerRepository):
        self._crawler = crawler_repository

    async def execute(self, base_url: str, max_pages: int = 50) -> List[Page]:
        logger.info(f"Iniciando crawling desde {base_url} — máximo {max_pages} páginas")

        pages = []
        failed_urls = []

        # Descubre links internos
        urls = await self._crawler.discover_links(base_url, max_pages)
        logger.info(f"URLs descubiertas: {len(urls)}")

        for url in urls:
            try:
                # Verifica robots.txt
                if not await self._crawler.is_allowed_by_robots(url):
                    logger.warning(f"Bloqueado por robots.txt: {url}")
                    continue

                page = await self._crawler.fetch_page(url)

                if page.is_valid():
                    pages.append(page)
                    logger.success(f"✓ [{len(pages)}/{max_pages}] {url}")
                else:
                    logger.warning(f"Página inválida o sin contenido: {url}")

            except Exception as e:
                failed_urls.append(url)
                logger.error(f"Error procesando {url}: {e}")

        logger.info(f"Crawling completado — {len(pages)} páginas válidas, {len(failed_urls)} fallidas")

        if failed_urls:
            logger.warning(f"URLs fallidas: {failed_urls}")

        return pages