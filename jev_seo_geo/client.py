"""Shared Jev + LLM client layer."""

from __future__ import annotations

import json
import os
import ssl
import urllib.request
from typing import Any
from jev_seo_geo.validation import validate_answers, validate_text, safe_error


class ProviderError(RuntimeError):
    """Sanitized transport/JSON error; original exception details are not exposed."""
    def __init__(self, category):
        self.category = category
        super().__init__(category)


def _request_json(request, timeout, context):
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            return json.loads(response.read().decode())
    except Exception as error:
        raise ProviderError(safe_error(error)) from None


class JevClient:
    """Minimal TypeSafe Jev client."""

    URL = "https://api.typesafe.ai/v1/systemone"

    def __init__(self, api_key: str | None = None, model: str = "jev-latest"):
        self.api_key = api_key or os.getenv("TYPESAFE_API_KEY", "")
        if not self.api_key:
            raise ValueError("Set TYPESAFE_API_KEY or pass api_key=")
        self.model = model
        self._ctx = ssl.create_default_context()

    def ask(self, state: str, questions: dict[str, dict[str, Any]], timeout: int = 30) -> dict[str, Any]:
        payload = json.dumps({"model": self.model, "state": state, "questions": questions}).encode()
        req = urllib.request.Request(
            self.URL, data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
        )
        data = _request_json(req, timeout, self._ctx)
        if not isinstance(data, dict) or "answers" not in data:
            raise ValueError("Missing Jev answers envelope")
        validate_answers(data["answers"], questions)
        return data["answers"]


class LLMProber:
    """Query LLM APIs and return raw text responses."""

    ENDPOINTS = {
        "openai": ("https://api.openai.com/v1/chat/completions", "OPENAI_API_KEY", "gpt-4o-mini"),
        "anthropic": ("https://api.anthropic.com/v1/messages", "ANTHROPIC_API_KEY", "claude-sonnet-4-20250514"),
        "google": ("https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", "GOOGLE_API_KEY", "gemini-2.0-flash"),
    }

    def __init__(self, keys: dict[str, str] | None = None, *, models: dict[str, str] | None = None):
        unknown = (set(keys or {}) | set(models or {})) - set(self.ENDPOINTS)
        if unknown:
            raise ValueError("Unknown provider configuration")
        self.models = {p: endpoint[2] for p, endpoint in self.ENDPOINTS.items()}
        self.models.update(models or {})
        if any(not isinstance(m, str) or not m.strip() for m in self.models.values()):
            raise ValueError("Model IDs must be nonempty strings")
        self.keys: dict[str, str] = {}
        for provider, (_, env_var, _) in self.ENDPOINTS.items():
            key = keys.get(provider, "") if keys is not None else os.getenv(env_var, "")
            if key:
                self.keys[provider] = key
        self._ctx = ssl.create_default_context()

    @property
    def available_models(self) -> list[str]:
        return list(self.keys.keys())

    def query(self, prompt: str, provider: str, timeout: int = 30) -> str:
        """Send a prompt to a provider and return the text response."""
        if provider not in self.ENDPOINTS:
            raise ValueError("Unknown provider")
        if provider not in self.keys:
            raise ValueError(f"No API key for {provider}. Set {self.ENDPOINTS[provider][1]}")

        url, _, default_model = self.ENDPOINTS[provider]
        default_model = self.models[provider]
        key = self.keys[provider]

        if provider == "openai":
            result = self._query_openai(prompt, url, key, default_model, timeout)
        elif provider == "anthropic":
            result = self._query_anthropic(prompt, url, key, default_model, timeout)
        elif provider == "google":
            result = self._query_google(prompt, url, key, default_model, timeout)
        return validate_text(result, "provider response")

    def query_all(self, prompt: str, timeout: int = 30) -> dict[str, Any]:
        """Query all available models."""
        results = {}
        for provider in self.available_models:
            try:
                results[provider] = {"status": "success", "response": self.query(prompt, provider, timeout)}
            except Exception as e:
                results[provider] = {"status": "error", "error": safe_error(e)}
        return results

    def _query_openai(self, prompt: str, url: str, key: str, model: str, timeout: int) -> str:
        payload = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1024}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
        data = _request_json(req, timeout, self._ctx)
        choice = data["choices"][0]
        if choice.get("finish_reason") == "length":
            raise ValueError("Provider output was truncated")
        return choice["message"]["content"]

    def _query_anthropic(self, prompt: str, url: str, key: str, model: str, timeout: int) -> str:
        payload = json.dumps({"model": model, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01",
        })
        data = _request_json(req, timeout, self._ctx)
        if data.get("stop_reason") == "max_tokens":
            raise ValueError("Provider output was truncated")
        return "\n".join(block["text"] for block in data["content"] if block.get("type", "text") == "text")

    def _query_google(self, prompt: str, url: str, key: str, model: str, timeout: int) -> str:
        url = url.replace("{model}", model)
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "x-goog-api-key": key})
        data = _request_json(req, timeout, self._ctx)
        candidate = data["candidates"][0]
        if candidate.get("finishReason") == "MAX_TOKENS":
            raise ValueError("Provider output was truncated")
        return "\n".join(part["text"] for part in candidate["content"]["parts"] if "text" in part)
