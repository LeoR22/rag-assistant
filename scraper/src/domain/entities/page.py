import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Page:
    """Entidad del dominio que representa una página scrapeada"""
    url: str
    title: str
    content: str
    category: str
    extracted_at: datetime
    word_count: int
    chunks: Optional[list[str]] = None
    content_hash: Optional[str] = None

    @classmethod
    def create(cls, url: str, title: str, content: str, category: str) -> "Page":
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return cls(
            url=url,
            title=title,
            content=content,
            category=category,
            extracted_at=datetime.utcnow(),
            word_count=len(content.split()),
            content_hash=content_hash,
        )

    def is_valid(self) -> bool:
        return (
            bool(self.url)
            and bool(self.content)
            and self.word_count > 50
        )