"""
LLM Client - OpenAI-compatible API client for the local LLM.
"""

import logging
import json
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for the locally deployed LLM via OpenAI-compatible API."""

    def __init__(
        self,
        api_base: str = "http://localhost:8080/v1",
        api_key: str = "not-needed",
        model_name: str = "llm-model",
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
    ) -> dict:
        """
        Send a chat completion request.
        Returns the full response dict from the API.
        """
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_response_text(self, messages: list[dict]) -> str:
        """Simple chat completion returning just the text response."""
        result = await self.chat(messages)
        return result["choices"][0]["message"]["content"]

    async def analyze_with_context(
        self, system_prompt: str, user_prompt: str, context: str = ""
    ) -> str:
        """
        Analyze with optional RAG context injected.
        """
        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({
                "role": "user",
                "content": f"Reference knowledge:\n{context}\n\n---\n\nNow analyze:\n{user_prompt}",
            })
        else:
            messages.append({"role": "user", "content": user_prompt})
        return await self.get_response_text(messages)
