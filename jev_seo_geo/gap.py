"""Competitor gap analysis."""

from __future__ import annotations

from dataclasses import dataclass, field

from jev_seo_geo.client import LLMProber, JevClient
from jev_seo_geo.probe import brand, BrandReport


@dataclass
class GapReport:
    """Competitor gap analysis result."""
    brand: str
    competitors: list[str]
    brand_report: BrandReport
    competitor_reports: dict[str, BrandReport]
    summary: str
    recommendations: list[str]
    mention_comparison: dict[str, float]  # brand/competitor -> mention_rate


def analyze(
    brand_name: str,
    competitors: list[str],
    queries: list[str],
    *,
    models: list[str] | None = None,
    prober: LLMProber | None = None,
    jev: JevClient | None = None,
) -> GapReport:
    """Run competitor gap analysis.

    Probes AI models for brand and all competitors, then compares visibility.
    """
    p = prober or LLMProber()
    j = jev or JevClient()

    # Probe brand
    brand_report = brand(brand_name, queries, models=models, prober=p, jev=j)

    # Probe competitors
    competitor_reports: dict[str, BrandReport] = {}
    for comp in competitors:
        competitor_reports[comp] = brand(comp, queries, models=models, prober=p, jev=j)

    # Build comparison
    mention_comparison = {brand_name: brand_report.mention_rate}
    for comp, report in competitor_reports.items():
        mention_comparison[comp] = report.mention_rate

    # Find winners and gaps
    sorted_brands = sorted(mention_comparison.items(), key=lambda x: x[1], reverse=True)
    brand_position = next(i for i, (name, _) in enumerate(sorted_brands) if name == brand_name) + 1

    # Generate summary
    top_brand = sorted_brands[0][0]
    summary_parts = []
    for name, rate in sorted_brands:
        pct = int(rate * 100)
        marker = " ← you" if name == brand_name else ""
        summary_parts.append(f"{name}: {pct}% mention rate{marker}")
    summary = "\n".join(summary_parts)

    if brand_position > 1:
        summary += f"\n\n{brand_name} ranks #{brand_position} out of {len(sorted_brands)}."
        gap = sorted_brands[0][1] - brand_report.mention_rate
        summary += f" Gap to #{1} ({top_brand}): {int(gap*100)}pp."

    # Generate recommendations
    recommendations = []
    if brand_report.mention_rate < 0.5:
        recommendations.append(f"Create comparison content: '{brand_name} vs {top_brand}' pages")
    if brand_report.mention_rate < sorted_brands[0][1]:
        recommendations.append(f"Study {top_brand}'s content strategy — they dominate AI responses")
    recommendations.append("Publish data-driven case studies with specific metrics")
    recommendations.append("Add structured FAQ sections targeting common queries")
    if brand_report.worst_query:
        recommendations.append(f"Weakest query: '{brand_report.worst_query}' — create dedicated content for this topic")

    return GapReport(
        brand=brand_name,
        competitors=competitors,
        brand_report=brand_report,
        competitor_reports=competitor_reports,
        summary=summary,
        recommendations=recommendations,
        mention_comparison=mention_comparison,
    )
