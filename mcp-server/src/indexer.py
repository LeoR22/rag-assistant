import sys
import os
import json
from pathlib import Path

SRC_PATH = Path(__file__).parent
sys.path.insert(0, str(SRC_PATH))

from dotenv import load_dotenv
from loguru import logger
from datetime import datetime
from domain.entities.document import Document
from infrastructure.vector_store.chroma_repository import ChromaRepository

load_dotenv()


def load_pages_from_json(raw_data_path: str) -> list:
    """Carga las páginas scrapeadas desde los archivos JSON"""
    data_path = Path(raw_data_path)

    if not data_path.exists():
        raise FileNotFoundError(f"No se encontró el directorio: {data_path}")

    json_files = [f for f in data_path.glob("*.json") if f.name != "index.json"]
    logger.info(f"Archivos JSON encontrados: {len(json_files)}")

    pages = []
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                pages.append(data)
        except Exception as e:
            logger.error(f"Error leyendo {json_file}: {e}")

    return pages


def create_documents_from_pages(pages: list) -> list[Document]:
    """Convierte páginas JSON en documentos para indexar"""
    documents = []

    for page in pages:
        chunks = page.get("chunks", [])

        if not chunks:
            chunks = [page.get("content", "")]

        total_chunks = len(chunks)

        for i, chunk in enumerate(chunks):
            if not chunk or len(chunk.split()) < 10:
                continue

            doc = Document.create(
                url=page["url"],
                title=page.get("title", ""),
                content=chunk,
                category=page.get("category", "General"),
                chunk_index=i,
                total_chunks=total_chunks,
            )
            documents.append(doc)

    logger.info(f"Documentos creados: {len(documents)}")
    return documents


def main():
    raw_data_path = os.getenv("RAW_DATA_PATH", "../scraper/data/raw")

    logger.info("Iniciando indexador de conocimiento")
    logger.info(f"Leyendo datos desde: {raw_data_path}")

    # 1. Cargar páginas
    pages = load_pages_from_json(raw_data_path)
    logger.info(f"Páginas cargadas: {len(pages)}")

    # 2. Crear documentos con chunks
    documents = create_documents_from_pages(pages)

    # 3. Indexar en ChromaDB
    logger.info("🔢 Indexando en ChromaDB...")
    repository = ChromaRepository()
    repository.add_documents(documents)

    # 4. Mostrar estadísticas
    stats = repository.get_stats()
    logger.success(f"✅ Indexación completada")
    logger.info(f"📊 Total documentos: {stats['total_documents']}")
    logger.info(f"📁 Categorías: {stats['categories']}")


if __name__ == "__main__":
    main()