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
            # 요청당 1회 호출(recommendation_pipeline.build_context) — vercel.json
            # maxDuration=30 예산에서 LLM 추천-이유 호출들에 쓸 여유를 남긴다.
            timeout=10.0,
        )
        response.raise_for_status()
        data = sorted(response.json()["data"], key=lambda item: item["index"])
        # HF provider 와 같이 count/dim 을 여기서 막는다. SQLite(테스트)는 길이가
        # 틀린 벡터도 받아 주므로, 잘못된 모델·dimensions 가 운영 INSERT 전까지
        # 조용히 오염되지 않게 한다.
        if len(data) != len(texts):
            raise ValueError(
                f"OpenAI 임베딩 결과 수 불일치: 입력 {len(texts)}건, 응답 {len(data)}건"
            )
        vectors: list[list[float]] = []
        for item in data:
            vector = item["embedding"]
            if len(vector) != self._dim:
                raise ValueError(
                    f"OpenAI 임베딩 차원 불일치: EMBEDDING_DIM={self._dim} 인데 "
                    f"{len(vector)}차원이 왔습니다 (model={self._model!r}). "
                    "모델과 EMBEDDING_DIM 을 맞추세요."
                )
            vectors.append(vector)
        return vectors
