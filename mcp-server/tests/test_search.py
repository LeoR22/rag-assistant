import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from unittest.mock import MagicMock
from datetime import datetime
from domain.entities.document import Document
from application.use_cases.search_knowledge import SearchKnowledgeUseCase
from application.use_cases.get_article import GetArticleByUrlUseCase
from application.use_cases.list_categories import ListCategoriesUseCase


def make_document(url="https://www.bancolombia.com/personas/creditos"):
    return Document(
        id=f"{url}__chunk_0",
        url=url,
        title="Créditos Bancolombia",
        content="Contenido de prueba sobre créditos de Bancolombia",
        category="Créditos",
        chunk_index=0,
        total_chunks=1,
        indexed_at=datetime.utcnow(),
        relevance_score=0.9,
    )


def test_search_empty_query_raises_error():
    mock_repo = MagicMock()
    mock_repo.is_empty.return_value = False
    use_case = SearchKnowledgeUseCase(vector_repository=mock_repo)
    with pytest.raises(ValueError):
        use_case.execute(query="")


def test_search_empty_repository_raises_error():
    mock_repo = MagicMock()
    mock_repo.is_empty.return_value = True
    use_case = SearchKnowledgeUseCase(vector_repository=mock_repo)
    with pytest.raises(RuntimeError):
        use_case.execute(query="créditos")


def test_search_returns_results():
    mock_repo = MagicMock()
    mock_repo.is_empty.return_value = False
    mock_repo.search.return_value = [make_document()]
    use_case = SearchKnowledgeUseCase(vector_repository=mock_repo)
    results = use_case.execute(query="créditos de vivienda")
    assert len(results) == 1
    assert results[0].category == "Créditos"


def test_get_article_invalid_url_raises_error():
    mock_repo = MagicMock()
    mock_repo.is_empty.return_value = False
    use_case = GetArticleByUrlUseCase(vector_repository=mock_repo)
    with pytest.raises(ValueError):
        use_case.execute(url="https://www.google.com/page")


def test_get_article_empty_url_raises_error():
    mock_repo = MagicMock()
    mock_repo.is_empty.return_value = False
    use_case = GetArticleByUrlUseCase(vector_repository=mock_repo)
    with pytest.raises(ValueError):
        use_case.execute(url="")


def test_list_categories_returns_list():
    mock_repo = MagicMock()
    mock_repo.is_empty.return_value = False
    mock_repo.list_categories.return_value = ["Créditos", "Ahorro", "Seguros"]
    use_case = ListCategoriesUseCase(vector_repository=mock_repo)
    categories = use_case.execute()
    assert len(categories) == 3
    assert "Créditos" in categories