import os
from typing import List
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class EmbeddingGenerator:
    """
    Genera embeddings usando GitHub Models (Azure OpenAI).

    Modelo elegido: text-embedding-3-large
    - Dimensionalidad: 3072 — mayor separación semántica
    - Multilingüe nativo — entrenado con contenido en español
    - Supera sentence-transformers en benchmarks MTEB
    - Gratuito via GitHub Models token
    """

    GITHUB_MODELS_URL = "https://models.inference.ai.azure.com"

    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise EnvironmentError("GITHUB_TOKEN no está configurado en .env")

        self._client = OpenAI(
            base_url=self.GITHUB_MODELS_URL,
            api_key=token,
        )
        self._model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
        self._dimension = int(os.getenv("EMBEDDING_DIMENSION", 3072))
        logger.success(f"EmbeddingGenerator listo — modelo: {self._model} | dimensión: {self._dimension}")

    def generate(self, text: str) -> List[float]:
        """Genera embedding para un texto"""
        if not text or not text.strip():
            raise ValueError("El texto no puede estar vacío")

        response = self._client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para una lista de textos"""
        if not texts:
            return []

        logger.info(f"Generando embeddings para {len(texts)} textos")

        embeddings = []
        batch_size = 16  # GitHub Models tiene límite de rate

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self._client.embeddings.create(
                model=self._model,
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
            logger.debug(f"Batch {i//batch_size + 1} completado — {len(embeddings)}/{len(texts)}")

        return embeddings

    @property
    def dimension(self) -> int:
        return self._dimension