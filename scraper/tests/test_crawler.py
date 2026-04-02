import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from unittest.mock import MagicMock, AsyncMock
from domain.entities.page import Page
from application.use_cases.clean_content import CleanContentUseCase
from application.use_cases.crawl_website import CrawlWebsiteUseCase


def test_page_is_valid():
    page = Page.create(
        url="https://www.bancolombia.com/personas/creditos",
        title="Créditos Bancolombia",
        content="Este es el contenido de la página con más de cincuenta palabras para que sea válido " * 4,
        category="Créditos",
    )
    assert page.is_valid() is True


def test_page_is_invalid_short_content():
    page = Page.create(
        url="https://www.bancolombia.com/personas",
        title="",
        content="Poco contenido",
        category="General",
    )
    assert page.is_valid() is False


def test_clean_content_creates_chunks():
    use_case = CleanContentUseCase()
    page = Page.create(
        url="https://www.bancolombia.com/personas/creditos",
        title="Créditos",
        content=" ".join(["palabra"] * 600),
        category="Créditos",
    )
    cleaned = use_case.execute(page)
    assert cleaned.chunks is not None
    assert len(cleaned.chunks) > 1


def test_clean_content_short_text_single_chunk():
    use_case = CleanContentUseCase()
    page = Page.create(
        url="https://www.bancolombia.com/personas",
        title="Test",
        content=" ".join(["palabra"] * 100),
        category="General",
    )
    cleaned = use_case.execute(page)
    assert len(cleaned.chunks) == 1


@pytest.mark.asyncio
async def test_crawl_website_stops_when_site_exhausted():
    mock_crawler = MagicMock()
    mock_crawler.discover_links = AsyncMock(return_value=[])
    mock_crawler.is_allowed_by_robots = AsyncMock(return_value=True)

    use_case = CrawlWebsiteUseCase(crawler_repository=mock_crawler)
    pages = await use_case.execute(base_url="https://www.bancolombia.com/personas")
    assert len(pages) == 0