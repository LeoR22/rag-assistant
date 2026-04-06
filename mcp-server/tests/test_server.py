import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from domain.entities.document import Document


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


# ── Tests search_knowledge_base tool ────────────────────────

class TestSearchKnowledgeBaseTool:

    def test_search_returns_results(self):
        """Tool retorna resultados estructurados correctamente"""
        mock_repo = MagicMock()
        mock_repo.is_empty.return_value = False
        mock_repo.search.return_value = [make_document()]

        with patch("server.get_repository", return_value=mock_repo):
            from server import search_knowledge_base
            result = search_knowledge_base(query="crédito vivienda", top_k=5)

            assert result["query"] == "crédito vivienda"
            assert result["total_results"] == 1
            assert len(result["results"]) == 1
            assert result["results"][0]["url"] == "https://www.bancolombia.com/personas/creditos"

    def test_search_empty_query_returns_error(self):
        """Query vacía retorna error estructurado sin explotar"""
        mock_repo = MagicMock()
        mock_repo.is_empty.return_value = False

        with patch("server.get_repository", return_value=mock_repo):
            from server import search_knowledge_base
            result = search_knowledge_base(query="", top_k=5)

            assert "error" in result
            assert result["results"] == []

    def test_search_database_unavailable_returns_error(self):
        """ChromaDB no disponible retorna error graceful"""
        with patch("server.get_repository", side_effect=RuntimeError("ChromaDB no disponible")):
            from server import search_knowledge_base
            result = search_knowledge_base(query="crédito vivienda")

            assert "error" in result
            assert result["results"] == []

    def test_search_multiple_results(self):
        """Búsqueda retorna múltiples resultados correctamente"""
        mock_repo = MagicMock()
        mock_repo.is_empty.return_value = False
        mock_repo.search.return_value = [
            make_document("https://www.bancolombia.com/personas/creditos/vivienda"),
            make_document("https://www.bancolombia.com/personas/creditos/consumo"),
        ]

        with patch("server.get_repository", return_value=mock_repo):
            from server import search_knowledge_base
            result = search_knowledge_base(query="créditos", top_k=5)

            assert result["total_results"] == 2


# ── Tests get_article_by_url tool ───────────────────────────

class TestGetArticleByUrlTool:

    def test_get_article_returns_content(self):
        """Retorna contenido completo de un artículo"""
        mock_repo = MagicMock()
        mock_repo.is_empty.return_value = False
        mock_repo.get_by_url.return_value = [
            make_document("https://www.bancolombia.com/personas/creditos/vivienda")
        ]

        with patch("server.get_repository", return_value=mock_repo):
            from server import get_article_by_url
            result = get_article_by_url(
                url="https://www.bancolombia.com/personas/creditos/vivienda"
            )

            assert result["url"] == "https://www.bancolombia.com/personas/creditos/vivienda"
            assert "content" in result
            assert result["category"] == "Créditos"

    def test_get_article_invalid_url_returns_error(self):
        """URL fuera del dominio retorna error"""
        mock_repo = MagicMock()
        mock_repo.is_empty.return_value = False

        with patch("server.get_repository", return_value=mock_repo):
            from server import get_article_by_url
            result = get_article_by_url(url="https://www.google.com/page")

            assert "error" in result

    def test_get_article_empty_url_returns_error(self):
        """URL vacía retorna error"""
        mock_repo = MagicMock()
        mock_repo.is_empty.return_value = False

        with patch("server.get_repository", return_value=mock_repo):
            from server import get_article_by_url
            result = get_article_by_url(url="")

            assert "error" in result

    def test_get_article_database_unavailable(self):
        """ChromaDB no disponible retorna error graceful"""
        with patch("server.get_repository", side_effect=RuntimeError("No disponible")):
            from server import get_article_by_url
            result = get_article_by_url(
                url="https://www.bancolombia.com/personas/creditos"
            )

            assert "error" in result


# ── Tests list_categories tool ───────────────────────────────

class TestListCategoriesTool:

    def test_list_categories_returns_all(self):
        """Retorna todas las categorías disponibles"""
        mock_repo = MagicMock()
        mock_repo.is_empty.return_value = False
        mock_repo.list_categories.return_value = [
            "Ahorro", "Créditos", "General",
            "Inversiones", "Pagos y Transferencias",
            "Seguros", "Tarjetas"
        ]

        with patch("server.get_repository", return_value=mock_repo):
            from server import list_categories
            result = list_categories()

            assert result["total_categories"] == 7
            assert "Ahorro" in result["categories"]
            assert "Créditos" in result["categories"]
            assert "Tarjetas" in result["categories"]

    def test_list_categories_empty_db_returns_error(self):
        """Base vacía retorna error estructurado"""
        mock_repo = MagicMock()
        mock_repo.is_empty.return_value = True

        with patch("server.get_repository", return_value=mock_repo):
            from server import list_categories
            result = list_categories()

            assert "error" in result

    def test_list_categories_database_unavailable(self):
        """ChromaDB no disponible retorna error graceful"""
        with patch("server.get_repository", side_effect=RuntimeError("No disponible")):
            from server import list_categories
            result = list_categories()

            assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])