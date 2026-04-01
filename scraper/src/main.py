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
    max_pages = int(os.getenv("MAX_PAGES", 80))
    output_dir = os.getenv("OUTPUT_DIR", "data/raw")

    logger.info("🚀 Iniciando scraper de Bancolombia")

    crawler = BancolombiaCrawler()
    repository = JsonRepository(output_dir=output_dir)
    crawl_use_case = CrawlWebsiteUseCase(crawler_repository=crawler)
    clean_use_case = CleanContentUseCase()

    logger.info("📡 Fase 1: Crawling")
    pages = await crawl_use_case.execute(base_url=base_url, max_pages=max_pages)

    logger.info("🧹 Fase 2: Limpieza y chunking")
    cleaned_pages = [clean_use_case.execute(page) for page in pages]

    logger.info("💾 Fase 3: Guardando datos")
    repository.save_all(cleaned_pages)

    logger.success(f"✅ Scraper completado — {len(cleaned_pages)} páginas procesadas")


if __name__ == "__main__":
    asyncio.run(main())