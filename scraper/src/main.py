import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from loguru import logger
from infrastructure.crawlers.bancolombia_crawler import BancolombiaCrawler
from infrastructure.persistence.json_repository import JsonRepository
from application.use_cases.crawl_website import CrawlWebsiteUseCase
from application.use_cases.clean_content import CleanContentUseCase

load_dotenv()


async def main():
    base_url = os.getenv("BASE_URL")
    output_dir = os.getenv("OUTPUT_DIR", "data/raw")

    logger.info("Iniciando scraper industrializado de Bancolombia....")

    crawler = BancolombiaCrawler()
    repository = JsonRepository(output_dir=output_dir)
    crawl_use_case = CrawlWebsiteUseCase(crawler_repository=crawler)
    clean_use_case = CleanContentUseCase()

    # URLs ya indexadas para proceso incremental
    existing_urls = repository.get_existing_urls()
    logger.info(f"URLs ya indexadas: {len(existing_urls)}")

    # Fase 1: Crawling
    logger.info("Fase 1: Crawling")
    pages = await crawl_use_case.execute(base_url=base_url)

    # Fase 2: Detección de cambios y limpieza
    logger.info("Fase 2: Detección de cambios y limpieza")
    new_pages = []
    updated_pages = []
    unchanged_pages = []

    for page in pages:
        cleaned = clean_use_case.execute(page)
        if page.url not in existing_urls:
            new_pages.append(cleaned)
        elif repository.is_page_modified(page.url, page.content_hash or ""):
            updated_pages.append(cleaned)
        else:
            unchanged_pages.append(cleaned)

    # Fase 3: Persistencia
    logger.info("Fase 3: Guardando datos")
    all_pages = new_pages + updated_pages + unchanged_pages
    repository.save_all(all_pages)

    # Reporte final
    logger.info("=" * 50)
    logger.success(f"Páginas nuevas:       {len(new_pages)}")
    logger.info(f" Páginas actualizadas: {len(updated_pages)}")
    logger.info(f"Sin cambios:          {len(unchanged_pages)}")
    logger.success(f"Total procesadas:    {len(all_pages)}")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())