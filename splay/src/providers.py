"""Model provider abstraction for splay."""

import os

import httpx

FIREWORKS_API_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
DEFAULT_FIREWORKS_MODEL = "accounts/fireworks/routers/kimi-k2p6-turbo"
DEFAULT_GEMMA_BASE_URL = "http://127.0.0.1:8080/v1"
DEFAULT_GEMMA_MODEL = "unsloth/gemma-4-26b-a4b-it-UD-MLX-4bit"


class ProviderError(Exception):
    """Raised when an inference provider cannot return a completion."""


class Provider:
    """Abstract inference provider."""

    def infer(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError


class FireworksProvider(Provider):
    """Call Fireworks API directly using the same credentials as FirePass."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ):
        self.api_key = api_key or os.environ.get("FIREWORKS_API_KEY")
        if not self.api_key:
            raise ProviderError("FIREWORKS_API_KEY not set")
        self.model = model or os.environ.get("FIREPASS_MODEL", DEFAULT_FIREWORKS_MODEL)
        self.timeout = timeout

    def infer(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(FIREWORKS_API_URL, headers=headers, json=payload)
            if resp.status_code != 200:
                body = resp.text[:500]
                raise ProviderError(f"API ERROR {resp.status_code}: {body}")
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise ProviderError("No choices in API response")
            return choices[0]["message"]["content"]


class OpenAICompatibleProvider(Provider):
    """Call an OpenAI-compatible chat-completions endpoint."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ):
        if not base_url.strip():
            raise ProviderError("OpenAI-compatible base_url is empty")
        if not model.strip():
            raise ProviderError("OpenAI-compatible model is empty")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.transport = transport

    def infer(self, system_prompt: str, user_prompt: str) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        url = f"{self.base_url}/chat/completions"
        try:
            with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
                resp = client.post(url, headers=headers, json=payload)
        except httpx.RequestError as exc:
            raise ProviderError(
                f"Could not reach OpenAI-compatible server at {url}; "
                "start the server or set SPLAY_GEMMA_BASE_URL."
            ) from exc
        if resp.status_code != 200:
            body = resp.text[:500]
            raise ProviderError(
                f"OpenAI-compatible API error {resp.status_code}: {body}"
            )
        try:
            data = resp.json()
        except ValueError as exc:
            raise ProviderError(
                "OpenAI-compatible API returned non-JSON response"
            ) from exc
        choices = data.get("choices", [])
        if not choices:
            raise ProviderError("No choices in OpenAI-compatible API response")
        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str):
            raise ProviderError(
                "OpenAI-compatible API response missing message.content"
            )
        return content


class GemmaProvider(OpenAICompatibleProvider):
    """Call the local Gemma OpenAI-compatible server."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ):
        resolved_base_url = (
            base_url
            or os.environ.get("SPLAY_GEMMA_BASE_URL")
            or os.environ.get("GEMMA_MCP_BASE_URL")
            or DEFAULT_GEMMA_BASE_URL
        )
        resolved_model = (
            model
            or os.environ.get("SPLAY_GEMMA_MODEL")
            or os.environ.get("GEMMA_MCP_MODEL")
            or DEFAULT_GEMMA_MODEL
        )
        resolved_api_key = (
            api_key
            if api_key is not None
            else os.environ.get("SPLAY_GEMMA_API_KEY")
            or os.environ.get("GEMMA_MCP_API_KEY")
        )
        super().__init__(
            base_url=resolved_base_url,
            model=resolved_model,
            api_key=resolved_api_key,
            timeout=timeout,
            transport=transport,
        )
