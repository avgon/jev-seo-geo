"""Title arena — rank headlines for AI visibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jev_seo_geo.client import JevClient
from jev_seo_geo.validation import validate_text, validate_answers


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
    for title in titles:
        validate_text(title, "title")
    c = client or JevClient()
    results: list[TitleRank] = []

    for title in titles:
        state = f"Article title: {title}"
        if intent:
            state += f"\nSearcher intent: {intent}"

        questions = {
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
            }
        answers = c.ask(state=state, questions=questions)
        values = validate_answers(answers, questions)

        def _val(key: str) -> float:
            return values[key]

        score = round(
            _val("specificity") * 0.25
            + _val("click_value") * 0.20
            + _val("ai_citation") * 0.30
            + _val("authority") * 0.25,
            2,
        )

        strength_str = values["strengths"]

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
        r.rank = results[i - 1].rank if i and results[i - 1].score == r.score else i + 1

    return results
