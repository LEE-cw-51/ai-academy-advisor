"""OpenAI 임베딩 provider (Embeddings REST API).

`text-embedding-3-*` 계열은 요청 시 `dimensions`를 지정해 벡터를 축소(Matryoshka
truncation)할 수 있어, 기존 `EMBEDDING_DIM`(1024)과 마이그레이션 스키마를 그대로
유지한 채 사용할 수 있다. Groq LLM provider와 동일하게 별도 SDK 없이 `httpx`만으로
호출한다.
"""

from __future__ import annotations

import httpx


class OpenAIEmbeddingProvider:
    """OpenAI Embeddings API를 호출하는 `EmbeddingProvider` 구현."""

    def __init__(self, api_key: str, model: str, base_url: str, dim: int) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = httpx.post(
            f"{self._base_url}/embeddings",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"model": self._model, "input": texts, "dimensions": self._dim},
            timeout=30.0,
        )
        response.raise_for_status()
        data = sorted(response.json()["data"], key=lambda item: item["index"])
        return [item["embedding"] for item in data]
