"""Groq LLM provider (OpenAI 호환 REST API).

Groq는 무료 티어로 Llama 계열 모델을 서빙하며, Chat Completions 엔드포인트가
OpenAI와 동일한 스펙이라 별도 SDK 없이 `httpx`만으로 호출한다.
"""

from __future__ import annotations

import httpx


class GroqLLMProvider:
    """Groq Chat Completions API를 호출하는 `LLMProvider` 구현."""

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    def chat(self, messages: list[dict]) -> str:
        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"model": self._model, "messages": messages},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
