"""Optimize — Jev diagnoses, LLM rewrites. No LLM? Actionable checklist."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
import re
from jev_seo_geo.validation import validate_text, safe_error

from jev_seo_geo.client import JevClient, LLMProber
from jev_seo_geo.score import content as score_content, ContentScore


@dataclass
class OptimizeResult:
    """Optimization output."""
    before: ContentScore
    after: ContentScore | None  # None if no LLM key
    checklist: list[dict[str, str]]  # [{priority, issue, action, example}]
    rewritten: str  # "" if no LLM key
    improvement: float  # heuristic score delta, not measured SEO improvement
    status: str = "no_provider"
    error: str | None = None
    unverified_draft: bool = True
    human_review_required: bool = True
    unresolved_placeholders: list[str] = field(default_factory=list)


def rewrite(
    text: str,
    *,
    focus: str = "all",  # "eeat", "structure", "citation", "freshness", "all"
    url: str = "",
    topic: str = "",
    jev: JevClient | None = None,
    prober: LLMProber | None = None,
    generator: Callable[[str], str] | None = None,
) -> OptimizeResult:
    """Diagnose content weaknesses and optionally rewrite.

    1. Score content with Jev (fast diagnosis)
    2. Generate actionable checklist from scores
    3. If LLM key available: rewrite content, re-score to show improvement

    Args:
        text: Content to optimize.
        focus: Which aspect to prioritize.
        url: Optional URL for context.
        topic: Optional target keyword/topic.
        generator: Optional callable that receives the rewrite prompt and returns text.
            Use this to connect any custom or local LLM without a built-in provider.
    """
    _validate_focus(focus)
    validate_text(text)
    j = jev or JevClient()
    p = prober or LLMProber()

    # Step 1: Diagnose
    before = score_content(text, url=url, topic=topic, client=j)

    # Step 2: Build checklist
    checklist = _build_checklist(before, focus)

    # Step 3: Rewrite if LLM available
    rewritten = ""
    after = None
    improvement = 0.0

    status = "no_provider"
    error = None
    if generator is not None or p.available_models:
        prompt = _build_rewrite_prompt(text, checklist, focus, topic)
        try:
            draft = generator(prompt) if generator is not None else p.query(prompt, p.available_models[0], timeout=60)
            if not isinstance(draft, str) or not draft.strip():
                raise ValueError("Generator must return nonempty text")
            rewritten = draft
            status = "generated"
        except Exception as exc:
            status, error = "generation_failed", safe_error(exc)
        if status == "generated":
            try:
                after = score_content(rewritten, url=url, topic=topic, client=j)
                improvement = round(after.overall - before.overall, 2)
            except Exception as exc:
                status, error = "scoring_failed", safe_error(exc)
    return OptimizeResult(before, after, checklist, rewritten, improvement, status, error,
                          unresolved_placeholders=re.findall(r"\[VERIFY:[^\]]*\]", rewritten, re.IGNORECASE))


def checklist(
    text: str,
    *,
    focus: str = "all",
    url: str = "",
    topic: str = "",
    jev: JevClient | None = None,
) -> list[dict[str, str]]:
    """Quick checklist without rewrite (Jev only, no LLM needed)."""
    _validate_focus(focus)
    validate_text(text)
    j = jev or JevClient()
    scores = score_content(text, url=url, topic=topic, client=j)
    return _build_checklist(scores, focus)


def _build_checklist(scores: ContentScore, focus: str) -> list[dict[str, str]]:
    """Convert scores + suggestions into prioritized actionable checklist."""
    _validate_focus(focus)
    items: list[dict[str, str]] = []

    # E-E-A-T issues
    if focus in ("all", "eeat") and scores.eeat < 0.6:
        items.append({
            "priority": "HIGH",
            "issue": "Low E-E-A-T score",
            "action": "Add author credentials, first-hand experience signals, and expert quotes",
            "example": 'Add: "Written by [Name], [title] with [X] years of experience in [field]"',
        })

    # Citation readiness
    if focus in ("all", "citation") and scores.citation_ready < 0.5:
        items.append({
            "priority": "HIGH",
            "issue": "Low heuristic citation-readiness score",
            "action": "Add specific data points, statistics, methodology, and source references",
            "example": 'Use "[VERIFY: measured result, sample size, methodology and source]"',
        })

    # Structure
    if focus in ("all", "structure") and scores.structure < 0.5:
        items.append({
            "priority": "MEDIUM",
            "issue": "Poor content structure for machine readability",
            "action": "Add H2/H3 headers, bullet points, numbered lists, comparison tables, FAQ section",
            "example": "Break wall of text into: ## Overview, ## Key Findings, ## Comparison Table, ## FAQ",
        })

    # Freshness
    if focus in ("all", "freshness") and scores.freshness < 0.5:
        items.append({
            "priority": "MEDIUM",
            "issue": "Content appears outdated",
            "action": "Add current year references, update statistics, remove dated language",
            "example": 'Add "[VERIFY: actual review date]" only after reviewing the content',
        })

    # From Jev suggestions. Avoid duplicating the specific checks above.
    covered = {
        "author": "eeat",
        "citation": "citation",
        "source": "citation",
        "data": "citation",
        "number": "citation",
        "structure": "structure",
        "header": "structure",
        "fresh": "freshness",
        "update": "freshness",
    }
    for suggestion in scores.suggestions:
        lowered = suggestion.lower()
        area = next((area for token, area in covered.items() if token in lowered), None)
        if focus != "all" and area != focus:
            continue
        # Deduplicate only against actions actually emitted, not hypothetical checks.
        if any(suggestion.casefold() == item["action"].casefold() for item in items):
            continue
        if area == "eeat" and any("Low E-E-A-T" in item["issue"] for item in items):
            continue
        if area == "citation" and any("citation-readiness" in item["issue"] for item in items):
            continue
        if area == "structure" and any("Poor content structure" in item["issue"] for item in items):
            continue
        if area == "freshness" and any("outdated" in item["issue"] for item in items):
            continue
        items.append({
            "priority": "MEDIUM",
            "issue": "Content gap detected",
            "action": suggestion,
            "example": "",
        })

    # Add quick wins if overall is low
    if focus == "all" and scores.overall < 0.4:
        items.append({
            "priority": "HIGH",
            "issue": "Low overall heuristic content score",
            "action": "Consider a complete rewrite with: expert author, data tables, FAQ, sources, and clear structure",
            "example": "Use the rewrite() function with an LLM key for automated optimization",
        })

    return items


def _build_rewrite_prompt(text: str, checks: list[dict[str, str]], focus: str, topic: str) -> str:
    """Build LLM prompt for content rewrite."""
    validate_text(text)
    _validate_focus(focus)
    issues = "\n".join(f"- [{c['priority']}] {c['action']}" for c in checks)

    prompt = f"""Rewrite the following content to maximize AI visibility and citation potential.

FOCUS AREA: {focus}
{"TARGET TOPIC: " + topic if topic else ""}

ISSUES TO FIX:
{issues}

RULES:
- Keep the same core message and facts
- Add structure: clear headers (##), bullet points, data tables where appropriate
- Add an author/expertise signal at the top
- Preserve facts. Do not invent numbers, citations, credentials, sources, or testimonials.
- Where evidence is absent, use explicit [VERIFY: ...] placeholders for the editor.
- Add a FAQ section at the bottom with 3-4 common questions
- Add source-reference placeholders where claims require verification
- Write in the same language as the original
- Do NOT add meta-commentary about the rewrite

ORIGINAL CONTENT:
{text}

REWRITTEN CONTENT:"""

    return prompt


def _validate_focus(focus):
    if focus not in ("all", "eeat", "citation", "structure", "freshness"):
        raise ValueError("Unknown focus; use all, eeat, citation, structure or freshness")
