from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Document:
    """Entidad del dominio que representa un documento indexado en la base vectorial"""
    id: str
    url: str
    title: str
    content: str
    category: str
    chunk_index: int
    total_chunks: int
    indexed_at: datetime
    embedding: Optional[list[float]] = None
    relevance_score: Optional[float] = None

    @classmethod
    def create(
        cls,
        url: str,
        title: str,
        content: str,
        category: str,
        chunk_index: int = 0,
        total_chunks: int = 1,
    ) -> "Document":
        doc_id = f"{url}__chunk_{chunk_index}"
        return cls(
            id=doc_id,
            url=url,
            title=title,
            content=content,
            category=category,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            indexed_at=datetime.utcnow(),
        )

    def is_valid(self) -> bool:
        return bool(self.content) and len(self.content.split()) > 10