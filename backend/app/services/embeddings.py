from abc import ABC, abstractmethod
import hashlib
import math
from collections.abc import Callable

import httpx

from app.config import get_settings


class EmbeddingProvider(ABC):
    dimensions: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class HashEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0 for _ in range(self.dimensions)]
        tokens = list(_tokenize(text))
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [round(value / norm, 8) for value in vector]


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        dimensions: int,
        client_factory: Callable[..., httpx.Client] = httpx.Client,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dimensions = dimensions
        self.client_factory = client_factory

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            raise ValueError("Embedding API key is required for OpenAI-compatible provider")
        payload = {"model": self.model, "input": texts, "dimensions": self.dimensions}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        with self.client_factory(timeout=60) as client:
            response = client.post(f"{self.base_url}/embeddings", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return [list(item["embedding"]) for item in data["data"]]


def get_embedding_provider(provider_name: str | None = None, dimensions: int | None = None) -> EmbeddingProvider:
    settings = get_settings()
    name = (provider_name or settings.embedding_provider).strip().lower()
    provider_dimensions = dimensions or settings.embedding_dimensions
    if name == "hash":
        return HashEmbeddingProvider(dimensions=provider_dimensions)
    if name in {"openai", "openai-compatible", "openai_compatible"}:
        return OpenAICompatibleEmbeddingProvider(
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url,
            model=settings.embedding_model,
            dimensions=provider_dimensions,
        )
    raise ValueError(f"Unsupported embedding provider: {name}")


def _tokenize(text: str):
    buffer = []
    chinese_buffer = []

    def flush_word_buffer():
        nonlocal buffer
        if buffer:
            yield "".join(buffer)
            buffer = []

    def flush_chinese_buffer():
        nonlocal chinese_buffer
        if not chinese_buffer:
            return
        sequence = "".join(chinese_buffer)
        for char in chinese_buffer:
            yield char
        for size in (2, 3, 4):
            if len(sequence) >= size:
                for index in range(len(sequence) - size + 1):
                    yield sequence[index:index + size]
        chinese_buffer = []

    for char in text.lower():
        if "\u4e00" <= char <= "\u9fff":
            yield from flush_word_buffer()
            chinese_buffer.append(char)
        elif char.isalnum():
            yield from flush_chinese_buffer()
            buffer.append(char)
        else:
            yield from flush_word_buffer()
            yield from flush_chinese_buffer()
    yield from flush_word_buffer()
    yield from flush_chinese_buffer()


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def vector_values(vector) -> list[float]:
    if vector is None:
        return []
    return list(vector)
