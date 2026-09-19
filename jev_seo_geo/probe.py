"""Sample API responses and measure literal mentions, not endorsements."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from jev_seo_geo.client import LLMProber, JevClient
from jev_seo_geo.validation import validate_text, safe_error


@dataclass
class ProbeResult:
    model: str
    query: str
    response: str
    mentioned: bool | None
    rank: int | None
    context: str
    status: Literal["success", "error"] = "success"
    error: str | None = None
    timestamp: str = ""
    model_id: str = ""
    sample: int = 1
    method: str = "unicode_literal_boundary_v1; explicit_numbered_item_only"


@dataclass
class BrandReport:
    brand: str
    results: list[ProbeResult]
    mention_rate: float | None
    avg_rank: float | None
    best_query: str
    worst_query: str
    success_count: int = 0
    error_count: int = 0
    status: str = "failed"
    error_counts: dict[str, int] = field(default_factory=dict)


def _detect_brand(brand: str, text: str, jev: JevClient | None = None):
    validate_text(brand, "brand")
    pattern = re.compile(r"(?<!\w)" + re.escape(brand.strip()) + r"(?!\w)", re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return False, None, ""
    rank = None
    for line in text.splitlines():
        # Only a brand at the start of a numbered item's label is ordinal evidence.
        item = re.match(r"^\s*(\d+)[.)]\s+(?:\*\*)?", line)
        if item and int(item[1]) > 0 and pattern.match(line, item.end()):
            rank = int(item[1])
            break
    return True, rank, text[max(0, match.start()-80):match.end()+80].strip()


def capture(queries, *, models=None, prober=None, samples=1):
    p = prober or LLMProber()
    target_models = p.available_models if models is None else models
    if not target_models:
        raise ValueError("No LLM providers configured")
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 1:
        raise ValueError("samples must be a positive integer")
    if not queries:
        raise ValueError("At least one query is required")
    if any(model not in p.available_models for model in target_models):
        raise ValueError("Unknown or unconfigured provider")
    for query in queries:
        validate_text(query, "query")
    observations = []
    for query in dict.fromkeys(queries):
        for model in dict.fromkeys(target_models):
            for sample in range(1, samples + 1):
                result = ProbeResult(model, query, "", None, None, "", timestamp=datetime.now(timezone.utc).isoformat(), model_id=getattr(p, "models", {}).get(model, model), sample=sample)
                try:
                    result.response = validate_text(p.query(f"List and briefly describe the top options for: {query}. Be specific with names.", model), "provider response")
                except Exception as error:
                    result.status = "error"
                    result.error = safe_error(error)
                observations.append(result)
    return observations


def evaluate(brand_name, observations):
    from dataclasses import replace
    validate_text(brand_name, "brand")
    results = []
    for observation in observations:
        result = replace(observation)
        if result.status == "success":
            result.mentioned, result.rank, result.context = _detect_brand(brand_name, result.response)
        results.append(result)
    successful = [r for r in results if r.status == "success"]
    ranks = [r.rank for r in successful if r.rank is not None]
    rates = {}
    for query in dict.fromkeys(r.query for r in successful):
        subset = [r for r in successful if r.query == query]
        rates[query] = sum(r.mentioned for r in subset) / len(subset)
    errors = {}
    for r in results:
        if r.error:
            errors[r.error] = errors.get(r.error, 0) + 1
    n = len(successful)
    return BrandReport(brand_name, results, sum(r.mentioned for r in successful)/n if n else None,
                       sum(ranks)/len(ranks) if ranks else None,
                       max(rates, key=rates.get) if rates else "", min(rates, key=rates.get) if rates else "",
                       n, len(results)-n, "complete" if n == len(results) and n else "partial" if n else "failed", errors)


def brand(brand: str, queries: list[str], *, models=None, prober=None, jev=None, samples=1) -> BrandReport:
    """Jev argument retained for compatibility; mention/rank detection needs no judge."""
    validate_text(brand, "brand")
    return evaluate(brand, capture(queries, models=models, prober=prober, samples=samples))
