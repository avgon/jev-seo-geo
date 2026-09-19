"""Content scoring — rate content for AI-friendliness."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jev_seo_geo.client import JevClient
from jev_seo_geo.validation import validate_text, validate_answers


@dataclass
class ContentScore:
    """Content quality assessment for GEO."""
    eeat: float  # Experience, Expertise, Authority, Trust (0-1)
    citation_ready: float  # Would AI cite this? (0-1)
    structure: float  # Headers, lists, data, schema (0-1)
    freshness: float  # Up-to-date signals (0-1)
    overall: float  # Weighted average
    suggestions: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


def content(
    text: str,
    *,
    url: str = "",
    topic: str = "",
    client: JevClient | None = None,
) -> ContentScore:
    """Score content for AI visibility potential.

    Args:
        text: Page content or article text.
        url: Optional URL (for context).
        topic: Optional topic/keyword focus.
    """
    validate_text(text)
    c = client or JevClient()

    state = f"Content to evaluate:\n{text}"
    if url:
        state += f"\nURL: {url}"
    if topic:
        state += f"\nTarget topic: {topic}"

    questions = {
            "expertise": {
                "type": "noul",
                "instructions": "Does this content demonstrate genuine expertise and first-hand experience on the topic?",
            },
            "authority": {
                "type": "noul",
                "instructions": "Does this content come from an authoritative source? (credentials, data, references, author info)",
            },
            "trust": {
                "type": "noul",
                "instructions": "Is this content trustworthy? (accurate, balanced, transparent, not misleading)",
            },
            "citation_ready": {
                "type": "noul",
                "instructions": "Would an AI assistant cite this content as a reliable source when answering questions?",
            },
            "structure": {
                "type": "score",
                "instructions": "How well-structured is this content for machine readability?",
                "criteria": [
                    "Poor: wall of text, no headers, no lists, no data",
                    "Moderate: some structure, headers exist, but could be better",
                    "Excellent: clear headers, bullet points, data tables, FAQ sections, schema-ready",
                ],
            },
            "freshness": {
                "type": "noul",
                "instructions": "Does this content appear current and up-to-date? (recent dates, current terminology, no outdated references)",
            },
            "missing_author": {
                "type": "noul",
                "instructions": "Is author information (name, bio, credentials) missing from this content?",
            },
            "missing_sources": {
                "type": "noul",
                "instructions": "Is this content missing citations, data sources, or references?",
            },
            "missing_data": {
                "type": "noul",
                "instructions": "Would adding specific numbers, statistics, or comparison data improve this content significantly?",
            },
        }
    answers = c.ask(state=state, questions=questions)
    values = validate_answers(answers, questions)

    def _val(key: str) -> float:
        return values[key]

    expertise = _val("expertise")
    authority = _val("authority")
    trust = _val("trust")
    eeat = round((expertise + authority + trust) / 3, 2)

    citation = _val("citation_ready")
    freshness = _val("freshness")

    structure_raw = _val("structure")
    structure = round(structure_raw / 2, 2)

    overall = round(eeat * 0.35 + citation * 0.30 + structure * 0.20 + freshness * 0.15, 2)

    # Generate suggestions
    suggestions = []
    if _val("missing_author") > 0.5:
        suggestions.append("Add author bio with credentials and experience")
    if _val("missing_sources") > 0.5:
        suggestions.append("Include citations, data sources, or references")
    if _val("missing_data") > 0.5:
        suggestions.append("Add specific numbers, statistics, or comparison tables")
    if structure_raw < 1:
        suggestions.append("Improve structure: add headers, bullet points, FAQ section")
    if freshness < 0.5:
        suggestions.append("Update content with current dates and terminology")

    return ContentScore(
        eeat=eeat,
        citation_ready=citation,
        structure=structure,
        freshness=freshness,
        overall=overall,
        suggestions=suggestions,
        raw=answers,
    )
