"""Model provider abstraction for splay.

Uses the Fireworks backend directly (same as FirePass) but owns the call.
"""

import os

import httpx


API_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
DEFAULT_MODEL = "accounts/fireworks/routers/kimi-k2p6-turbo"


class ProviderError(Exception):
    pass


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
        self.model = model or os.environ.get("FIREPASS_MODEL", DEFAULT_MODEL)
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
            resp = client.post(API_URL, headers=headers, json=payload)
            if resp.status_code != 200:
                body = resp.text[:500]
                raise ProviderError(f"API ERROR {resp.status_code}: {body}")
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise ProviderError("No choices in API response")
            return choices[0]["message"]["content"]
