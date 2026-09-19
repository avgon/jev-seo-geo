"""Shared Jev + LLM client layer."""

from __future__ import annotations

import json
import os
import ssl
import urllib.request
from typing import Any


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
        with urllib.request.urlopen(req, timeout=timeout, context=self._ctx) as r:
            return json.loads(r.read().decode()).get("answers", {})


class LLMProber:
    """Query LLM APIs and return raw text responses."""

    ENDPOINTS = {
        "openai": ("https://api.openai.com/v1/chat/completions", "OPENAI_API_KEY", "gpt-4o-mini"),
        "anthropic": ("https://api.anthropic.com/v1/messages", "ANTHROPIC_API_KEY", "claude-sonnet-4-20250514"),
        "google": ("https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", "GOOGLE_API_KEY", "gemini-2.0-flash"),
    }

    def __init__(self, keys: dict[str, str] | None = None):
        self.keys: dict[str, str] = {}
        for provider, (_, env_var, _) in self.ENDPOINTS.items():
            key = (keys or {}).get(provider) or os.getenv(env_var, "")
            if key:
                self.keys[provider] = key
        self._ctx = ssl.create_default_context()

    @property
    def available_models(self) -> list[str]:
        return list(self.keys.keys())

    def query(self, prompt: str, provider: str, timeout: int = 30) -> str:
        """Send a prompt to a provider and return the text response."""
        if provider not in self.keys:
            raise ValueError(f"No API key for {provider}. Set {self.ENDPOINTS[provider][1]}")

        url, _, default_model = self.ENDPOINTS[provider]
        key = self.keys[provider]

        if provider == "openai":
            return self._query_openai(prompt, url, key, default_model, timeout)
        elif provider == "anthropic":
            return self._query_anthropic(prompt, url, key, default_model, timeout)
        elif provider == "google":
            return self._query_google(prompt, url, key, default_model, timeout)
        return ""

    def query_all(self, prompt: str, timeout: int = 30) -> dict[str, str]:
        """Query all available models."""
        results = {}
        for provider in self.available_models:
            try:
                results[provider] = self.query(prompt, provider, timeout)
            except Exception as e:
                results[provider] = f"[ERROR: {e}]"
        return results

    def _query_openai(self, prompt: str, url: str, key: str, model: str, timeout: int) -> str:
        payload = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1024}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=timeout, context=self._ctx) as r:
            data = json.loads(r.read().decode())
        return data["choices"][0]["message"]["content"]

    def _query_anthropic(self, prompt: str, url: str, key: str, model: str, timeout: int) -> str:
        payload = json.dumps({"model": model, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01",
        })
        with urllib.request.urlopen(req, timeout=timeout, context=self._ctx) as r:
            data = json.loads(r.read().decode())
        return data["content"][0]["text"]

    def _query_google(self, prompt: str, url: str, key: str, model: str, timeout: int) -> str:
        url = url.replace("{model}", model) + f"?key={key}"
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout, context=self._ctx) as r:
            data = json.loads(r.read().decode())
        return data["candidates"][0]["content"]["parts"][0]["text"]
