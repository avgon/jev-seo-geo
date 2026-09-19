"""Brand probe — ask AI models if they know about your brand."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from jev_seo_geo.client import LLMProber, JevClient


@dataclass
class ProbeResult:
    """Single probe result."""
    model: str
    query: str
    response: str
    mentioned: bool
    rank: int  # 0 = not mentioned, 1 = first, 2 = second, etc.
    context: str  # snippet where brand appears


@dataclass
class BrandReport:
    """Aggregated brand visibility across models and queries."""
    brand: str
    results: list[ProbeResult]
    mention_rate: float  # 0.0-1.0, how often brand appears
    avg_rank: float  # average rank when mentioned
    best_query: str  # query with highest mention rate
    worst_query: str  # query with lowest mention rate


def brand(
    brand: str,
    queries: list[str],
    *,
    models: list[str] | None = None,
    prober: LLMProber | None = None,
    jev: JevClient | None = None,
) -> BrandReport:
    """Probe AI models for brand visibility.

    Args:
        brand: Brand name to search for.
        queries: Questions to ask AI models.
        models: Which providers to query (default: all available).
        prober: Custom LLMProber instance.
        jev: Custom JevClient for rank extraction.
    """
    p = prober or LLMProber()
    j = jev or JevClient()
    target_models = models or p.available_models

    if not target_models:
        raise ValueError("No LLM API keys configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY.")

    results: list[ProbeResult] = []
    query_mention_counts: dict[str, int] = {}

    for query in queries:
        prompt = f"List and briefly describe the top options for: {query}. Be specific with names."
        query_mentions = 0

        for model in target_models:
            try:
                response = p.query(prompt, model)
            except Exception as e:
                response = f"[ERROR: {e}]"

            mentioned, rank, context = _detect_brand(brand, response, j)
            if mentioned:
                query_mentions += 1

            results.append(ProbeResult(
                model=model,
                query=query,
                response=response,
                mentioned=mentioned,
                rank=rank,
                context=context,
            ))

        query_mention_counts[query] = query_mentions

    # Aggregate
    mentioned_results = [r for r in results if r.mentioned]
    mention_rate = len(mentioned_results) / len(results) if results else 0
    avg_rank = sum(r.rank for r in mentioned_results) / len(mentioned_results) if mentioned_results else 0

    best_query = max(query_mention_counts, key=query_mention_counts.get) if query_mention_counts else ""
    worst_query = min(query_mention_counts, key=query_mention_counts.get) if query_mention_counts else ""

    return BrandReport(
        brand=brand,
        results=results,
        mention_rate=round(mention_rate, 2),
        avg_rank=round(avg_rank, 1),
        best_query=best_query,
        worst_query=worst_query,
    )


def _detect_brand(brand: str, text: str, jev: JevClient) -> tuple[bool, int, str]:
    """Detect brand mention and rank in AI response."""
    if not text or text.startswith("[ERROR"):
        return False, 0, ""

    # Simple regex detection first
    pattern = re.compile(re.escape(brand), re.IGNORECASE)
    match = pattern.search(text)

    if not match:
        return False, 0, ""

    # Extract context around mention
    start = max(0, match.start() - 80)
    end = min(len(text), match.end() + 80)
    context = text[start:end].strip()

    # Use Jev to determine rank position
    answers = jev.ask(
        state=f"AI response listing products/services:\n{text[:1500]}\n\nBrand to find: {brand}",
        questions={
            "rank": {
                "type": "score",
                "instructions": f"At what position is '{brand}' mentioned in this list?",
                "criteria": [
                    "Not mentioned or mentioned last/as afterthought",
                    "Mentioned in middle of the list (3rd-5th position)",
                    "Mentioned near the top (1st or 2nd position)",
                ],
            },
        },
    )

    raw_rank = answers.get("rank", {})
    rank_score = raw_rank.get("score", 0) if isinstance(raw_rank, dict) else 0
    # Convert: 2=top(rank 1), 1=middle(rank 3), 0=bottom(rank 5+)
    rank_map = {2: 1, 1: 3, 0: 5}
    rank = rank_map.get(round(float(rank_score)) if isinstance(rank_score, (int, float)) else 0, 5)

    return True, rank, context
