"""결정적(deterministic) stub provider 구현.

실제 모델/API 호출 없이 파이프라인 골격을 검증하기 위한 구현이다. 같은 입력에는
항상 같은 출력을 내므로 테스트에 안전하고, API 키 없이도 앱이 기동된다.
"""

from __future__ import annotations

import hashlib
import math

from app.providers.base import Hit


class StubEmbeddingProvider:
    """텍스트 해시를 시드로 결정적 단위벡터를 생성한다.

    의미론적 유사도를 갖지는 않지만, 같은 텍스트는 같은 벡터로 매핑되고 L2 정규화되어
    코사인 유사도 계산이 안정적이다.
    """

    def __init__(self, dim: int) -> None:
        if dim <= 0:
            raise ValueError("embedding dimension은 양수여야 합니다")
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def _embed_one(self, text: str) -> list[float]:
        # 텍스트별 해시를 시드로, 차원 인덱스마다 바이트를 확장해 값을 뽑는다.
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        raw: list[float] = []
        for i in range(self._dim):
            h = hashlib.sha256(seed + i.to_bytes(4, "big")).digest()
            # 첫 4바이트를 [-1, 1) 범위 부동소수로 변환
            value = int.from_bytes(h[:4], "big") / 2**32 * 2 - 1
            raw.append(value)
        norm = math.sqrt(sum(v * v for v in raw)) or 1.0
        return [v / norm for v in raw]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]


class StubLLMProvider:
    """마지막 user 메시지를 요약·에코하는 결정적 응답을 만든다."""

    def chat(self, messages: list[dict]) -> str:
        last_user = ""
        for message in messages:
            if message.get("role") == "user":
                last_user = str(message.get("content", ""))
        preview = last_user.strip().replace("\n", " ")
        if len(preview) > 200:
            preview = preview[:200] + "…"
        return f"[stub-llm] 입력을 받았습니다: {preview}"


class StubVectorStore:
    """in-memory 코사인 유사도 검색소."""

    def __init__(self) -> None:
        self._items: list[tuple[str, list[float]]] = []

    def add(self, items: list[tuple[str, list[float]]]) -> None:
        self._items.extend(items)

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            raise ValueError(f"embedding dimension mismatch: {len(a)} != {len(b)}")
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1.0
        nb = math.sqrt(sum(y * y for y in b)) or 1.0
        return dot / (na * nb)

    def search(self, embedding: list[float], top_k: int) -> list[Hit]:
        scored = [
            Hit(id=item_id, score=self._cosine(embedding, vector))
            for item_id, vector in self._items
        ]
        scored.sort(key=lambda hit: hit.score, reverse=True)
        return scored[:top_k]
