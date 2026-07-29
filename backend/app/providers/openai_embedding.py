"""OpenAI Embeddings provider.

Groq LLM provider(`app/providers/groq.py`)와 동일하게 SDK 없이 `httpx`만으로
호출한다. `dimensions` 파라미터로 `text-embedding-3-small`을 축소 차원으로 요청해
기존 `embedding_dim`/`Vector(dim)` 컬럼과 마이그레이션 없이 맞춘다.
"""

from __future__ import annotations

import httpx


class OpenAIEmbeddingProvider:
    """OpenAI Embeddings API(`/embeddings`)를 호출하는 `EmbeddingProvider` 구현."""

    def __init__(self, api_key: str, model: str, base_url: str, dimensions: int) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._dimensions = dimensions

    @property
    def dimension(self) -> int:
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = httpx.post(
            f"{self._base_url}/embeddings",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"model": self._model, "input": texts, "dimensions": self._dimensions},
            timeout=30.0,
        )
        response.raise_for_status()
        # OpenAI는 입력 순서를 보장한다고 문서화하지만, index로 재정렬해 texts와의
        # 정렬을 안전하게 보장한다.
        data = sorted(response.json()["data"], key=lambda item: item["index"])
        return [item["embedding"] for item in data]
