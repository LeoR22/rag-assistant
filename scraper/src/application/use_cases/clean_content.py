import re
from typing import List
from loguru import logger
from domain.entities.page import Page


class CleanContentUseCase:
    """Caso de uso: limpia y divide el contenido en chunks para RAG"""

    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

    def execute(self, page: Page) -> Page:
        """Limpia el contenido y genera chunks"""
        cleaned = self._clean_text(page.content)
        chunks = self._create_chunks(cleaned)

        return Page(
            url=page.url,
            title=page.title,
            content=cleaned,
            category=page.category,
            extracted_at=page.extracted_at,
            word_count=len(cleaned.split()),
            chunks=chunks,
        )

    def _clean_text(self, text: str) -> str:
        """Elimina caracteres especiales y espacios innecesarios"""
        # Elimina múltiples espacios y saltos de línea
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        # Elimina caracteres especiales no útiles
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\"\'\n]', '', text)
        return text.strip()

    def _create_chunks(self, text: str) -> List[str]:
        """
        Divide el texto en chunks con overlap.
        Estrategia: chunks por palabras con overlap para no perder contexto.
        Tamaño: 500 palabras — balance entre contexto y precisión del retrieval.
        Overlap: 50 palabras — evita perder información en los bordes.
        """
        words = text.split()
        chunks = []

        if len(words) <= self.CHUNK_SIZE:
            return [text]

        start = 0
        while start < len(words):
            end = start + self.CHUNK_SIZE
            chunk = ' '.join(words[start:end])
            chunks.append(chunk)
            start += self.CHUNK_SIZE - self.CHUNK_OVERLAP

        logger.debug(f"Generados {len(chunks)} chunks")
        return chunks