import os
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from loguru import logger
import chromadb
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domain.entities.document import Document
from domain.repositories.vector_repository import VectorRepository
from infrastructure.embeddings.embedding_generator import EmbeddingGenerator

load_dotenv()


class ChromaRepository(VectorRepository):
    """
    Implementación de VectorRepository usando ChromaDB.

    ChromaDB elegido por:
    - Gratuito y local — sin costos ni dependencias externas
    - Persistencia en disco — los datos sobreviven reinicios
    - Filtrado por metadatos — permite filtrar por categoría, URL
    - Fácil de dockerizar
    - Migrable a Qdrant/Pinecone sin cambiar el dominio (inversión de dependencias)
    """

    def __init__(self):
        chroma_path = os.getenv("CHROMA_PATH", "data/chroma")
        collection_name = os.getenv("CHROMA_COLLECTION", "bancolombia")

        self._client = chromadb.PersistentClient(path=chroma_path)
        self._embedding_generator = EmbeddingGenerator()
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",
                "embedding_dimension": int(os.getenv("EMBEDDING_DIMENSION", 3072)),
            },
        )
        logger.success(f"ChromaDB inicializado — colección: {collection_name}")

    def add_documents(self, documents: List[Document]) -> None:
        if not documents:
            logger.warning("No hay documentos para indexar")
            return

        ids = [doc.id for doc in documents]
        contents = [doc.content for doc in documents]
        metadatas = [
            {
                "url": doc.url,
                "title": doc.title,
                "category": doc.category,
                "chunk_index": doc.chunk_index,
                "total_chunks": doc.total_chunks,
                "indexed_at": doc.indexed_at.isoformat(),
            }
            for doc in documents
        ]

        logger.info(f"Generando embeddings para {len(documents)} documentos")
        embeddings = self._embedding_generator.generate_batch(contents)

        self._collection.add(
            ids=ids,
            documents=contents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.success(f"Indexados {len(documents)} documentos en ChromaDB")

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> List[Document]:
        if not query or not query.strip():
            raise ValueError("La consulta no puede estar vacía")

        query_embedding = self._embedding_generator.generate(query)
        where = {"category": category} if category else None

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        documents = []
        for i, doc_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            relevance_score = round(1 - distance, 4)

            doc = Document(
                id=doc_id,
                url=metadata["url"],
                title=metadata["title"],
                content=results["documents"][0][i],
                category=metadata["category"],
                chunk_index=metadata["chunk_index"],
                total_chunks=metadata["total_chunks"],
                indexed_at=datetime.fromisoformat(metadata["indexed_at"]),
                relevance_score=relevance_score,
            )
            documents.append(doc)

        return documents

    def get_by_url(self, url: str) -> List[Document]:
        if not url or not url.strip():
            raise ValueError("La URL no puede estar vacía")

        results = self._collection.get(
            where={"url": url},
            include=["documents", "metadatas"],
        )

        if not results["ids"]:
            return []

        documents = []
        for i, doc_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i]
            doc = Document(
                id=doc_id,
                url=metadata["url"],
                title=metadata["title"],
                content=results["documents"][i],
                category=metadata["category"],
                chunk_index=metadata["chunk_index"],
                total_chunks=metadata["total_chunks"],
                indexed_at=datetime.fromisoformat(metadata["indexed_at"]),
            )
            documents.append(doc)

        return sorted(documents, key=lambda d: d.chunk_index)

    def list_categories(self) -> List[str]:
        results = self._collection.get(include=["metadatas"])
        if not results["metadatas"]:
            return []
        categories = list({m["category"] for m in results["metadatas"]})
        return sorted(categories)

    def get_stats(self) -> dict:
        count = self._collection.count()
        categories = self.list_categories()
        return {
            "total_documents": count,
            "categories": categories,
            "total_categories": len(categories),
            "embedding_model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"),
            "embedding_dimension": int(os.getenv("EMBEDDING_DIMENSION", 3072)),
            "vector_db": "ChromaDB",
            "last_updated": datetime.utcnow().isoformat(),
        }

    def is_empty(self) -> bool:
        return self._collection.count() == 0