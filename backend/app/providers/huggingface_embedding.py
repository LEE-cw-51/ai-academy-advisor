"""HuggingFace Inference 임베딩 provider (feature-extraction 태스크).

`BAAI/bge-m3`는 **네이티브 1024차원**이라 `Review.embedding`의 `Vector(1024)`와
그대로 맞는다 — OpenAI `text-embedding-3-*`처럼 `dimensions`로 잘라 쓸 필요가 없다.
한국어 검색에서 검증된 모델이고, `EMBEDDING_MODEL` 기본값이 처음부터 이 모델이었다.

Groq은 임베딩을 제공하지 않는다 (채팅·음성·가드 모델뿐). 그래서 LLM은 Groq,
임베딩은 HuggingFace로 provider가 갈린다. Groq LLM provider와 같이 별도 SDK 없이
`httpx`만으로 호출한다.

과금은 토큰이 아니라 CPU 시간 기준이고 무료 계정은 월 크레딧이 작다. 배치는
`--limit`으로 나눠 돌리며 소모량을 확인한다 (docs/decision-log.md).
"""

from __future__ import annotations

import time

import httpx

# 콜드 스타트(503 `model loading`) 재시도 간격. 지수 백오프를 쓰지 않는 이유는
# 요청 경로가 Vercel maxDuration 예산을 공유하기 때문이다 — 대기는 짧고 예측
# 가능해야 한다. 요청 경로는 애초에 max_retries=0으로 둔다.
_RETRY_WAIT_SECONDS = 2.0


class HuggingFaceEmbeddingProvider:
    """HF Inference feature-extraction을 호출하는 `EmbeddingProvider` 구현."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        dim: int,
        timeout: float = 10.0,
        max_retries: int = 0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._dim = dim
        self._timeout = timeout
        self._max_retries = max_retries

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def url(self) -> str:
        return f"{self._base_url}/models/{self._model}/pipeline/feature-extraction"

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._post_with_retry(texts)
        return self._parse(response.json(), expected=len(texts))

    def _post_with_retry(self, texts: list[str]) -> httpx.Response:
        """503(모델 로딩)만 재시도한다. 나머지 오류는 그대로 올린다."""
        attempts = self._max_retries + 1
        for attempt in range(attempts):
            response = httpx.post(
                self.url,
                headers={"Authorization": f"Bearer {self._api_key}"},
                # normalize: BGE-M3의 표준 사용법. pgvector가 코사인 거리(<=>)를
                # 쓰므로 순위는 같지만 score(1-distance) 해석이 안정된다.
                # truncate: 8192 토큰을 넘는 입력을 400 대신 잘라서 처리한다.
                json={"inputs": texts, "normalize": True, "truncate": True},
                timeout=self._timeout,
            )
            if response.status_code == 503 and attempt < attempts - 1:
                time.sleep(_RETRY_WAIT_SECONDS)
                continue
            response.raise_for_status()
            return response
        raise AssertionError("unreachable")  # pragma: no cover

    def _parse(self, payload: object, expected: int) -> list[list[float]]:
        """응답을 (expected, dim) 벡터 목록으로 검증한다.

        차원을 여기서 막지 않으면 조용히 오염된다 — SQLite(테스트)의 JSON 컬럼은
        길이가 틀린 벡터도 그대로 받아주고, 잘못된 모델을 가리켰다는 사실이
        운영 Postgres에 INSERT할 때까지 드러나지 않는다.
        """
        if not isinstance(payload, list):
            raise ValueError(f"HF 임베딩 응답이 배열이 아닙니다: {type(payload).__name__}")
        if len(payload) != expected:
            raise ValueError(
                f"HF 임베딩 결과 수 불일치: 입력 {expected}건, 응답 {len(payload)}건"
            )
        vectors: list[list[float]] = []
        for index, item in enumerate(payload):
            vector = self._as_vector(item, index)
            if len(vector) != self._dim:
                raise ValueError(
                    f"HF 임베딩 차원 불일치: EMBEDDING_DIM={self._dim} 인데 "
                    f"{len(vector)}차원이 왔습니다 (model={self._model!r}). "
                    "모델과 EMBEDDING_DIM 을 맞추세요."
                )
            vectors.append(vector)
        return vectors

    def _as_vector(self, item: object, index: int) -> list[float]:
        """문장 임베딩 1개를 꺼낸다.

        sentence-transformers 설정이 있는 모델은 풀링된 1차원 벡터를 준다. 설정이
        없으면 토큰 단위 2차원(`[토큰][차원]`)이 오므로 평균 풀링으로 맞춘다.
        """
        if not isinstance(item, list) or not item:
            raise ValueError(f"HF 임베딩 {index}번 항목이 비어 있거나 배열이 아닙니다")
        if all(isinstance(value, (int, float)) for value in item):
            return [float(value) for value in item]
        if all(isinstance(row, list) and row for row in item):
            width = len(item[0])
            if any(len(row) != width for row in item):
                raise ValueError(f"HF 임베딩 {index}번 토큰 벡터 길이가 제각각입니다")
            return [sum(row[i] for row in item) / len(item) for i in range(width)]
        raise ValueError(f"HF 임베딩 {index}번 항목의 형태를 해석할 수 없습니다")
