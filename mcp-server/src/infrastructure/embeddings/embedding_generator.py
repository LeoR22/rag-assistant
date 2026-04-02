import os
from typing import List
from loguru import logger
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()


class EmbeddingGenerator:
    """
    Genera embeddings usando sentence-transformers.
    
    Modelo elegido: paraphrase-multilingual-mpnet-base-v2
    - Dimensionalidad: 768
    - Multilingüe: soporta español nativamente
    - Gratuito: no requiere API key
    - Balance calidad/velocidad ideal para RAG
    """

    def __init__(self):
        model_name = os.getenv(
            "EMBEDDING_MODEL",
            "paraphrase-multilingual-mpnet-base-v2"
        )
        logger.info(f"Cargando modelo de embeddings: {model_name}")
        self._model = SentenceTransformer(model_name)
        self._dimension = int(os.getenv("EMBEDDING_DIMENSION", 768))
        logger.success(f"Modelo cargado — dimensión: {self._dimension}")

    def generate(self, text: str) -> List[float]:
        """Genera embedding para un texto"""
        embedding = self._model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para una lista de textos en batch"""
        logger.info(f"Generando embeddings para {len(texts)} textos")
        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
            batch_size=32,
        )
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        return self._dimension