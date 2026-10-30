import hashlib
import math
from abc import ABC, abstractmethod
import httpx
from packages.core.config import get_settings
from packages.observability.logger import logger

settings = get_settings()


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dimensions(self) -> int:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        pass


class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        self._dimensions = settings.EMBEDDING_DIMENSIONS
        self._model_name = settings.EMBEDDING_MODEL
        self._url = f"{settings.OLLAMA_URL}/api/embed"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        # Batch in groups of 32
        batch_size = 32
        results: list[list[float]] = []

        with httpx.Client(timeout=120.0) as client:
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                resp = client.post(
                    self._url,
                    json={"model": self._model_name, "input": batch},
                )
                if resp.status_code != 200:
                    raise RuntimeError(f"Ollama embedding failed ({resp.status_code}): {resp.text}")

                data = resp.json()
                embeddings = data.get("embeddings", [])
                for emb in embeddings:
                    # L2 normalize
                    norm = math.sqrt(sum(x * x for x in emb)) or 1.0
                    results.append([x / norm for x in emb])

        return results


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic, fast mock embeddings for unit and integration testing."""

    def __init__(self):
        self._dimensions = settings.EMBEDDING_DIMENSIONS
        self._model_name = "mock-v1"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for text in texts:
            seed = hashlib.sha256(text.encode("utf-8")).digest()
            vec = [(seed[i % len(seed)] / 255.0) - 0.5 for i in range(self._dimensions)]
            norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            results.append([x / norm for x in vec])
        return results


def get_embedding_provider() -> EmbeddingProvider:
    if settings.EMBEDDING_PROVIDER == "mock":
        return MockEmbeddingProvider()
    elif settings.EMBEDDING_PROVIDER == "ollama":
        return OllamaEmbeddingProvider()
    return OllamaEmbeddingProvider()

