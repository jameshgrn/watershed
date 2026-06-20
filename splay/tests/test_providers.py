"""Provider tests without external API calls."""

import json
import os
from typing import cast
from unittest.mock import patch

import httpx

from splay.src.providers import (
    DEFAULT_GEMMA_BASE_URL,
    DEFAULT_GEMMA_MODEL,
    GemmaProvider,
    OpenAICompatibleProvider,
    ProviderError,
)

GEMMA_ENV_VARS = (
    "SPLAY_GEMMA_BASE_URL",
    "GEMMA_MCP_BASE_URL",
    "SPLAY_GEMMA_MODEL",
    "GEMMA_MCP_MODEL",
    "SPLAY_GEMMA_API_KEY",
    "GEMMA_MCP_API_KEY",
)


def _completion_response(content: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": content}}]},
    )


def test_openai_compatible_provider_posts_chat_completion_payload():
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers.get("authorization")
        captured["payload"] = json.loads(request.content)
        return _completion_response("ok")

    provider = OpenAICompatibleProvider(
        base_url="http://example.test/v1/",
        model="gemma-test",
        api_key="secret",
        transport=httpx.MockTransport(handler),
    )

    assert provider.infer("system", "user") == "ok"
    assert captured["url"] == "http://example.test/v1/chat/completions"
    assert captured["authorization"] == "Bearer secret"
    assert captured["payload"] == {
        "model": "gemma-test",
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
        ],
        "stream": False,
    }


def test_gemma_provider_defaults_to_local_openai_compatible_server():
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["payload"] = json.loads(request.content)
        captured["authorization"] = request.headers.get("authorization")
        return _completion_response("local")

    with patch.dict(os.environ, dict.fromkeys(GEMMA_ENV_VARS, "")):
        provider = GemmaProvider(transport=httpx.MockTransport(handler))

    assert provider.infer("system", "user") == "local"
    assert captured["url"] == f"{DEFAULT_GEMMA_BASE_URL}/chat/completions"
    payload = cast(dict[str, object], captured["payload"])
    assert payload["model"] == DEFAULT_GEMMA_MODEL
    assert captured["authorization"] is None


def test_gemma_provider_uses_environment_overrides():
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["payload"] = json.loads(request.content)
        captured["authorization"] = request.headers.get("authorization")
        return _completion_response("env")

    with patch.dict(
        os.environ,
        {
            "SPLAY_GEMMA_BASE_URL": "http://gemma.test/v1",
            "SPLAY_GEMMA_MODEL": "local-gemma",
            "SPLAY_GEMMA_API_KEY": "local-secret",
        },
    ):
        provider = GemmaProvider(transport=httpx.MockTransport(handler))

    assert provider.infer("system", "user") == "env"
    assert captured["url"] == "http://gemma.test/v1/chat/completions"
    payload = cast(dict[str, object], captured["payload"])
    assert payload["model"] == "local-gemma"
    assert captured["authorization"] == "Bearer local-secret"


def test_openai_compatible_provider_errors_on_missing_content():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {}}]})

    provider = OpenAICompatibleProvider(
        base_url="http://example.test/v1",
        model="gemma-test",
        transport=httpx.MockTransport(handler),
    )

    try:
        provider.infer("system", "user")
    except ProviderError as exc:
        assert "message.content or message.reasoning" in str(exc)
    else:
        raise AssertionError("ProviderError not raised")


def test_openai_compatible_provider_uses_reasoning_when_content_missing():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"reasoning": "reasoned response"}}]},
        )

    provider = OpenAICompatibleProvider(
        base_url="http://example.test/v1",
        model="gemma-test",
        transport=httpx.MockTransport(handler),
    )

    assert provider.infer("system", "user") == "reasoned response"
