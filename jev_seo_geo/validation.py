"""Strict shared response validation and explicit coverage limits."""
import math

MAX_TEXT_CHARS = 12000


def validate_text(text, name="text"):
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"{name} must be nonempty text")
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(f"{name} exceeds supported limit of {MAX_TEXT_CHARS} characters; nothing was truncated")
    return text


def validate_answers(answers, questions):
    if not isinstance(answers, dict):
        raise ValueError("Jev answers must be an object")
    values = {}
    for key, question in questions.items():
        if key not in answers:
            raise ValueError(f"Missing Jev answer: {key}")
        answer = answers[key]
        kind = question["type"]
        if not isinstance(answer, dict) or answer.get("type", kind) != kind or kind not in answer:
            raise ValueError(f"Invalid Jev answer schema: {key}")
        value = answer[kind]
        if kind == "choice":
            if not isinstance(value, str) or value not in question["criteria"]:
                raise ValueError(f"Invalid Jev choice: {key}")
        else:
            maximum = len(question["criteria"]) - 1 if kind == "score" else 1
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= maximum:
                raise ValueError(f"Invalid Jev numeric range: {key}")
        values[key] = value
    return values


def safe_error(error):
    # Never include exception messages, URLs, request bodies or credentials.
    import urllib.error
    from jev_seo_geo.client import ProviderError
    if isinstance(error, ProviderError):
        return error.category
    if isinstance(error, TimeoutError):
        return "timeout"
    if isinstance(error, urllib.error.HTTPError):
        return "http_error"
    if isinstance(error, urllib.error.URLError):
        return "timeout" if isinstance(error.reason, TimeoutError) else "transport_error"
    if isinstance(error, (ValueError, TypeError, KeyError, IndexError)):
        return "invalid_response"
    return "provider_error"
