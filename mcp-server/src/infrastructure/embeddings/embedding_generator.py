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

    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise EnvironmentError("GITHUB_TOKEN no está configurado en .env")

        github_models_url = os.getenv("GITHUB_MODELS_URL")
        if not github_models_url:
            raise EnvironmentError("GITHUB_MODELS_URL no está configurado en .env")

        embedding_model = os.getenv("EMBEDDING_MODEL")
        if not embedding_model:
            raise EnvironmentError("EMBEDDING_MODEL no está configurado en .env")

        embedding_dimension = os.getenv("EMBEDDING_DIMENSION")
        if not embedding_dimension:
            raise EnvironmentError("EMBEDDING_DIMENSION no está configurado en .env")

        self._client = OpenAI(
            base_url=github_models_url,
            api_key=token,
        )
        self._model = embedding_model
        self._dimension = int(embedding_dimension)
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
        batch_size = 16

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