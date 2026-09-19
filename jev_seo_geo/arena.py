"""Title arena — rank headlines for AI visibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jev_seo_geo.client import JevClient


@dataclass
class TitleRank:
    """Ranked title result."""
    title: str
    score: float  # 0-1
    rank: int
    strengths: str
    raw: dict[str, Any] = None


def titles(
    titles: list[str],
    *,
    intent: str = "",
    client: JevClient | None = None,
) -> list[TitleRank]:
    """Rank titles/headlines for AI visibility.

    Jev evaluates each title independently, then sorts by score.

    Args:
        titles: List of title variations to compare.
        intent: What the searcher is trying to do.
    """
    c = client or JevClient()
    results: list[TitleRank] = []

    for title in titles:
        state = f"Article title: {title}"
        if intent:
            state += f"\nSearcher intent: {intent}"

        answers = c.ask(
            state=state,
            questions={
                "specificity": {
                    "type": "noul",
                    "instructions": "Is this title specific and concrete (with numbers, names, comparisons) rather than generic?",
                },
                "click_value": {
                    "type": "noul",
                    "instructions": "Does this title promise clear value that would make someone click?",
                },
                "ai_citation": {
                    "type": "noul",
                    "instructions": "Would an AI model prefer to cite an article with this title when answering related questions?",
                },
                "authority": {
                    "type": "noul",
                    "instructions": "Does this title signal expertise or authority (data, testing, comparison, guide)?",
                },
                "strengths": {
                    "type": "choice",
                    "instructions": "What is the strongest aspect of this title?",
                    "criteria": {
                        "specific": "Uses specific numbers, names, or data points",
                        "comparative": "Compares options, helps decision-making",
                        "experiential": "Signals first-hand testing or experience",
                        "comprehensive": "Promises thorough coverage of the topic",
                        "actionable": "Clear how-to or step-by-step value",
                        "generic": "Nothing particularly strong about this title",
                    },
                },
            },
        )

        def _val(key: str) -> float:
            ans = answers.get(key, {})
            if isinstance(ans, (int, float)):
                return float(ans)
            if isinstance(ans, dict):
                return float(ans.get("noul", ans.get("probability", 0)))
            return 0.0

        score = round(
            _val("specificity") * 0.25
            + _val("click_value") * 0.20
            + _val("ai_citation") * 0.30
            + _val("authority") * 0.25,
            2,
        )

        strengths = answers.get("strengths", {})
        strength_str = strengths.get("choice", "generic") if isinstance(strengths, dict) else "generic"

        results.append(TitleRank(
            title=title,
            score=score,
            rank=0,
            strengths=strength_str,
            raw=answers,
        ))

    # Sort and assign ranks
    results.sort(key=lambda x: x.score, reverse=True)
    for i, r in enumerate(results):
        r.rank = i + 1

    return results
