import json
from pathlib import Path
from datetime import datetime
from typing import List
from loguru import logger
from domain.entities.page import Page


class JsonRepository:
    """Persiste las páginas scrapeadas en archivos JSON estructurados"""

    def __init__(self, output_dir: str = "data/raw"):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def save_page(self, page: Page) -> None:
        """Guarda una página como archivo JSON"""
        filename = self._url_to_filename(page.url)
        filepath = self._output_dir / filename

        data = {
            "url": page.url,
            "title": page.title,
            "content": page.content,
            "category": page.category,
            "extracted_at": page.extracted_at.isoformat(),
            "word_count": page.word_count,
            "chunks": page.chunks or [],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.success(f"Guardado: {filepath}")

    def save_all(self, pages: List[Page]) -> None:
        """Guarda todas las páginas y genera un índice"""
        for page in pages:
            self.save_page(page)

        self._save_index(pages)
        logger.info(f"Total guardado: {len(pages)} páginas en {self._output_dir}")

    def _save_index(self, pages: List[Page]) -> None:
        """Genera un índice con metadatos de todas las páginas"""
        index = {
            "total_pages": len(pages),
            "generated_at": datetime.utcnow().isoformat(),
            "pages": [
                {
                    "url": p.url,
                    "title": p.title,
                    "category": p.category,
                    "word_count": p.word_count,
                    "chunks_count": len(p.chunks) if p.chunks else 0,
                }
                for p in pages
            ],
        }

        index_path = self._output_dir / "index.json"
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        logger.success(f"Índice generado: {index_path}")

    def _url_to_filename(self, url: str) -> str:
        """Convierte una URL en nombre de archivo válido"""
        clean = url.replace("https://", "").replace("http://", "")
        clean = clean.replace("/", "_").replace(".", "_")
        return f"{clean[:100]}.json"